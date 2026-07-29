import httpx

# Verified live and statewide - confirmed directly (Midland County, Permian
# Basin test query returned real well data) on 2026-07-29. This is RRC's own
# service behind their actual Public GIS Viewer, not a regional mirror.
KNOWN_SERVICES = {
    "rrc_statewide": {
        "url": "https://gis.rrc.texas.gov/server/rest/services/rrc_public/RRC_Public_Viewer_Srvs/MapServer",
        "layers": {
            0: "Well Number (labels)",
            1: "Well Locations - fields: API, GIS_WELL_NUMBER, SYMNUM, GIS_SYMBOL_DESCRIPTION, RELIAB, GIS_LAT83/GIS_LONG83",
            2: "Orphan Wells",
            3: "Commercial Disposal",
            4: "Injection/Disposal",
            5: "HCTS Deeper than 15,000 ft.",
            6: "High Cost Tight Sands",
            7: "EOR H13 Oil Wells",
            8: "Well Logs",
            9: "Horiz/Dir Surface Locations",
            10: "Horizontal/Directional Lines",
            11: "LPGAS Sites",
            12: "QPipelines",
            13: "Pipelines",
            14: "Pipelines",
            15: "Bay Tracts",
            16: "Offshore Areas",
            17: "Offshore Tracts",
            18: "Water Lines",
            19: "Subdivision Labels",
            20: "Subdivisions",
            21: "Railroads",
            22: "Survey Abstract Labels",
            23: "Survey Labels",
            24: "Surveys",
            25: "Quads",
            26: "Alert Areas",
            27: "Water",
            28: "City Limits",
            29: "Counties",
            30: "District Offices",
            31: "Districts",
            32: "Water Labels",
            33: "Operator Cleanup Program Sites",
            34: "Voluntary Cleanup Program Sites",
            35: "Brownfield Response Program Sites",
            36: "Commercial Waste Disposal Sites",
            37: "Discharge Permits",
            38: "AED Districts",
            39: "PS Regions",
            40: "Places",
        },
        "note": "Statewide. Server may cap results per request (watch for "
                "exceededTransferLimit:true in responses) - paginate with "
                "resultOffset if you need more than one page for a query.",
    },
    "hgac_txrrc_wells_regional_mirror": {
        "url": "https://www.gis.hctx.net/arcgishcpid/rest/services/TXRRC/Wells/MapServer",
        "layers": {
            0: "Surface Wells (point) - fields: API, WELLID, LONG83, LAT83, SYMNUM, RELIAB",
            1: "Bottom Well Lines (polyline, directional/horizontal connectors) - fields: API10, API",
            2: "Bottom Wells (point) - fields: APINUM, API10, LONG83, LAT83, WELLID",
        },
        "note": "Houston-Galveston Area Council's regional mirror of TXRRC data. "
                "Confirmed Houston-area coverage only - kept here as a fallback, "
                "prefer rrc_statewide above for anything outside that region.",
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
    result_offset: int = 0,
    token: str | None = None,
) -> dict:
    """
    Query an ArcGIS Feature/MapServer layer and return GeoJSON.

    bbox: optional "xmin,ymin,xmax,ymax" in the same SR as out_sr (default WGS84
    lat/long) to filter by extent, e.g. "-96.9,29.0,-96.5,29.4".

    result_offset: for pagination - if the response has "exceededTransferLimit":
    true, call again with result_offset increased by result_record_count to
    get the next page.
    """
    url = f"{service_url.rstrip('/')}/{layer_id}/query"
    params = {
        "where": where,
        "outFields": out_fields,
        "f": "geojson",
        "outSR": out_sr,
        "resultRecordCount": result_record_count,
        "resultOffset": result_offset,
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
