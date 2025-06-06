# ckanext-selfinfo

This extension is built to represent a basic information about the running CKAN Application accessible only to admins.

CKAN should be configured to be able to connect to Redis as it heavily relies on it for storage.

On CKAN admin page `/ckan-admin/selfinfo` can see a big variety of information such as System Info, RAM, disk Usage, CKAN Errors, GIT Info and more.

![Main Selfinfo Screen](docs/assets/main_screen.png)

Check full [documentation](https://datashades.github.io/ckanext-selfinfo/) for more information.

## Selftools (new)

Selftools plugin is now available for ckanext-selfinfo.

It is designed to do different sort of operations with SOLR/DB/Redis Data, for example Search within the DB using UI, update records in DB, SOLR search, index Dataset within UI, CKAN config query and more.

You can find more details on what it does and what it needed for in [here](https://datashades.github.io/ckanext-selfinfo/selftools/overview/).

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
