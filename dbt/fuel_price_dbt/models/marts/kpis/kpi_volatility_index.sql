with station_stats as (
    select
        station_id,
        fuel_type,
        avg(price) as avg_price,
        stddev(price) as price_stddev,
        count(*) as observation_count
    from {{ ref('fact_price_observation') }}
    group by station_id, fuel_type
    having count(*) >= 10  -- need enough observations for stddev to mean anything
)

select
    s.station_id,
    st.station_name,
    st.brand,
    st.city,
    s.fuel_type,
    round(s.avg_price, 3) as avg_price,
    round(s.price_stddev, 4) as price_stddev,
    round(s.price_stddev / s.avg_price, 4) as coefficient_of_variation,
    s.observation_count
from station_stats s
left join {{ ref('dim_station') }} st
    on s.station_id = st.station_id
order by coefficient_of_variation desc