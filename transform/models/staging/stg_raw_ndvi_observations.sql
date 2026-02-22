select
    aoi_id,
    observation_date as observed_on,
    status,
    mean_ndvi,
    cloud_cover,
    item_datetime,
    source_bucket,
    source_key,
    loaded_at
from {{ source('raw', 'raw_ndvi_observations') }}
