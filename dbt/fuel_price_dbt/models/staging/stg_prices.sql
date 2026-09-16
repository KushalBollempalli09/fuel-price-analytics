with source as (
    select
        station_id,
        payload,
        retrieved_at
    from {{ source('raw', 'prices') }}
),

-- Tankerkönig packs 3 fuel types into one row per pull. For the eventual
-- fact table (one row per station, per fuel type, per observation), it's
-- easier to work with "long" format now: one row per fuel type instead
-- of 3 columns. UNION ALL stacks the 3 fuel types on top of each other.
unpivoted as (
    select station_id, retrieved_at, payload ->> 'status' as station_status,
           'e5' as fuel_type, payload ->> 'e5' as raw_price
    from source
    union all
    select station_id, retrieved_at, payload ->> 'status' as station_status,
           'e10' as fuel_type, payload ->> 'e10' as raw_price
    from source
    union all
    select station_id, retrieved_at, payload ->> 'status' as station_status,
           'diesel' as fuel_type, payload ->> 'diesel' as raw_price
    from source
)

select
    station_id,
    fuel_type,
    station_status,
    raw_price::numeric as price,
    retrieved_at
from unpivoted
-- when a station is closed or doesn't report a fuel type, Tankerkönig
-- returns `false` instead of a number for that field — this regex keeps
-- only rows where raw_price actually looks like a number, so the cast
-- above never fails on a stray "false"
where raw_price ~ '^[0-9]+(\.[0-9]+)?$'