# pSSID-GUI

pSSID-GUI is a web app for creating Ansible inventories usable by [ansible-playbook-pssid-daemon](https://github.com/UMNET-perfSONAR/ansible-playbook-pssid-daemon) for configuring Raspberry Pi's running [pSSID](https://github.com/UMNET-perfSONAR/pSSID).

![Demo Image](images/wide-view.png)

## Running Locally

Install Docker (along with `docker-compose`/`docker compose`). Configure various settings by changing the values in `.env`. Run

```
docker compose up --build
```

to build it and run in the foreground. Optionally append ` -d` to run it in the background and use `--env-file` to specify the path to the `.env` file if it is not in `./.env`, like so

```
docker compose --env-file /etc/pssid-gui/.env up --build -d
```

## Provisioning

Use [ansible-playbook-pssid-gui](https://github.com/UMNET-perfSONAR/ansible-playbook-pssid-gui) to provision.

## Documentation

See [frontend/readme.md](src/frontend/readme.md) and [backend/readme.md](src/backend/readme.md).
