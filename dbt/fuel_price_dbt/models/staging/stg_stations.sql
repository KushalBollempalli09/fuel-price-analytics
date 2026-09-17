with source as (
    select
        station_id,
        payload,
        retrieved_at
    from {{ source('raw', 'stations') }}
),

deduped as (
    select
        *,
        row_number() over (
            partition by station_id
            order by retrieved_at desc
        ) as rn
    from source
),

cleaned as (
    select
        station_id,
        payload ->> 'name'        as station_name,
        payload ->> 'brand'       as brand,
        payload ->> 'street'      as street,
        payload ->> 'houseNumber' as house_number,
        payload ->> 'postCode'    as post_code,
        payload ->> 'place'       as raw_city,
        (payload ->> 'lat')::numeric as latitude,
        (payload ->> 'lng')::numeric as longitude,
        (payload ->> 'isOpen')::boolean as is_open,
        retrieved_at as last_seen_at
    from deduped
    where rn = 1
)

select
    c.station_id,
    c.station_name,
    c.brand,
    c.street,
    c.house_number,
    c.post_code,
    coalesce(m.canonical_city, c.raw_city) as city,
    c.latitude,
    c.longitude,
    c.is_open,
    c.last_seen_at
from cleaned c
left join {{ ref('city_name_mapping') }} m
    on c.raw_city = m.raw_city