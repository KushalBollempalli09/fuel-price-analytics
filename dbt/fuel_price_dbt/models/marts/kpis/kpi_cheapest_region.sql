select
    city,
    fuel_type,
    round(avg(price), 3) as avg_price,
    round(min(price), 3) as min_price,
    count(distinct station_id) as station_count
from {{ ref('fact_price_observation') }}
where brand is not null and trim(brand) <> ''
group by city, fuel_type
having count(distinct station_id) >= 10  -- keep only cities with enough stations for a fair comparison
order by fuel_type, avg_price asc