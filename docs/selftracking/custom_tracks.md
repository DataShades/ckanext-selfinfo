There few options of how you can add your own track types, here two examples:

1. Using `utils` function `selftracking_add_track_to_redis`, which accepts `dict` like this:
    ```
    data = {
        "path": PATH,
        "user": USER_ID,
        "type": TRACK_TYPE,
        "track_time": datetime.utcnow().timestamp(),
    }

    selftracking_add_track_to_redis(data)
    ```
This will store your custom track at Redis and will be stored in DB once `selftracking_store_tracks` action is called.

2. Using javascript that will file on item click (e.g. links like Resource Download):
    ```
    <a class="" href="{{ PATH }}" data-module="selftracking-track-click" data-module-activity="{{ TRACK_TYPE }}" data-module-path="{{ PATH }}">
        <i class="fas fa-scroll" aria-hidden="true"></i>
    </a>
    ```

    `user` and `track_time` will added in the action automatically.

    It will send an ajax call to CKAN that will store you custom track.
