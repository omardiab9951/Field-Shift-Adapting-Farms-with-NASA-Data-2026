import csv,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
def rows(name):
    with (root/'backend/data/processed'/name).open() as f:return list(csv.DictReader(f))
scores={}
for r in rows('scores_all.csv'):
    scores.setdefault(r['cell_id'],[]).append({k:(float(r[k]) if k in ['s_land','s_water','s_practice','irrig_mm_year','score_fit'] else r[k]) for k in ['option','winter_crop','summer_crop','s_land','s_water','s_practice','irrig_mm_year','score_fit','suit_filled','water_filled']})
cells=[]
for r in rows('master_cell.csv'):
    if r['is_farm_cell']!='True':continue
    c={k:float(r[k]) for k in ['lat','lon','farm_pct','winter_ndvi','summer_ndvi','soil_overall','rain_mm_year']}
    c.update(id=int(r['cell_id']),trend=r['ls_trend_class'],ndvi=[float(r[f'ndvi_m{i:02}']) for i in range(1,13)],scores=scores[r['cell_id']])
    cells.append(c)
(root/'js/dashboard-data.js').write_text('window.FIELD_CELLS='+json.dumps(cells,separators=(',',':'))+';')
print(len(cells),'agricultural cells exported with full precision scoring components')
