**`ckan.selftracking.redis_prefix`** - (Recommended) Adds prefix to Redis Selftracking key, so it will be unique. For example `my_project_name`, as an result it will store tracks under `my_project_name_selftracking_tracks` key.

**`ckan.selftracking.categories`** - (optional) Manages that list of categories shown on the Selftracking page. For example you don't need `Page Views`, so the categories will be `main api_view`.

**`ckan.selftracking.redis_batch_size`** - (optional) Sets the amount of tracks that will be stored in DB per 1 call of `selftracking_store_tracks` action. By default its `300`.

**`ckan.selftracking.type_color.`** - (optional) Sets an color for specific track type for all graphics. For example if we want `page view` type to be `rgba(0, 128, 0, 0.7)` the config will look like `ckan.selftracking.type_color.page_view = rgba(0, 128, 0, 0.7)`, the name of the type should use underscore instead of space. HEX colors can be used as well. By default the color is being constracted based on the track type string.
