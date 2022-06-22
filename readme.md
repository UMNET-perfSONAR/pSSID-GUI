# pSSID-GUI

A Web Interface for configuring [pSSID](https://github.com/UMNET-perfSONAR/pSSID) by editing Ansible config files

Requirements: `node >= 10`, `npm`, `python3`, `pip3`

Provided example Ansible directory at `/inventory`

Built with Vue and Django

Installation:

- `pip3 install -r pSSIDGUI-root/requirements.txt`

- `chmod +x build_dev`

- `./build_dev [IP]:[PORT]`: build Vue and host Django dev server at IP:PORT

- MacOS: if you get something like `nodename nor servname provided, or not known`, run `echo 127.0.0.1 $HOSTNAME >> /etc/hosts` as root

After building, if no changes were made you can use `./run_dev [IP]:[PORT] to just run the server.

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

```
wget https://kojipkgs.fedoraproject.org//packages/sqlite/3.9.0/1.fc21/x86_64/sqlite-3.9.0-1.fc21.x86_64.rpm

sudo yum install sqlite-3.9.0-1.fc21.x86_64.rpm
```

## Provisioning and Running

Do the following on the system on which you want the web server and Ansible controller hosted:

1. Install Docker using the system package manager.
1. Start the Docker daemon with `systemctl start docker` as root (assumes a systemd system).
1. Run `chmod 666 /var/run/docker.sock` to prevent permissions problems.
1. Install `docker-compose` using the system package manager. Verify installation with `docker-compose -v`.
    * If the system package manager gives errors, just install the static binary from GitHub Releases [somewhat like this](https://phoenixnap.com/kb/install-docker-compose-centos-7).
1. Install Ansible using the system package manager. Verify installation with `ansible-playbook -v`.
1. 
        git clone https://github.com/UMNET-perfSONAR/pSSID-GUI
        git checkout fixes
1. Run `./build_all` to build the Docker container. The web service should be accessible at `host:8080`. Add an inventory and a host there.
1. Run `ssh-keygen` to generate ssh keys and somehow get the public key to the RPis to which you want to deploy.
1. Create `ansible/logins.json` containing the SSIDs and passwords that will be copied to the target machines' `/etc/pscheduler/tests` file. Encrypt the file using `ansible-vault encrypt ansible/logins.json` so it can be checked into version control.
1. Run the following to generate and copy a pSSID configuration for and to each host you have added to your inventory via the web service:
    ```
    ansible-playbook --inventory inventories/$(name) --become --become-user root --ask-become-pass --become-method su ansible/playbook.yml --ask-vault-pass
    ```