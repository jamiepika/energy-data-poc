-- Net position per desk and instrument, valued at the latest settlement price
with positions as (
    select desk, instrument, sum(signed_volume_mwh) as net_position_mwh
    from {{ ref('stg_trades') }}
    group by desk, instrument
),

latest_prices as (
    select instrument, settle_price_eur
    from {{ ref('stg_prices') }}
    qualify row_number() over (partition by instrument order by price_date desc) = 1
)

select
    p.desk,
    p.instrument,
    p.net_position_mwh,
    lp.settle_price_eur,
    p.net_position_mwh * lp.settle_price_eur as position_value_eur
from positions p
left join latest_prices lp using (instrument)
