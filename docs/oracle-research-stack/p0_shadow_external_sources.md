# Oracle External Source Registry — P0 SHADOW notes

Canonical catalog lives in the Notion database **Oracle External Source Registry**.
Local working notes for adapter wiring live in this directory (`docs/oracle-research-stack`).

These P0 sources are registered in SourceAtlas as SHADOW / influence=NONE.
They are not promoted to Canary or Active. No secrets. No phenomenology claims.

| source_id | adapter | Notion catalog id | HTTP GET |
| --- | --- | --- | --- |
| WORLDBANK_REGION_V2 | worldbank_region_v2 | EXT.WORLDBANK.REGION.v1 | https://api.worldbank.org/v2/region?format=json |
| EXCHANGERATE_OPEN_V6 | exchangerate_open_v6 | EXT.EXCHANGERATE.LATEST.v1 | https://open.er-api.com/v6/latest/USD |
| USGS_EARTHQUAKE_FDSN | usgs_earthquake_fdsn | EXT.USGS.EARTHQUAKE.v1 | https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&limit=50&orderby=time |
| US_FEDERAL_REGISTER | us_federal_register | EXT.US.FEDERAL_REGISTER.v1 | https://www.federalregister.gov/api/v1/documents.json?per_page=20&order=newest |
| RESTCOUNTRIES_V3 | restcountries_v3 | EXT.RESTCOUNTRIES.v1 | https://restcountries.com/v3.1/all?fields=name,cca2,region,population |

Operator path: Notion registry row → this note → `abraxas/sources/atlas.py` SourceSpec → named `HTTPSnapshotAdapter` subclass → `ADAPTER_REGISTRY`.

Status label: `candidate`. Missing live-run receipts remain explicit (`attestation_pending` for any gated claim).
