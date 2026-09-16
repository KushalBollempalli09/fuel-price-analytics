with source as (
    select
        station_id,
        payload,
        retrieved_at
    from {{ source('raw', 'stations') }}
),

-- station details barely change, but we've pulled the same station
-- multiple times across different city/run overlaps — keep only the
-- most recent snapshot per station
deduped as (
    select
        *,
        row_number() over (
            partition by station_id
            order by retrieved_at desc
        ) as rn
    from source
)

select
    station_id,
    payload ->> 'name'        as station_name,
    payload ->> 'brand'       as brand,
    payload ->> 'street'      as street,
    payload ->> 'houseNumber' as house_number,
    payload ->> 'postCode'    as post_code,
    payload ->> 'place'       as city,
    (payload ->> 'lat')::numeric as latitude,
    (payload ->> 'lng')::numeric as longitude,
    (payload ->> 'isOpen')::boolean as is_open,
    retrieved_at as last_seen_at
from deduped
where rn = 1