select
    brand,
    fuel_type,
    round(min(price), 3) as min_price,
    round(max(price), 3) as max_price,
    round(max(price) - min(price), 3) as price_spread,
    round(avg(price), 3) as avg_price,
    count(distinct station_id) as station_count
from {{ ref('fact_price_observation') }}
where brand is not null and trim(brand) <> ''
group by brand, fuel_type
having count(distinct station_id) >= 5
order by price_spread desc