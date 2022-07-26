# pSSID-GUI Backend

Requests are fed through the dispatcher in `urls.py`, which passes them to the functions `submit()` and `init()` in `views.py`. `views.py` contains nearly all of the logic.

`default-inventory/` is the reference inventory that is copied when you create new inventories in the UI.

## Endpoints

### GET `/init/`

This returns a JSON object of the following format:

```json
{
    "directories": [
        {
            "name": string,
            "path": string, // the path to the inventory
            "id": number,
            "created": boolean // unknown purpose
        }
    ],
    "token": string // CSRF token
}
```

The directories list returns the data as it is represented in the Django database, not the filesystem. But these are synced every time GET `/init` is received by the backend.

#### RESTful Version

To be RESTful this should just be GET `/inventories` instead of GET `/init`.

### GET `/init?directory={{directory_path}`

This is very different from `/init/`; it returns JSON for all the Ansible data. Here is an example return:

```json
{
    "hosts": [],
    "groups": [
        {
            "name": "all",
            "nodes": [],
            "id": 0,
            "meta": [],
            "tasks": []
        }
    ],
    "schedules": [
        {
            "id": 0,
            "name": "Julie",
            "repeatstring": "1 2 3 4 5",
            "repeat": {
                "minute": "1",
                "hour": "2",
                "day": "3",
                "month": "4",
                "year": "5"
            }
        }
    ],
    "ssid_profiles": [],
    "bssid_scans": [],
    "archivers": [],
    "tests": [],
    "tasks": [],
    "directories": [
        {
            "name": "test-directory",
            "path": "inventory",
            "id": 0,
            "created": false
        }
    ],
    "testnames": [],
    "archivernames": [],
    "token": "wqe8Ke7XwJbmS6bE97McwwhxaGUIteKrwvuWQ3SaueVJzd2IW9cmR8QNI2JPYYEW"
}
```

Each of the objects within these arrays appears to be a superset of it's corresponding schema in `src/frontend/src/assets` (and described in [`src/frontend/readme.md`](../frontend/readme.md)).

Each of the objects appears to also have an `id: number` key-value which can simply be set to the index of that element in the array. Finally the `directories` array (representing inventories) also contains a `created: boolean` key-value which has unknown use.

`testnames` and `archivernames` are arrays of objects of the form `{ name: string }` which enumerate the possible test types and archiver types respectively.

#### RESTful Version

To be RESTful, the request should just be GET `/inventories/{{inventory_name}}` instead of `/init?directory={{inventory_name}}`.

### POST `/submit/`

The request is of the form:

```json
{
    "tab": string, // e.g. ssid_profile, etc
    "action": "add" | "edit" | "delete",
    "data": object // of the form described in the corresponding schema in `src/frontend/src/assets`
}
```

`"delete"` deletes the element matching `data.name`. `"add"` appends `data` as a new element. `"edit"` overwrites the element with name `data.name` with `data`.

The CSRF token is absent in the request, so is either in the headers or completely neglected.

#### Responses

`edit` appears to echo the entire request payload as the response. 

`add` and `delete` appear to echo the content of the `data` attribute, with an `id` key added.

#### RESTful Version

The `tab` attribute should be moved to the URL, e.g. for `bssid_channel` the request URL should be `/inventories/{{inventory_name}}/bssid_channel/{{id}}`. This also entails moving the `inventory_name` into the request URL explicitly, instead of storing it in Django state, as it is stored now.

The `action` attribute should be moved to the HTTP method. `add` should be POST†, `edit` should be PUT, `delete` should be DELETE.

The `data` attribute should be the entire payload.

† The POST request URL should be `/inventories/{{inventory_name}}/{{node_name}}` instead of `/inventories/{{inventory_name}}/{{node_name}}/{{id}}`.