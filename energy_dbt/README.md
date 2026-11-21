# energy_dbt

Transformation layer of a tiny integration POC:

Google Sheets -> **Fivetran** -> Snowflake (`GOOGLE_SHEETS` schema, raw) -> **dbt** (`ANALYTICS` schema) -> MuleSoft API

## Models
- `stg_trades`: casts types, signs volume (BUY +, SELL -), removes a trade loaded twice
- `stg_prices`: casts types
- `net_position`: net MWh per desk and instrument, valued at the latest settlement price

## Tests
unique / not_null trade IDs, BUY/SELL only, every traded instrument has a price, volumes positive, source freshness (warn after 24h).

## Run
    python -m venv .venv && source .venv/bin/activate
    pip install dbt-snowflake
    # put your profile in ~/.dbt/profiles.yml (see profiles.example.yml)
    dbt debug
    dbt build
    dbt source freshness

## POC shortcut vs requirement
- Shared warehouse for Fivetran and dbt; in production: a separate TRANSFORM warehouse for cost tracking.
- Key-pair auth for service users; secrets kept outside the repo. in prod: encrypted, rotated, managed in vault


## Things I would change
- Naming convention for databases: RAW and ANALYTICS databases rather than FIVETRAN and ANALYTICS. 
- 

