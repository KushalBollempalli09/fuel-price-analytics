select
    station_id,
    station_name,
    brand,
    street,
    house_number,
    post_code,
    city,
    latitude,
    longitude,
    is_open,
    last_seen_at
from {{ ref('stg_stations') }}