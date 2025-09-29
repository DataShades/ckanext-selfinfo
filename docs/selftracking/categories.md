You can add your own custom categories to Selftracking section alongside Page View and API View or modify the exisitng categories.

### CKAN Hook

There is an interface `ISelftracking` that has an method `selftracking_categories`, which provides you an ability to extend or modify categories list.

Example of how it might look in your `plugin.py` file:

``` py
from ckanext.selftracking.interfaces import ISelftracking

class MyPlugin(plugins.SingletonPlugin):
    plugins.implements(ISelftracking, inherit=True)

    def selftracking_categories(self, models_list):
        # Modifications done to categories here
        # You can register any category you need, it shouldn't be only Track types, but an custom dashboards
        # Example of structure
        new_category = {
            "key": "resource_download",
            "label": "Resource Downloads",
            "snippet": "CUSTOM_PATH_TO_SNIPPET", # Example /YOUR_EXTENSION/snippets/selftracking_resource_download.html
        }

        categories.append(new_category)

        return categories
```

Within your snippet you'll need to prepare an variable or logic that will return expected data. Here is an example of variable using helper function, but you can construct anything you would like, even an full functional dashboard based of your needs:
```
{% set resource_download_data = h.selftracking_get_view_data("resource download") %}

<div class="p-3 mt-4">
    <div class="table-responsive">
        <div class="d-flex justify-content-between mb-3 align-items-center">
          <button class="btn btn-dark" onclick="copyTableJsonToClipboard('selftracking-api-views-path')">
            Copy as JSON
          </button>
        </div>
        <table id="selftracking-resource-download-path" class="table table-striped table-bordered table-hover" data-module="selftracking-views-table" data-module-target="selftracking-api-views-path">
            <thead class="table-light">
              <tr>
                  <th scope="col">{{ _('Path') }}</th>
                  <th scope="col">{{ _('Views') }}</th>
              </tr>
            </thead>
            <tbody>
              {% for row in api_view_data %}
                <tr>
                    <td>{{ row[0] }}</td>
                    <td>{{ row[1] }}</td>
                </tr>
              {% endfor %}
            </tbody>
        </table>
    </div>
</div>

```

