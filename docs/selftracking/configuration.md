Make sure to re-install Selfinfo extension mentioned in [Installation](../installation.md) step.

To enable `selftracking`:

1. Add `selftracking` plugin before `selfinfo` plugin at `ckan.plugins`, so it will inherit its templates.

2. Initialize `selftracking` tables in DB:
     ```
     ckan -c CKAN_CONFIG_PATH db upgrade -p selftracking
     ```

3. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:
     ```
     sudo service apache2 reload
     ```

4. The data won't autocatically will be saved in your DB, so in order to make it appear from Redis in your DB, you'll either need to figure out an way to call `selftracking_store_tracks` that will store tracks in DB or use Cron job for this (calls the action every 10 mins):
     ```
     */10 * * * * /usr/lib/ckan/VIRTUAL_ENV/bin/ckan -c CONFIG_PATH selftracking store-tracking > /dev/null 2>&1
     ```
     CKAN jobs worker is not used for this, as it can be stuck in the queue, which we don't want to happen if there big Resources that should be indexed to the Datastore.
