# energy_dbt

Transformation layer of a tiny integration POC:

Google Sheets -> **Fivetran** -> Snowflake (`GOOGLE_SHEETS` schema, raw) -> **dbt** (`ANALYTICS.TRADING` database.schema) -> MuleSoft API

## Models
- `stg_trades`: (view) casts types, signs volume (BUY +, SELL -), removes a trade loaded twice
- `stg_prices`: (view) casts types
- `net_position`: (table) MWh per desk and instrument, valued at the latest settlement price

## Tests
unique / not_null trade IDs, BUY/SELL only, every traded instrument has a price, volumes positive, source freshness (warn after 24h).

## Access Pre-Reqs
Needs a DBT_USER key pair (see Access in the root README).

## Run
    python -m venv .venv && source .venv/bin/activate
    pip install dbt-snowflake
    # put your profile in ~/.dbt/profiles.yml (see profiles.example.yml)
    dbt debug
    dbt build
    dbt source freshness

## Changes for prod
- Currently shared warehouse for Fivetran and dbt; in production: a separate TRANSFORM warehouse for cost tracking
- Separate STAGING and MARTS schemas, so consumers like the API only see marts
- Key-pair auth for service users; secrets kept outside the repo. in prod: encrypted, rotated, managed in vault
- IRL I'd have different naming convention for databases: RAW and ANALYTICS databases rather than FIVETRAN and ANALYTICS. 

