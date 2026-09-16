select
    p.station_id,
    p.fuel_type,
    p.price,
    p.station_status,
    p.retrieved_at,
    p.retrieved_at::date as date_day,       -- key to join dim_date
    extract(hour from p.retrieved_at)::int as hour_of_day,  -- for the hour-of-day KPI
    s.brand,
    s.city
from {{ ref('stg_prices') }} p
left join {{ ref('dim_station') }} s
    on p.station_id = s.station_id