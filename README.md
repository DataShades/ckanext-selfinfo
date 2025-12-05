# ckanext-selfinfo

This extension is built to represent a basic information about the running CKAN Application accessible only to admins.

CKAN should be configured to be able to connect to Redis as it heavily relies on it for storage.

On CKAN admin page `/ckan-admin/selfinfo` can see a big variety of information such as System Info, RAM, disk Usage, CKAN Errors, GIT Info and more.

![Main Selfinfo Screen](docs/assets/main_screen.png)

Check full [documentation](https://datashades.github.io/ckanext-selfinfo/) for more information.

## Selftools

Selftools plugin is now available for ckanext-selfinfo.

It is designed to do different sort of operations with SOLR/DB/Redis Data, for example Search within the DB using UI, update records in DB, SOLR search, index Dataset within UI, CKAN config query and more.

You can find more details on what it does and what it needed for in [here](https://datashades.github.io/ckanext-selfinfo/selftools/overview/).

## Selftracking (new)

Selftracking plugin is now available for ckanext-selfinfo.

An plugin that provides lightweight tracking of user interactions. It records page views, API calls, and supports custom event tracking such as resource downloads, enabling better insights into portal usage and user behavior.

You can find more details on what it does and how to confiugre [here](https://datashades.github.io/ckanext-selfinfo/selftracking/overview/).

## What's New in Version 2

Version 2 introduces several important improvements and breaking changes:

### New Features

- **Enhanced UI Styling** - Completely redesigned interface with improved user experience
- **Action Security** - New `ckan.selfinfo.actions_prefix` configuration option to add custom prefixes to all actions for enhanced security through obscurity
- **Updated Documentation** - Comprehensive documentation updates with better examples and configuration guides

### Breaking Changes

**Category Configuration Changes**

Version 2 changes the default behavior for categories. Previously, all categories were enabled by default. Now you must explicitly configure which categories to use:

- **Selfinfo**: Only `platform_info` is enabled by default, while `status_show` was removed from the list and added by default.
- **Selftools**: Only `solr` is enabled by default

### Upgrading from Version 1 to Version 2

When upgrading from version 1.x to 2.x, you **must** explicitly configure your categories in your CKAN configuration file:

**For Selfinfo**, add to your `.ini` file:

```ini
# Enable all categories (v1 behavior)
ckan.selfinfo.categories_list = python_modules platform_info ram_usage disk_usage git_info freeze errors actions auth_actions blueprints helpers status_show ckan_queues ckan_solr_schema ckan_cli_commands

# Or enable only specific categories you need
ckan.selfinfo.categories_list = platform_info ram_usage disk_usage errors
```

**For Selftools**, add to your `.ini` file:

```ini
# Enable all tools (v1 behavior)
ckan.selftools.categories = solr db redis config model datastore

# Or enable only specific tools you need
ckan.selftools.categories = solr db redis
```

> **Note**: If you don't specify these configurations, only the default categories will be available, which may result in missing functionality you previously relied on.

See the [full documentation](https://datashades.github.io/ckanext-selfinfo/) for detailed configuration options.

## Active work

You can find future features that currently being under development on [this board](https://github.com/orgs/DataShades/projects/1/views/1).

## Requirements

Compatibility with core CKAN versions:

  | CKAN version | Compatibility                           |
  |--------------|-----------------------------------------|
  | 2.7          | untested                                |
  | 2.8          | untested                                |
  | 2.9          | untested                                |
  | 2.10         | yes                                     |
  | 2.11         | yes                                     |
  | master       | yes as of 2025/06 (check test results)  |


## License

MIT
