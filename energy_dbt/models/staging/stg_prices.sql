select
    instrument,
    cast(price_date as date) as price_date,
    cast(settle_price_eur as decimal(12, 2)) as settle_price_eur
from {{ source('google_sheets', 'raw_prices') }}
