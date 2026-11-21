-- A test passes when this query returns zero rows
select *
from {{ ref('stg_trades') }}
where volume_mwh <= 0
