import httpx

# Verified, working layers (checked directly against the live service).
# "TXRRC" data mirrored by Houston-Galveston Area Council (HGAC) - built from
# the same RRC source data, but this particular endpoint's extent suggests
# regional (Houston-area) coverage rather than confirmed statewide coverage.
# Swap in RRC's own gis.rrc.texas.gov service URL here once you confirm its
# exact path - the query/get_layer_info tools work against any ArcGIS REST
# MapServer/FeatureServer URL, not just these.
KNOWN_SERVICES = {
    "hgac_txrrc_wells": {
        "url": "https://www.gis.hctx.net/arcgishcpid/rest/services/TXRRC/Wells/MapServer",
        "layers": {
            0: "Surface Wells (point) - fields: API, WELLID, LONG83, LAT83, SYMNUM, RELIAB",
            1: "Bottom Well Lines (polyline, directional/horizontal connectors) - fields: API10, API",
            2: "Bottom Wells (point) - fields: APINUM, API10, LONG83, LAT83, WELLID",
        },
        "note": "Coordinates given in both NAD27 (LONG27/LAT27) and NAD83 (LONG83/LAT83). "
                "Native spatial reference is EPSG:2278 (Texas State Plane South Central, feet); "
                "request outSR=4326 to get plain lat/long back.",
    },
    "hgac_txrrc_pipelines": {
        "url": "https://www.gis.hctx.net/arcgishcpid/rest/services/TXRRC/Pipelines/MapServer",
        "layers": {},  # not yet introspected - call get_layer_info to list
        "note": "Derived from RRC T-4 pipeline permit applications.",
    },
}


async def get_layer_info(service_url: str, layer_id: int | None = None, token: str | None = None) -> dict:
    """Fetch metadata (fields, geometry type, extent) for a service or a specific layer."""
    url = service_url.rstrip("/")
    if layer_id is not None:
        url = f"{url}/{layer_id}"
    params = {"f": "json"}
    if token:
        params["token"] = token
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()


async def query_layer(
    service_url: str,
    layer_id: int,
    where: str = "1=1",
    out_fields: str = "*",
    bbox: str | None = None,
    out_sr: int = 4326,
    result_record_count: int = 1000,
    token: str | None = None,
) -> dict:
    """
    Query an ArcGIS Feature/MapServer layer and return GeoJSON.

    bbox: optional "xmin,ymin,xmax,ymax" in the same SR as out_sr (default WGS84
    lat/long) to filter by extent, e.g. "-96.9,29.0,-96.5,29.4".
    """
    url = f"{service_url.rstrip('/')}/{layer_id}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "f": "geojson",
        "outSR": out_sr,
        "resultRecordCount": result_record_count,
    }
    if bbox:
        params["geometry"] = bbox
        params["geometryType"] = "esriGeometryEnvelope"
        params["spatialRel"] = "esriSpatialRelIntersects"
        params["inSR"] = out_sr
    if token:
        params["token"] = token
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()
