/* Field Shift map.
 *
 * Built once and kept for the whole visit. The dashboard rewrites #app on
 * every change, so the map element is moved into the new #field-map slot
 * instead of being rebuilt. Nothing reloads when the page, language, month or
 * theme changes.
 *
 * Layers, bottom to top:
 *   1. Satellite imagery: Esri World Imagery (no key). If those tiles fail it
 *      switches to Sentinel-2 cloudless (EOX). If both fail it shows a plain
 *      background and says so.
 *   2. The study grid from the backend: every 1 km cell with its real corners.
 *      It is drawn locally, so the map is never empty, even offline.
 *   3. The selected cell, outlined in gold.
 *
 * Requires js/vendor/leaflet.js (Leaflet 1.9.4, bundled, no CDN).
 */
(() => {
  'use strict';

  const PROVIDERS = [
    {
      id: 'esri',
      url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      options: {maxNativeZoom: 17, maxZoom: 18,
        attribution: 'Imagery &copy; Esri, Maxar, Earthstar Geographics'}
    },
    {
      id: 'eox',
      url: 'https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless-2020_3857/default/g/{z}/{y}/{x}.jpg',
      options: {maxNativeZoom: 15, maxZoom: 18,
        attribution: '<a href="https://s2maps.eu" target="_blank" rel="noopener">Sentinel-2 cloudless</a> by EOX (Copernicus Sentinel data 2020)'}
    }
  ];
  const LABELS = {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}',
    options: {maxNativeZoom: 17, maxZoom: 18, pane: 'labels'}
  };
  const STYLE = {
    farm: {color: '#ffffff', weight: 0.7, opacity: 0.55, fillColor: '#ffffff', fillOpacity: 0.02},
    farmHover: {color: '#ffffff', weight: 2, opacity: 1, fillColor: '#ffffff', fillOpacity: 0.18},
    village: {color: '#d7d2c8', weight: 0.6, opacity: 0.6, fillColor: '#6b6a64', fillOpacity: 0.45, dashArray: '3 3'},
    selected: {color: '#f2b632', weight: 3.5, opacity: 1, fillColor: '#f2b632', fillOpacity: 0.22}
  };

  let info = {lang: 'en'};
  let root, holder, map, gridLayer, selectedLayer, baseLayer, labelLayer, statusEl, captionEl;
  let providerIndex = 0, tileLoads = 0, tileErrors = 0, grid = [], cellsById = new Map(), currentId = null;
  let onSelect = null, renderer = null;

  const t = (en, ar) => info.lang === 'ar' ? ar : en;
  const leafletMissing = () => typeof window.L === 'undefined';

  function setStatus(text) {
    if (!statusEl) return;
    statusEl.textContent = text || '';
    statusEl.hidden = !text;
  }

  function useProvider(index) {
    if (baseLayer) { map.removeLayer(baseLayer); baseLayer = null; }
    providerIndex = index; tileLoads = 0; tileErrors = 0;
    root.classList.toggle('fs-map--no-imagery', index >= PROVIDERS.length);
    if (index >= PROVIDERS.length) {
      setStatus(t('Satellite imagery cannot load on this network. The study grid is still shown.',
                  'صور القمر الصناعي مش بتحمل على الشبكة دي. شبكة الدراسة لسه ظاهرة.'));
      return;
    }
    const p = PROVIDERS[index];
    baseLayer = L.tileLayer(p.url, {...p.options, crossOrigin: false, keepBuffer: 4, updateWhenIdle: false});
    baseLayer.on('tileload', () => { tileLoads++; if (tileLoads === 1) setStatus(''); });
    baseLayer.on('tileerror', () => {
      tileErrors++;
      // Switch only when this source is clearly not reachable, not on one bad tile.
      if (tileLoads === 0 && tileErrors >= 4) useProvider(providerIndex + 1);
    });
    baseLayer.addTo(map);
    baseLayer.bringToBack();
  }

  function build() {
    holder = document.createElement('div');
    holder.hidden = true;
    document.body.appendChild(holder);

    root = document.createElement('div');
    root.className = 'fs-map';
    root.setAttribute('dir', 'ltr');
    root.innerHTML = '<div class="fs-map__canvas"></div><div class="fs-map__status" role="status" hidden></div>' +
      '<div class="fs-map__bar"><span class="fs-map__caption"></span><span class="fs-map__actions">' +
      '<button type="button" data-map="fit"></button><button type="button" data-map="cell"></button>' +
      '<a data-map="google" target="_blank" rel="noopener"></a></span></div>';
    holder.appendChild(root);
    statusEl = root.querySelector('.fs-map__status');
    captionEl = root.querySelector('.fs-map__caption');

    if (leafletMissing()) {
      root.classList.add('fs-map--no-imagery');
      setStatus('Map library did not load. Refresh the page.');
      return;
    }

    map = L.map(root.querySelector('.fs-map__canvas'), {
      zoomControl: true, attributionControl: true, scrollWheelZoom: false,
      zoomSnap: 0.25, minZoom: 9, maxZoom: 18, preferCanvas: true, worldCopyJump: false
    });
    // A view from the start, so layers can be added before the first cell is known.
    map.setView([31.175, 30.806], 12, {animate: false});
    map.attributionControl.setPrefix('<a href="https://leafletjs.com" target="_blank" rel="noopener">Leaflet</a>');
    map.createPane('labels');
    map.getPane('labels').style.zIndex = 450;
    map.getPane('labels').style.pointerEvents = 'none';
    map.createPane('cells');
    map.getPane('cells').style.zIndex = 420;

    // Wheel zoom only after the user clicks into the map, so the page scrolls normally.
    map.on('click', () => map.scrollWheelZoom.enable());
    root.addEventListener('mouseleave', () => map.scrollWheelZoom.disable());

    useProvider(0);
    labelLayer = L.tileLayer(LABELS.url, {...LABELS.options, opacity: 0.85});
    labelLayer.on('tileerror', () => {});
    labelLayer.addTo(map);

    root.querySelector('[data-map="fit"]').onclick = fitStudy;
    root.querySelector('[data-map="cell"]').onclick = () => focusCell(currentId, true);
    window.addEventListener('online', () => { if (providerIndex >= PROVIDERS.length || tileLoads === 0) useProvider(0); });
  }

  function drawGrid() {
    if (!map || !grid.length || gridLayer) return;
    renderer = renderer || L.canvas({padding: 0.5, pane: 'cells'});
    gridLayer = L.layerGroup();
    for (const c of grid) {
      const poly = L.polygon(c.corners, {...(c.is_farm ? STYLE.farm : STYLE.village), renderer, pane: 'cells',
        bubblingMouseEvents: false, interactive: true});
      poly.cell = c;
      poly.bindTooltip(() => c.is_farm
        ? `${t('Cell', 'خلية')} ${c.id} · ${t('click to analyse', 'اضغط للتحليل')}`
        : `${t('Cell', 'خلية')} ${c.id} · ${t('mostly village or water, no recommendation', 'قرية أو مياه، مفيش توصية')}`,
        {sticky: true, direction: 'top', opacity: 0.95});
      if (c.is_farm) {
        poly.on('mouseover', () => { if (c.id !== currentId) poly.setStyle(STYLE.farmHover); });
        poly.on('mouseout', () => { if (c.id !== currentId) poly.setStyle(STYLE.farm); });
        poly.on('click', () => { if (onSelect && c.id !== currentId) onSelect(c.id); });
      }
      gridLayer.addLayer(poly);
    }
    gridLayer.addTo(map);
  }

  function studyBounds() {
    if (!grid.length) return null;
    return L.latLngBounds(grid.flatMap(c => c.corners));
  }

  function fitStudy() {
    const b = studyBounds();
    if (b) map.fitBounds(b, {padding: [16, 16]});
  }

  function focusCell(id, animate) {
    const c = cellsById.get(id);
    if (!map || !c) return;
    const b = L.latLngBounds(c.corners);
    const zoom = Math.min(15, map.getBoundsZoom(b.pad(2.2)));
    if (animate) map.flyTo(b.getCenter(), zoom, {duration: 0.6});
    else map.setView(b.getCenter(), zoom, {animate: false});
  }

  function highlight(id) {
    if (!map) return;
    if (selectedLayer) { map.removeLayer(selectedLayer); selectedLayer = null; }
    const c = cellsById.get(id);
    if (!c) return;
    // Same canvas as the grid: a second canvas on top would swallow every click.
    renderer = renderer || L.canvas({padding: 0.5, pane: 'cells'});
    selectedLayer = L.polygon(c.corners, {...STYLE.selected, renderer, pane: 'cells', interactive: false}).addTo(map);
    if (gridLayer) gridLayer.eachLayer(l => { if (l.cell.is_farm) l.setStyle(STYLE.farm); });
  }

  function relabel() {
    if (!root) return;
    root.querySelector('[data-map="fit"]').textContent = t('Whole study area', 'منطقة الدراسة كلها');
    root.querySelector('[data-map="cell"]').textContent = t('Back to my cell', 'رجوع لخليتي');
    const g = root.querySelector('[data-map="google"]');
    g.textContent = t('Google Maps ↗', 'Google Maps ↗');
    if (info.lat != null) g.href = `https://www.google.com/maps/@${info.lat},${info.lon},1200m/data=!3m1!1e3`;
    captionEl.textContent = currentId != null
      ? `${t('Cell', 'خلية')} #${currentId} · ${Number(info.lat).toFixed(4)}° N, ${Number(info.lon).toFixed(4)}° E`
      : '';
    root.querySelector('.fs-map__canvas').setAttribute('aria-label',
      t('Satellite map of the study area with the 1 km cell grid. The selected cell is outlined in gold.',
        'خريطة أقمار صناعية لمنطقة الدراسة مع شبكة الخلايا ١ كم. الخلية المختارة محددة باللون الذهبي.'));
    if (providerIndex >= PROVIDERS.length) useProvider(PROVIDERS.length);
  }

  window.FieldMap = {
    /** Give the map the study grid once (the backend catalog's `grid`). */
    setGrid(cells) {
      if (!Array.isArray(cells) || !cells.length) return;
      if (!root) build();
      grid = cells;
      cellsById = new Map(cells.map(c => [c.id, c]));
      drawGrid();
    },
    /** Called when a farm cell on the map is clicked. */
    onSelect(fn) { onSelect = fn; },
    /** Put the map in `slot` and show `next` ({id, lat, lon, lang}). Never rebuilds it. */
    show(slot, next) {
      if (!root) build();
      if (!slot || !next) {
        if (root.parentNode !== holder) holder.appendChild(root);
        return;
      }
      const changed = next.id !== currentId;
      info = next;
      if (root.parentNode !== slot) slot.replaceChildren(root);
      if (!map) { relabel(); return; }
      currentId = next.id;
      relabel();
      // The slot is new after each render: let it get its size, then redraw tiles.
      requestAnimationFrame(() => {
        map.invalidateSize({animate: false});   // keeps the centre when the card size changes
        if (changed || !map._loaded) { highlight(currentId); focusCell(currentId, map._loaded === true && changed && !!next.animate); }
      });
    }
  };
})();
