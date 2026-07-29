# arcgis-mcp

Generic MCP connector for querying ArcGIS REST services - built so it works
against RRC's well/pipeline data today, and your own ArcGIS Online account
later (once you have a login), without any code changes.

## Why generic, not hardcoded to one URL

RRC's own statewide GIS service (`gis.rrc.texas.gov`) exists but its exact
service path wasn't confirmed directly (an automated-access block on that
one page stopped me checking it myself). What *is* confirmed and verified
live is a regional mirror of the same TXRRC well/pipeline data, hosted by
Houston-Galveston Area Council - see `KNOWN_SERVICES` in
`src/arcgis_client.py`. That mirror's extent suggests Houston-area coverage
rather than confirmed statewide, so treat it as a starting point, and swap
in RRC's real statewide URL the moment you confirm it (same tool works
against any ArcGIS REST MapServer/FeatureServer URL).

## Tools exposed

- `list_known_services()` - pre-verified service URLs and layer notes.
- `get_layer_metadata(service_url, layer_id?, token?)` - field names,
  geometry type, extent for a service or one layer in it. Call this first
  against any new/unknown service so you know what to filter on.
- `query_arcgis_layer(service_url, layer_id, where, out_fields, bbox?, token?)`
  - runs a standard Esri REST query, returns GeoJSON. `token` is optional
  and only needed for private/ArcGIS Online services later.

## Verified so far

`get_layer_metadata` was checked directly against the live HGAC TXRRC/Wells
service and returned real field names (`API`, `WELLID`, `LONG83`, `LAT83`,
etc. on the Surface Wells layer). The actual `query_arcgis_layer` data call
follows the standard, widely-documented Esri REST query spec, but wasn't
hit live before handoff - it should work as-is; if a response looks off,
send me the error/output and I'll adjust.

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Test:
```bash
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"query_arcgis_layer","arguments":{"service_url":"https://www.gis.hctx.net/arcgishcpid/rest/services/TXRRC/Wells/MapServer","layer_id":0,"where":"1=1","out_fields":"API,WELLID","bbox":"-96.9,29.0,-96.5,29.4"}}}'
```

## Deploy

Same pattern as before:
```bash
git init && git add . && git commit -m "Initial ArcGIS MCP connector"
git remote add origin https://github.com/<you>/arcgis-mcp.git
git push -u origin main
```
Render dashboard -> New -> Blueprint -> point at the repo (picks up
`render.yaml`) -> deploy. Endpoint will be
`https://arcgis-mcp.onrender.com/mcp`.

## Adding your own ArcGIS Online account later

Once you have a login: generate a token (ArcGIS Online -> your account ->
generate API key/token, or OAuth if you want it to expire/refresh), then
pass it as the `token` argument on `query_arcgis_layer` /
`get_layer_metadata` calls against your own hosted feature layers - no
redeploy needed, it's just a per-call argument.

## Combining with Enverus isopach data

This connector only fetches ArcGIS layers (wells, pipelines, or whatever
else you point it at). Combining that with Enverus's isopach output into
one map happens at the chat level - ask Claude to pull both and render them
together once you're connected to this and have wells/pipelines to
overlay.
