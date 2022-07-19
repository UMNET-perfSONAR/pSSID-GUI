# Endpoints

This is documentation of my understanding of the endpoints used by the frontend as of 15 May 2022.

## GET `/init/`

This returns a JSON object of the following format:

```json
{
    "directories": [
        {
            "name": string, // unknown purpose
            "path": string, // the path to the inventory
            "id": number,
            "created": boolean // unknown purpose
        }
    ],
    "token": string // CSRF token
}
```

The directories list returns the data as it is represented in the Django database, not the filesystem. But these are synced every time GET `/init` is received by the backend.

### RESTful Version

To be RESTful this should just be GET `/inventories` instead of GET `/init`.

## GET `/init?directory={{directory_path}`

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
    "bssid_channels": [],
    "ssid_profiles": [],
    "ssid_groups": [],
    "network_interfaces": [],
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

Each of the objects within these arrays appears to be a superset of it's corresponding schema in `pSSIDGUI-root/main/main_spa/src/assets`. These schemas (arrays of `slot`s I guess) are mostly self-descriptive. The type of a slot appears to be determined by its `componentname`. Each `componentname` corresponds with a handler in `pSSIDGUI-root/main/main_spa/src/components/inputTypes`. By going through each one, the types corresponding to each appear to be (at the level of the HTTP request):

| `componentname` | Type |
| - | - |
| `authMethod` | `AuthMethod` per [example_pssid_conf.json](https://github.com/UMNET-perfSONAR/pSSID/blob/37bc129fdfba5e1acf0690c60d46ed9d899432ce/example_pssid_conf.json) |
| `channelPicker` | `number[]` |
| `checkboxInput` | `boolean` |
| `connectionFlags` | `connection_flags` per [example_pssid_conf.json](https://github.com/UMNET-perfSONAR/pSSID/blob/37bc129fdfba5e1acf0690c60d46ed9d899432ce/example_pssid_conf.json) |
| `cronInput` | `...{ minute: string, hour: string, day: string, year: string }` |
| `customInput` | listed under `props.type`, default appears to be `string` |
| `jsonEditor` | arbitrary JSON, it appears |
| `metadataInput` | unknown |
| `nodePicker` | `string` if `props.single == true`, otherwise `string[]`, the strings correspond with the names of the mentioned node |

Each of the objects appears to also have an `id: number` key-value which can simply be set to the index of that element in the array. Finally the `directory` array also contains a `created: boolean` key-value which has unknown use.

### RESTful Version

To be RESTful, the request should just be GET `/inventories/{{inventory_name}}` instead of `/init?directory={{inventory_name}}`.

## POST `/submit/`

The request is of the form:

```json
{
    "tab": string, // e.g. bssid_channel, etc
    "action": "add" | "edit" | "delete",
    "data": object // of the form described in the corresponding schema in `pSSIDGUI-root/main/main_spa/src/assets`
}
```

### Responses

`edit` appears to echo the entire request payload as the response. 

`add` and `delete` appear to echo the content of the `data` attribute, with an `id` key added.

### RESTful Version

The `tab` attribute should be moved to the URL, e.g. for `bssid_channel` the request URL should be `/inventories/{{inventory_name}}/bssid_channel/{{id}}`. This also entails moving the `inventory_name` into the request URL explicitly, instead of storing it in Django state, as it is stored now.

The `action` attribute should be moved to the HTTP method. `add` should be POST†, `edit` should be PUT, `delete` should be DELETE.

The `data` attribute should be the entire payload.

† The POST request URL should be `/inventories/{{inventory_name}}/{{node_name}}` instead of `/inventories/{{inventory_name}}/{{node_name}}/{{id}}`.