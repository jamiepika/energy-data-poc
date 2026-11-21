-- Clean the raw trades from Fivetran: fix types, sign the volume, drop duplicate loads.
-- Google Sheets data can arrive as text, so every column is cast explicitly.
with typed as (
    select
        trade_id,
        desk,
        instrument,
        upper(side) as side,
        cast(volume_mwh as double) as volume_mwh,
        cast(price_eur as decimal(12, 2)) as price_eur,
        cast(trade_ts as timestamp) as trade_ts_utc,
        cast(loaded_at as timestamp) as loaded_at
    from {{ source('google_sheets', 'raw_trades') }}
)

select
    trade_id,
    desk,
    instrument,
    side,
    volume_mwh,
    case when side = 'BUY' then volume_mwh else -volume_mwh end as signed_volume_mwh,
    price_eur,
    trade_ts_utc
from typed
-- T003 was loaded twice; keep only the latest load of each trade
qualify row_number() over (partition by trade_id order by loaded_at desc) = 1
