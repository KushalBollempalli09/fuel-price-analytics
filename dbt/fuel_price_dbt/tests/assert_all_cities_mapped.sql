-- This test fails (returns rows) if any city value in the raw source data
-- isn't yet covered by city_name_mapping.csv. A new/unmapped value here
-- means someone needs to review it and add a row to the seed — the test
-- exists specifically so that step never gets silently skipped.

select distinct
    raw_stations.payload ->> 'place' as unmapped_raw_city
from {{ source('raw', 'stations') }} raw_stations
left join {{ ref('city_name_mapping') }} m
    on raw_stations.payload ->> 'place' = m.raw_city
where m.raw_city is null