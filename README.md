# pSSID-GUI

A Web Interface for configuring [pSSID](https://github.com/UMNET-perfSONAR/pSSID) by editing Ansible config files

Requirements: `node >= 10`, `npm`, `python3`, `pip3`

Provided example Ansible directory at `/inventory`

Built with Vue and Django

Installation:

- `pip3 install -r pSSIDGUI-root/requirements.txt`

- `chmod +x build_dev`

- `./build_dev [IP]:[PORT]`: build Vue and host Django dev server at IP:PORT

After building, if no changes were made you can use `./run_dev [IP]:[PORT] to just run the server.

# Docs (to be put in wiki when repo is public)

## Frontend Structure

### App.vue

Main Vue component, requests pSSID data via AJAX when the user submits a directory
Also stores the data for the rest of the components to use
Templates most of the static visuals, like the navbar

### nodeVue.vue

Maintain a list of hosts, groups, etc.
Each "node" in the list opens an instance of vueEditor.vue with the appropriate start values in the form
The add node button opens a blank form instance
Remove node sends an AJAX request to delete it, the refresh button emits an event to the parent App.vue to refresh the pSSID data

### vueEditor.vue

Gets a JSON schema for the corresponding node type (located in the directory `assets`) and sets Vue slots using [vue-form-json](https://github.com/14nrv/vue-form-json)
Then it uses the same schema to fill the slots with different `inputTypes`, and initializes those `inputTypes` with starting data by checking the `slot` property and comparing with the data received from pSSID
For example if a node has a key called "SSID" then the slot with name "SSID" would get initvalue set to node["SSID"]
`extraData` can be used to bring in other pSSID data, such as `hosts` for the host picker in the group editor

## Backend Structure

All backend functionality is implemented through AJAX calls that are routed through `urls.py` and return JSON data in `views.py`
When the site is first loaded, it requests `/init/` and returns directory data from the requests active session
When a directory is picked, it requests `/init/` again but returns the corresponding pSSID data from the selected directory
When any other user input is processed, namely add/remove/edit nodes, it requests `/submit/` and the corresponding function in `views.py` is called to generate the right config format in the selected Ansible directory

Footnote: troubleshooting setup with Centos 7:

Use this command to update `sqlite`:
`wget https://kojipkgs.fedoraproject.org//packages/sqlite/3.9.0/1.fc21/x86_64/sqlite-3.9.0-1.fc21.x86_64.rpm

sudo yum install sqlite-3.9.0-1.fc21.x86_64.rpm`
