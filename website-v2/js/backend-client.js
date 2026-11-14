/* All recommendations come from the validated backend; no silent local scoring. */
(() => {
  // The dashboard may be opened directly from Finder as file://index.html.
  // In that case there is no same-origin API, so use the local FastAPI server.
  const base = window.FS_API_BASE_URL || (location.protocol === 'file:' || location.port === '8080'
    ? `http://${location.hostname || '127.0.0.1'}:8000`
    : location.origin);
  async function request(path, body, signal) {
    const controller = new AbortController();
    const abort = () => controller.abort();
    if (signal?.aborted) controller.abort();
    signal?.addEventListener('abort', abort, {once:true});
    const timeout = setTimeout(abort, 12000);
    try {
      const response = await fetch(base + path, {
        method: body ? 'POST' : 'GET',
        headers: {Accept:'application/json', ...(body ? {'Content-Type':'application/json'} : {})},
        ...(body ? {body:JSON.stringify(body)} : {}), signal:controller.signal,
      });
      if (!response.ok) {const error=new Error(`API ${response.status}`);error.status=response.status;try{const body=await response.json();error.detail=body&&body.detail;}catch{}throw error;}
      return await response.json();
    } finally {clearTimeout(timeout);signal?.removeEventListener('abort',abort);}
  }
  window.FieldBackend = {
    science:signal=>request('/api/dashboard/science',null,signal),
    catalog:signal=>request('/api/dashboard/catalog',null,signal),
    evaluate:(cellId,weights,signal,area)=>request('/api/dashboard/evaluate',{cell_id:cellId,weights:{land:weights[0],water:weights[1],practice:weights[2]},...(area?{area_feddan:area}:{})},signal),
    match:(lat,lon,signal)=>request('/api/dashboard/match',{lat,lon},signal),
    health:signal=>request('/api/health',null,signal),
    base,
  };
})();
