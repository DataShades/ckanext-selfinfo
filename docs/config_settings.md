# Configuration Settings

## Core Settings

### `ckan.selfinfo.redis_prefix_key`

**Type:** `string`
**Required:** Recommended for multi-instance setups

This configuration is needed when you use Redis with multiple CKAN applications. It provides a unique key per portal instance.

**Example:**

```ini
ckan.selfinfo.redis_prefix_key = ckan_test
```

This will be used as `ckan_test_errors_selfinfo` in Redis.

---

### `ckan.selfinfo.page_url`

**Type:** `string`
**Default:** `/ckan-admin/selfinfo`
**Required:** Recommended

Provides an alternative URL to the Selfinfo admin page.

**Example:**

```ini
ckan.selfinfo.page_url = /admin/system-info
```

---

### `ckan.selfinfo.main_action_name`

**Type:** `string`
**Default:** `get_selfinfo`
**Required:** Recommended

Provides an alternative name for the main action of Selfinfo.

**Example:**

```ini
ckan.selfinfo.main_action_name = system_info
```

---

### `ckan.selfinfo.actions_prefix`

**Type:** `string`
**Default:** Empty (no prefix)
**Required:** Optional

Adds a custom prefix to all registered API actions from Selfinfo, Selftools, and Selftracking extensions. This provides an additional security layer by obscuring action names, making them harder to discover.

!!! note "Scope"
    This prefix applies to **all three extensions**:

    - **Selfinfo** actions (except `get_selfinfo` which uses `ckan.selfinfo.main_action_name`)
    - **Selftools** actions
    - **Selftracking** actions

!!! warning "Important"
    When using a prefix, you must use the helper function `h.selfinfo_action_name()` in templates and code to construct the correct action name.

**Example:**

```ini
# Add "custom" prefix to all actions
ckan.selfinfo.actions_prefix = custom
```

**Usage in code:**

```python
from ckanext.selfinfo import helpers

# Instead of calling the action directly:
# tk.get_action("selfinfo_get_ram")(context, {})

# Use the helper to get the prefixed name:
tk.get_action(helpers.selfinfo_action_name("selfinfo_get_ram"))(context, {})
```

---

## Categories and Display

### `ckan.selfinfo.categories_list`

**Type:** `space-separated list`
**Default:** `platform_info`
**Required:** Optional

List of categories that should be shown on the Selfinfo page or returned using the API.

Check the full list of available [Categories](configuration/categories.md).

**Example:**

```ini
ckan.selfinfo.categories_list = platform_info errors ram_usage disk_usage
```

---

## Storage and Limits

### `ckan.selfinfo.partitions`

**Type:** `space-separated paths`
**Default:** `/`
**Required:** Optional

Specifies paths for disk space monitoring. The value is a space-separated list of partition paths. Required only for `disk_usage` category.

**Example:**

```ini
ckan.selfinfo.partitions = /path/to/partition /path/to/partition2 /path/to/partition3
```

---

### `ckan.selfinfo.errors_limit`

**Type:** `integer`
**Default:** `40`
**Required:** Optional

Limits how many errors will be stored in Redis.

**Example:**

```ini
ckan.selfinfo.errors_limit = 100
```

---

## Git Repository Information

### `ckan.selfinfo.ckan_repos_path`

**Type:** `path`  
**Required:** Optional

Path to the source folder where CKAN and CKAN extensions are stored in the environment. When provided, additional Git information will be available. Required for `git_info` category.

!!! warning "Important"
    Ensure that only CKAN-related folders are stored in this path. Other files and folders may cause errors.

**Example:**

```ini
ckan.selfinfo.ckan_repos_path = /usr/lib/ckan/default/src
```

---

### `ckan.selfinfo.ckan_repos`

**Type:** `space-separated list`  
**Required:** Optional

List of CKAN extension folder names. By default, if `ckan.selfinfo.ckan_repos_path` is provided, it will automatically discover extensions from that directory.

**Example:**

```ini
ckan.selfinfo.ckan_repos = ckanext-scheming ckanext-spatial ckanext-xloader
```

!!! note "Linux Permissions"
    For Linux systems, ensure that folders in `ckan.selfinfo.ckan_repos_path` have the same owner as the user running the application.

    For example, if the application runs as the `ckan` user, then the `ckanext-scheming` folder owner should also be `ckan`. Otherwise, you may encounter repository ownership errors.

    Git-related errors are displayed below the repository table on the Git Info tab.

---

## Solr Configuration

### `ckan.selfinfo.solr_schema_filename`

**Type:** `string`
**Required:** Optional

Specifies the filename that Solr uses for the CKAN schema. Required for `ckan_solr_schema` category.

See [Enable Solr Schema](configuration/solr_schema.md) for more details.

**Example:**

```ini
ckan.selfinfo.solr_schema_filename = schema.xml
```

---

## Additional Profiles

### `ckan.selfinfo.additional_profiles_using_redis_keys`

**Type:** `space-separated list`  
**Required:** Optional

Retrieves Selfinfo data from external sources that store data using the `write-selfinfo` CLI command under unique Redis keys. The stored data must use the same Redis connection as the "default" profile.

**Example:**

```ini
ckan.selfinfo.additional_profiles_using_redis_keys = unique_redis_key_1 unique_redis_key_2
```

---

### `ckan.selfinfo.additional_profiles_expire_time`

**Type:** `integer` (seconds)
**Required:** Optional

Defines how long additional profiles will exist before being automatically deleted. Must be a positive integer representing lifetime in seconds.

**Example:**

```ini
# 1 hour = 3600 seconds
ckan.selfinfo.additional_profiles_expire_time = 3600
```

---

## Duplicated Environments

### `ckan.selfinfo.duplicated_envs.mode`

**Type:** `boolean`
**Default:** `False`
**Required:** Optional

When enabled, removes the `default` profile and replaces it with duplicated environments.

See [Selfinfo under Redis internal env IP key](profiles/duplicated_env.md) for more details.

**Example:**

```ini
ckan.selfinfo.duplicated_envs.mode = True
```

---

### `ckan.selfinfo.shared_categories_list`

**Type:** `space-separated list`  
**Required:** Optional

Used in combination with `ckan.selfinfo.duplicated_envs.mode` to specify which categories are shared between duplicated environments.

See [Shared categories](profiles/shared_categories.md) for more details.

**Example:**

```ini
ckan.selfinfo.shared_categories_list = platform_info ckan_information
```
