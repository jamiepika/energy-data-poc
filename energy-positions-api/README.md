# energy-positions-api

A small Mule 4 application that serves the dbt `NET_POSITION` mart from Snowflake as a JSON API.

```
Google Sheets -> Fivetran -> Snowflake (raw) -> dbt (ANALYTICS.TRADING) -> this API -> apps / agents
```

## Endpoint

`GET /positions` returns each desk's net position per instrument, marked to market at the latest settlement price.

```
curl http://localhost:8081/positions
```

Example response (shape):

```json
[
  {
    "desk": "power_de",
    "instrument": "DE_BASE_DEC",
    "netPositionMwh": -40,
    "settlePriceEur": 86.00,
    "positionValueEur": -3440
  }
]
```

## How it works

| File | Purpose |
|---|---|
| `src/main/mule/energy-positions-api.xml` | The flow: HTTP Listener -> Database Select -> Transform Message (DataWeave) |
| `src/main/mule/global-configs.xml` | Shared configs: properties file, HTTP listener (port), Snowflake JDBC connection |
| `src/main/resources/config.yaml` | Local connection settings. **Git-ignored.** Copy from `config.example.yaml` |
| `pom.xml` | Connectors (HTTP, Database) and the Snowflake JDBC driver, registered as a shared library so the Database connector can load it |

DataWeave renames Snowflake's uppercase column names (`NET_POSITION_MWH`) to camelCase JSON (`netPositionMwh`).

## Prerequisites

- VS Code with the **Anypoint Extension Pack** (Anypoint Code Builder), signed in to Anypoint Platform
- Java (Code Builder prompts if missing)
- A Snowflake service user `MULE_USER` with read-only role `MULE_ROLE`:
  usage on the warehouse, `ANALYTICS` database and `TRADING` schema, plus `select` on current **and future** tables
  (dbt rebuilds the tables on every run, so future grants keep access working)
- An unencrypted private key for `MULE_USER`, stored **outside** this repo (key-pair auth)

## Run locally

1. Copy `src/main/resources/config.example.yaml` to `config.yaml` in the same folder and set the full path to the private key in `private_key_file=`.
2. Open **this folder** (`energy-positions-api`) as the root folder in VS Code. Code Builder requires the Mule project at the workspace root.
3. **Run -> Start Debugging**. The first run downloads the Mule runtime and libraries and takes a few minutes.
4. Wait for `DEPLOYED` in the console, then `curl http://localhost:8081/positions`.

### Troubleshooting

- **"Attribute 'config-ref' must appear"**: the flow XML wasn't saved, or a component isn't linked to its config in `global-configs.xml`.
- **Driver class not found**: check the `sharedLibrary` entry for `snowflake-jdbc` in `pom.xml`.
- **JWT token is invalid**: the private key doesn't match the public key on `MULE_USER`. Compare fingerprints:
  `openssl rsa -in KEY.p8 -pubout -outform DER | openssl dgst -sha256 -binary | openssl enc -base64`
  against `RSA_PUBLIC_KEY_FP` from `desc user MULE_USER;`
- `JDBC_QUERY_RESULT_FORMAT=JSON` in the URL avoids a known Snowflake driver issue on newer Java versions.

## POC shortcuts, and what I'd do in production

- **Secrets:** key path in a git-ignored YAML file. In production: secure (encrypted) properties, with keys held in a secrets manager such as Azure Key Vault and rotated regularly.
- **API-first:** in production I'd write the OpenAPI/RAML spec first, publish it to Anypoint Exchange, and scaffold the flow from it with APIkit.
- **API-led layering:** this app combines layers for simplicity. In a fuller design, a **system API** wraps Snowflake, a **process API** holds the position logic, and **experience APIs** shape the output for each consumer (a dashboard, or an agent's MCP tool).
- **Error handling:** add an error handler returning clean 4xx/5xx JSON instead of default errors.
- **Filtering:** add `?desk=` using Database connector **input parameters**, never string-built SQL, to prevent SQL injection.
- **Deployment:** deploy to CloudHub 2.0 with API Manager policies (client ID enforcement, rate limiting).
- **Agents:** expose `/positions` as an MCP tool so an AI agent can ask "what's the UK desk's position?" through a governed, read-only interface.