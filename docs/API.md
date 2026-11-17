# Local HTTP API

Base URL is `http://127.0.0.1:3000`. Health and profile data may be sensitive. This interface serves the overlay, settings and launch scripts on the same PC.

| Method and path | Purpose |
| --- | --- |
| GET `/` | Browser Source. Use `?demo=1` for the full sample or `?gsi-test=1` for isolated sample packets. |
| GET `/settings` | Account override and refresh controls. |
| GET `/api/health` | GSI age and connection, profile status and refresh interval. |
| GET `/api/state` | Latest live state envelope with `connected`, `received_at`, `age_seconds`, and `data`. |
| GET `/api/test-state` | Same envelope for isolated sample packets. |
| GET `/api/overlay` | Combined `profile` and `state` objects. |
| GET `/api/profile` | Selected identity, rating, aggregates and provider status. |
| GET `/api/settings` | Saved, detected and effective SteamID64. |
| POST `/api/settings` | Set `steam_id` to a SteamID64 or blank to restore autodetection. |
| POST `/api/refresh-profile` | Send `{}` to request a refresh subject to the schedule. |
| POST `/gsi` | Game packets with the supplied config's `auth.token`. |
| POST `/gsi/test` | Sample-only ingestion. Use the [sample payload](../examples/sample_gsi_payload.json). |
| POST `/api/stop` | Used by `stop_overlay.bat`. Requires the launcher control header. |

JSON POST bodies use a maximum of 64 KiB. The server returns `400` for malformed bodies, `403` for disallowed origins, hosts or tokens, `404` for unknown paths, and `503` if a completed match cannot be recorded. Use the test route for samples because the normal GSI route persists valid completed matches.
