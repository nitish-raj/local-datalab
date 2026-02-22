with ranked_observations as (
    select
        aoi_id,
        observed_on,
        status,
        mean_ndvi,
        cloud_cover,
        item_datetime,
        source_bucket,
        source_key,
        loaded_at,
        row_number() over (
            partition by aoi_id, observed_on
            order by loaded_at desc
        ) as latest_rank
    from {{ ref('stg_raw_ndvi_observations') }}
)

select
    aoi_id,
    observed_on,
    status,
    mean_ndvi,
    cloud_cover,
    item_datetime,
    source_bucket,
    source_key,
    loaded_at,
    case
        when status = 'ok' and mean_ndvi is not null then true
        else false
    end as is_valid_observation
from ranked_observations
where latest_rank = 1
