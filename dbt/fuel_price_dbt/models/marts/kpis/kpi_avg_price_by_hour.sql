select
    hour_of_day,
    fuel_type,
    round(avg(price), 3) as avg_price,
    count(*) as observation_count
from {{ ref('fact_price_observation') }}
where brand is not null  -- exclude the unbranded/unknown stations flagged earlier
group by hour_of_day, fuel_type
order by hour_of_day, fuel_type