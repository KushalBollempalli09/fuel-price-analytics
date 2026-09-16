with date_spine as (
    select
        generate_series(
            '2026-09-01'::date,
            '2026-12-31'::date,
            '1 day'::interval
        )::date as date_day
)

select
    date_day,
    extract(year from date_day)::int as year,
    extract(month from date_day)::int as month,
    extract(day from date_day)::int as day_of_month,
    extract(dow from date_day)::int as day_of_week,  -- 0 = Sunday, 6 = Saturday
    to_char(date_day, 'Day') as day_name,
    extract(week from date_day)::int as week_of_year,
    case when extract(dow from date_day) in (0, 6) then true else false end as is_weekend
from date_spine