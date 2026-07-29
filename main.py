import os
import json
from mcp.server import MCPServer

from src.arcgis_client import get_layer_info, query_layer, KNOWN_SERVICES

mcp = MCPServer("arcgis-connector", version="0.1.0")


@mcp.tool()
async def list_known_services() -> str:
    """List pre-verified ArcGIS REST services this connector knows about
    (currently: RRC's real statewide well/pipeline data, plus a Houston-area
    regional mirror as fallback). Use these as a starting point, or call
    query_layer / get_layer_info against any other ArcGIS REST
    MapServer/FeatureServer URL - including your own ArcGIS Online account
    once you have a token."""
    return json.dumps(KNOWN_SERVICES, indent=2)


@mcp.tool()
async def get_layer_metadata(service_url: str, layer_id: int | None = None, token: str | None = None) -> str:
    """Fetch field names, geometry type, and extent for an ArcGIS service or
    a specific layer within it. Call this before query_layer if you don't
    already know the field names to filter/select on."""
    info = await get_layer_info(service_url, layer_id, token)
    return json.dumps(info, indent=2)


@mcp.tool()
async def query_arcgis_layer(
    service_url: str,
    layer_id: int,
    where: str = "1=1",
    out_fields: str = "*",
    bbox: str | None = None,
    result_offset: int = 0,
    token: str | None = None,
) -> str:
    """Query an ArcGIS Feature/MapServer layer and return GeoJSON features.

    service_url: the MapServer/FeatureServer base URL (no trailing layer id).
    layer_id: numeric layer index within that service (see list_known_services
      or get_layer_metadata).
    where: SQL-style filter, e.g. "API='42-xxxxxxxx'" or "1=1" for everything.
    out_fields: comma-separated field names, or "*" for all.
    bbox: optional "xmin,ymin,xmax,ymax" in WGS84 lat/long to limit by area.
    result_offset: for pagination - if the response says
      "exceededTransferLimit": true, call again with result_offset increased
      by 1000 (the default page size) to get the next page.
    token: optional ArcGIS auth token, needed only for private/ArcGIS Online
      services - not needed for the public RRC-derived layers.
    """
    geojson = await query_layer(
        service_url=service_url,
        layer_id=layer_id,
        where=where,
        out_fields=out_fields,
        bbox=bbox,
        result_offset=result_offset,
        token=token,
    )
    return json.dumps(geojson, indent=2)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    mcp.run(transport="streamable-http", host="0.0.0.0", port=port, stateless_http=True)
