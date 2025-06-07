# ckanext-selfinfo

This extension is built to represent a basic information about the running CKAN Application accessible only to admins.

![Main Selfinfo Screen](assets/main_screen.png)

CKAN should be configured to be able to connect to Redis as it heavily relies on it for storage.

On CKAN admin page `/ckan-admin/selfinfo`, admin can see such information as:

* **System Information**
    - System Platform
    - Distribution
    - Python version
* **RAM**
    - RAM Usage in %
    - RAM Usage GB
    - RAM Total
    - Monitor feature
        - Top 10 processes shown
* **Disk Space**
    - Path
    - Disk Usage in %
    - Disk Total
    - Disk Free
* **CKAN Information**
    - Basic Information
    - Actions
    - Auth
    - Helpers
    - Blueprints
    - CLI Commands
* **GIT Information** (Optional, see [Config Settings section](configuration/git_info.md))
    - Project
    - Head
    - Based on
    - Commit
    - Remotes
    - Errors info in case if cannot be shown
* **PIP Freeze**
    - List of modules that are installed.
* **Python Information**
    - Provides information about CKAN Core, CKAN Extensions, Python installed packages. It shows their current version and latest version.
* **CKAN Queues**
    - Show queues and their active jobs.
* **Solr Schema** (Optional, see [Enable Solr Schema](configuration/solr_schema.md))
    - Shows CKAN Solr Schema.
* **Errors** (Optional, see [Enable Error Saving](configuration/errors.md))
    - Shows latest exceptions.


Recommened to firstly visit [Secure URL and Action](configuration/secure_url_and_action.md) and [Unique Redis key](configuration/unique_redis_key_per_portal_instance.md) after the installation done.
