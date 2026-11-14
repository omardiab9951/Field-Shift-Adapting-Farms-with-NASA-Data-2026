import pytest
from fastapi.testclient import TestClient
from app.main import create_app

@pytest.fixture(scope='module')
def client():
    with TestClient(create_app()) as c:
        yield c

def test_catalog_sectors(client):
    data=client.get('/api/dashboard/catalog').json()
    assert len(data['cells'])==556
    assert len(data['regions'])==1
    assert data['regions'][0]['name']['ar']=='سيدي سالم وقلين'
    assert data['study']['administrative_boundaries_available'] is False
    assert all(c['region_id']=='sidi-salem-qallin' for c in data['cells'])
    assert len({c['id'] for c in data['cells']})==556
    assert sum(r['cell_count'] for r in data['regions'])==556
    for r in data['regions']:
        group=[c for c in data['cells'] if c['region_id']==r['id']]
        assert len(group)==r['cell_count']
        assert r['default_cell'] in [c['id'] for c in group]
        assert r['name']['ar'] and r['name']['en']

@pytest.mark.parametrize('weights',[{'land':1,'water':1,'practice':1},{'land':0,'water':100,'practice':0},{'land':1e308,'water':1e308,'practice':0},{'land':.7,'water':.2,'practice':.1}])
def test_dashboard_matches_existing_api(client, weights):
    for region in client.get('/api/dashboard/catalog').json()['regions']:
        body={'cell_id':region['default_cell'],'weights':weights}
        response=client.post('/api/dashboard/evaluate',json=body)
        assert response.status_code==200
        data=response.json()
        assert data['evaluation']==client.post('/api/rotations/evaluate',json=body).json()
        assert data['profile']['id']==body['cell_id']
        assert len(data['profile']['ndvi'])==12
        raw=client.get(f"/api/cells/{body['cell_id']}").json()
        assert data['profile']['lat']==raw['lat']
        assert data['profile']['winter_ndvi']==raw['winter_ndvi']

def test_match_and_coverage(client):
    c=client.get('/api/cells/222').json()
    response=client.post('/api/dashboard/match',json={'lat':c['lat'],'lon':c['lon']})
    assert response.status_code==200
    assert response.json()['cell']['id']==222
    assert response.json()['distance_m']==0
    c=client.get('/api/cells/69').json()
    assert client.post('/api/dashboard/match',json={'lat':c['lat'],'lon':c['lon']}).status_code==422
    for point in [{'lat':0,'lon':0},{'lat':91,'lon':30},{'lat':'31','lon':30},{'lat':31,'lon':181}]:
        assert client.post('/api/dashboard/match',json=point).status_code==422

def test_errors_and_static_boundary(client):
    for cell_id,code in [(99999,404),(69,422)]:
        assert client.post('/api/dashboard/evaluate',json={'cell_id':cell_id,'weights':{'land':1,'water':1,'practice':1}}).status_code==code
    assert client.post('/api/dashboard/evaluate',json={'cell_id':1,'weights':{'land':0,'water':0,'practice':0}}).status_code==422
    assert client.get('/').status_code==200
    assert client.get('/js/backend-client.js').status_code==200
    assert client.get('/backend/.venv/pyvenv.cfg').status_code==404
    assert 'dashboard-data.js' not in client.get('/').text


def test_science_uses_dictionary_and_study_identity(client):
    result=client.get('/api/dashboard/science')
    assert result.status_code==200
    data=result.json()
    assert data['study']['name']['en']=='Sidi Salem & Qallin'
    assert data['cell_count']==560 and data['farm_cell_count']==556
    assert data['rotation_count']==13
    assert sum(s['field_count'] for s in data['sources'])==189
    assert {s['name'] for s in data['sources']} >= {'Sentinel-2','Landsat','GPM','NASA POWER'}
    assert len({(c['row'],c['col']) for c in client.get('/api/dashboard/catalog').json()['cells']})==556


def test_monthly_values_and_farm_volume(client):
    payload={'cell_id':222,'weights':{'land':1,'water':1,'practice':1},'area_feddan':5}
    result=client.post('/api/dashboard/evaluate',json=payload).json()
    raw=client.get('/api/cells/222').json()
    for item in result['profile']['monthly']:
        month=item['month']
        assert item['rain_mm']==raw[f'rain_mm_m{month:02}']
        assert item['max_temperature_c']==raw[f't_max_c_m{month:02}']
    for estimate,score in zip(result['farm_estimates']['rotations'],result['evaluation']['ranked_options']):
        assert estimate['option']==score['option']
        assert estimate['annual_irrigation_m3']==pytest.approx(score['irrig_mm_year']*5*4200/1000)
    for invalid in [0,-1,100001,'5']:
        payload['area_feddan']=invalid
        assert client.post('/api/dashboard/evaluate',json=payload).status_code==422
    del payload['area_feddan']
    assert client.post('/api/dashboard/evaluate',json=payload).json()['farm_estimates'] is None
