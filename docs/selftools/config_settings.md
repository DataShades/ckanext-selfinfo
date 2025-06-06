**`ckan.selftools.opetations_pwd`** - (Recommended) Provides an additional security layer for operations like update/delete/create for the Categoires.

**`ckan.selftools.operations_limit`** - (optional) Sets an limit to most of the operations like query/update. By default the limit is set to `100`.

**`ckan.selftools.categories`** - (optional) You can specify the categories you want to see on Selftools, for example you can remove DB category or leave only Config category. By default if not set, Selftools will show all possbile Categories. Current list looks this `solr db redis config model`.

**`ckan.selftools.tools_blacklist`** - This is needed, when you don't want to remove for example DB Category, but want to disable the Update tools for security reasons, this config params allows you do to this. Here is an example of how it will look like if you want to disable DB Update and Redis Delete tools. In CKAN config we need to provide it like this `db.db_update redis.redis_delete`.

**`ckan.selftools.config_blacklist`** - (optional) In this configuration, you can add CKAN config that you don't want to expose while doing the query as an additional security layer, for example DB conection or Tokens. By default there already an predefined list of CKAN configuations that won't be shown like `sqlalchemy.url` and more. To provide an additional list set it like this `ckan.site_url ckan.site_id` and so on.

**`ckan.selftools.model_fields_blacklist`** - (optional) This setting gives an ability to hide the actual value for specific Model that returs in DB results while doing Query operation. For example if you want to make sure that User email or Package name are not exposed in the results after DB query, you can achieve this by adding list of fields per Model that you want to hide like this `Package.name User.email`, where first part is the Model name and the second one is the field for this model. Default hidden fields are `User.password User.apikey`.

**`ckan.selftools.model_key_ecryption`** - (optional) This settings is used for in Model category to ecrypt the Export data to secure it.
