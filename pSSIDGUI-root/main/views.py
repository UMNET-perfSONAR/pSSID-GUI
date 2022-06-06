'''
Main Backend File
'''

from copy import deepcopy as copy  # forgive me for my sins
import os
import shutil
import traceback


from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from django.http.response import JsonResponse
from django.template import loader
from django.middleware.csrf import get_token
import requests
from urllib3.exceptions import InsecureRequestWarning
import yaml
from yaml.loader import SafeLoader
from pathlib import Path

# TODO: these should be configurable in a config file
# they should also probably be absolute paths
INVENTORIES_DIRECTORY = Path("inventories")
DEFAULT_INVENTORY = Path("default-inventory")

requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# used when making nodes for bootstrap styling


def bootstrap_bg(status):
    if status:
        return "success"
    return "danger"

def removeByKeyVal(x, key, val):
    for i in range(len(x)):
        if x[i][key] == val:
            x.pop(i)
            return
def replaceByKeyVal(x, key, val, newdata):
    for i in range(len(x)):
        if x[i][key] == val:
            x[i] = newdata
            return

def hosts_add(address, group, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.safe_load(f)

    if group not in hosts_yml:
        raise HttpResponse("Cannot add host to group that doesn't exist", status="400")

    if hosts_yml[group]["hosts"] is None:
        hosts_yml[group]["hosts"] = {}
    hosts_yml[group]["hosts"][address] = None

    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)


def hosts_remove(address, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.safe_load(f)
    
    for group_name, group_content in hosts_yml.items():
        group_content["hosts"].pop(address, None)

    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)

# change the ip address of a host
def hosts_edit(old_address, new_address, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.safe_load(f)
    
    # `copy` is to avoid `RuntimeError: dictionary keys changed during iteration`
    for group_name, group_content in hosts_yml.copy().items():
        for host_name, host_content in group_content["hosts"].copy().items():
            if host_name == old_address:
                hosts_yml[group_name]["hosts"][new_address] = hosts_yml[group_name]["hosts"].pop(old_address)

    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)


# add a group to hosts.yml
def group_add(group, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.load(f, Loader=SafeLoader)

    hosts_yml[group] = { "hosts": {} }
    
    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)


# remove a group from hosts.yml
def group_remove(group, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.load(f, Loader=SafeLoader)

    hosts_yml.pop(group, None)

    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)

# change `old_group`'s name to `new_group` and
# change its list of hosts to `hosts`
def group_edit(old_group, new_group, hosts, request):

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.load(f, Loader=SafeLoader)

    hosts_yml.pop(old_group, None)
    hosts_yml[new_group] = {
        "hosts": dict.fromkeys(hosts, None)
    }

    with open(request.session["directory"] + "/hosts.yml", "w") as f:
        yaml.dump(hosts_yml, f, indent=2, sort_keys=False)


def make_node(name, ip, meta, node_id):

    new_node = {"name": name, "ip": ip, "host_meta": meta, "status": bootstrap_bg(
            True), "id": node_id, "host_batches": []}
    return new_node


def submit_host(request, data, action):
    #
    # submit a host
    # every other node type is implemented in a similar fashion, separating add/edit/remove
    #
    new_node = {}

    response = data

    if response.get("id") is None:
        node_id = len(request.session["hosts"])
    else:
        node_id = response.get("id")
    name = response["name"]
    ip = response["ip"]
    meta = response.get("meta", [])

    new_node = make_node(name, ip, meta, node_id)
    new_node.pop("host_meta")
    new_node["host_batches"] = response["batches"]
    
    if action == "add":
        for i in request.session["hosts"]:
            if i["name"] == name:
                return HttpResponse(status="503")
        Path(request.session["directory"] + "/host_vars/" + ip).mkdir(parents=True)
        hosts_add(ip, "all", request)
        request.session["hosts"].append(new_node)

    elif action == "edit":
        oldip = request.session["hosts"][node_id]["ip"]
        os.rename(request.session["directory"] + "/host_vars/" +
                    oldip, request.session["directory"] + "/host_vars/" + ip)
        hosts_edit(oldip, ip, request)
        request.session["hosts"][node_id] = new_node

    elif action == "delete":
        shutil.rmtree(
            request.session["directory"] + "/host_vars/" + ip)
        hosts_remove(ip, request)
        i = 0
        while i < len(request.session["hosts"]):
            if request.session["hosts"][i]["id"] == node_id:
                request.session["hosts"].pop(i)
                continue
            i += 1
        request.session.modified = True
        return JsonResponse({"success": True})

    with open(request.session["directory"] + "/host_vars/" + ip + "/pssid_conf.yml", "w") as f:
        f.seek(0)
        yaml.dump(new_node, f, indent=2, sort_keys=False)
    with open(request.session["directory"] + "/host_vars/" + ip + "/meta.yml", "w") as f:
        f.seek(0)
        yaml.dump({"host_meta": meta}, f, indent=2, sort_keys=False)

    request.session.modified = True
    return JsonResponse(new_node, safe=False)


def submit_group(request, data, action):
    print(request.session["groups"])
    new_group = {}

    response = data
    
    if response.get("id") is None:
        node_id = len(request.session["groups"])
    else:
        node_id = response.get("id")
    name = response["name"]
    nodes = response["nodes"]
    meta = response["meta"]
    batches = response["batches"]
    batches_key = f"{name}_batches"
    meta_key = f"{name}_meta"
    new_group = {"name": name, "nodes": nodes, meta_key: meta, "id": node_id, batches_key: batches}
    try:

        if action == "add":
            for i in request.session["groups"]:
                if i["name"] == name:
                    return HttpResponse(status="503")

            Path(request.session["directory"] + "/group_vars/" + name).mkdir(parents=True,exist_ok=True)

            with open(request.session["directory"] + "/group_vars/" + name + "/meta.yml", "w") as f:
                yaml.dump({meta_key: new_group[meta_key]}, f, indent=2, sort_keys=False)
            with open(request.session["directory"] + "/group_vars/" + name + "/batches.yml", "w") as f:
                yaml.dump({batches_key: new_group[batches_key]}, f, indent=2, sort_keys=False)
            group_add(name, request)
            request.session["groups"].append(new_group)
            for host in new_group["nodes"]:

                hosts_add(host, name, request)

        elif action == "edit":
            oldname = request.session["groups"][node_id]["name"]

            os.rename(request.session["directory"] + "/group_vars/" +
                      oldname, request.session["directory"] + "/group_vars/" + name)
            with open(request.session["directory"] + "/group_vars/" + name + "/meta.yml", "w") as f:
                yaml.dump({meta_key: new_group[meta_key]}, f, indent=2, sort_keys=False)
            with open(request.session["directory"] + "/group_vars/" + name + "/batches.yml", "w") as f:
                yaml.dump({batches_key: new_group[batches_key]}, f, indent=2, sort_keys=False)
            group_edit(oldname, name, nodes, request)
            request.session["groups"][node_id] = new_group

        elif action == "delete":
            shutil.rmtree(
                request.session["directory"] + "/group_vars/" + name)
            group_remove(name, request)

            i = 0
            # lowkey im reading this like weeks after writing this what even is this
            while i < len(request.session["groups"]):
                if request.session["groups"][i]["id"] == node_id:
                    request.session["groups"].pop(i)
                    continue
                i += 1
            request.session.modified = True
            return JsonResponse({"success": True})

        request.session.modified = True
        print("GROUP")
        print(new_group)
        return JsonResponse(new_group, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_schedule(request, data, action):

    try:
        name = data["name"]
        repeat = data["repeatstring"]
        if data.get("id") is None:
            data["id"] = len(request.session["schedules"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/schedules.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["schedules"]
        if action == "add":
            for i in request.session["schedules"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["schedules"].append(data)
            # yamlfile[name] = {"repeat": repeat}
            yamlfile.append({"name": name, "repeat": repeat})
        elif action == "edit":
            # yamlfile.pop(request.session["schedules"][node_id]["name"])
            # yamlfile[name] = {"repeat": repeat}
            # print(request.session["schedules"][node_id]["name"])
            replaceByKeyVal(yamlfile, "name", request.session["schedules"][node_id]["name"], {"name": name, "repeat": repeat})
            request.session["schedules"][node_id] = data
        elif action == "delete":
            removeByKeyVal(yamlfile, "name", name)
            request.session["schedules"].pop(node_id)
            # yamlfile.pop(name, None)
        with open(request.session["directory"] + "/group_vars/all/schedules.yml", "w") as f:
            yaml.dump({"schedules": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_bssid_channel(request, data, action):

    try:
        name = data["name"]
        channels = data["channels"]
        if data.get("id") is None:
            data["id"] = len(request.session["bssid_channels"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/bssid_channels.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["bssid_channels"]
        if action == "add":
            for i in request.session["bssid_channels"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["bssid_channels"].append(data)
            # yamlfile[name] = channels
            yamlfile.append({"name": name, "channels": channels})
        elif action == "edit":
            # yamlfile.pop(request.session["bssid_channels"][node_id]["name"])
            # yamlfile[name] = channels
            replaceByKeyVal(yamlfile, "name", request.session["bssid_channels"][node_id]["name"], {"name": name, "channels": channels})
            request.session["bssid_channels"][node_id] = data
        elif action == "delete":
            request.session["bssid_channels"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/bssid_channels.yml", "w") as f:
            yaml.dump({"bssid_channels": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_network_interface(request, data, action):

    try:
        name = data["name"]
        interface = data["interface"]
        if data.get("id") is None:
            data["id"] = len(request.session["network_interfaces"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/network_interfaces.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["network_interfaces"]
        if action == "add":
            for i in request.session["network_interfaces"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["network_interfaces"].append(data)
            # yamlfile[name] = interface
            yamlfile.append({"name": name, "interface": interface})
            
        elif action == "edit":
            # yamlfile.pop(request.session["network_interfaces"][node_id]["name"])
            # yamlfile[name] = interface
            replaceByKeyVal(yamlfile, "name", request.session["network_interfaces"][node_id]["name"], {"name": name, "interface": interface})
            request.session["network_interfaces"][node_id] = data
        elif action == "delete":
            request.session["network_interfaces"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/network_interfaces.yml", "w") as f:
            yaml.dump({"network_interfaces": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_ssid_profile(request, data, action):

    try:
        name = data["name"]
        dataout = copy(data)
        dataout.pop("id", None)
        # dataout.pop("name")
        if data.get("id") is None:
            data["id"] = len(request.session["ssid_profiles"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/ssid_profiles.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["ssid_profiles"]
        if action == "add":
            for i in request.session["ssid_profiles"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["ssid_profiles"].append(data)
            # yamlfile[name] = dataout
            yamlfile.append(dataout)
        elif action == "edit":
            # yamlfile.pop(request.session["ssid_profiles"][node_id]["name"])
            # yamlfile[name] = dataout
            replaceByKeyVal(yamlfile, "name", request.session["ssid_profiles"][node_id]["name"], dataout)
            request.session["ssid_profiles"][node_id] = data
        elif action == "delete":
            request.session["ssid_profiles"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/ssid_profiles.yml", "w") as f:
            yaml.dump({"ssid_profiles": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_ssid_group(request, data, action):

    try:
        name = data["name"]
        # nodes = [request.session["ssid_profiles"][i]["name"] for i in data["nodes"]]
        nodes = data["nodes"]
        if data.get("id") is None:
            data["id"] = len(request.session["ssid_groups"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/ssid_groups.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["ssid_groups"]
        if action == "add":
            for i in request.session["ssid_groups"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["ssid_groups"].append(data)
            yamlfile.append({"name": name, "nodes": nodes})
        elif action == "edit":
            # yamlfile.pop(request.session["ssid_groups"][node_id]["name"])
            # yamlfile[name] = nodes
            replaceByKeyVal(yamlfile, "name", request.session["ssid_groups"][node_id]["name"], {"name": name, "profiles": nodes})
            request.session["ssid_groups"][node_id] = data
        elif action == "delete":
            request.session["ssid_groups"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/ssid_groups.yml", "w") as f:
            yaml.dump({"ssid_groups": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_bssid_scan(request, data, action):

    try:
        name = data["name"]
        dataout = copy(data)
        print(dataout)
        dataout.pop("id", None)
        # dataout.pop("name")
        if data.get("id") is None:
            data["id"] = len(request.session["bssid_scans"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/bssid_scans.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["bssid_scans"]
        if action == "add":
            for i in request.session["bssid_scans"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["bssid_scans"].append(data)
            # yamlfile[name] = dataout
            yamlfile.append(dataout)
        elif action == "edit":
            # yamlfile.pop(request.session["bssid_scans"][node_id]["name"])
            # yamlfile[name] = dataout
            replaceByKeyVal(yamlfile, "name", request.session["bssid_scans"][node_id]["name"], dataout)
            request.session["bssid_scans"][node_id] = data
        elif action == "delete":
            request.session["bssid_scans"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/bssid_scans.yml", "w") as f:
            yaml.dump({"bssid_scans": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def get_absolute_inventory_path(inventory_name):
    absolute_path = INVENTORIES_DIRECTORY.joinpath(Path(inventory_name))
    # verify the submitted path didn't escape our inventories directory
    if absolute_path.parent != INVENTORIES_DIRECTORY:
        raise PermissionDenied("Invalid inventory path submitted")
    
    return absolute_path

def submit_inventory(request, data, action):

    # deletes are not permitted
    if action == "delete":
        return HttpResponse(status="405") # Method Not Allowed

    submitted_path = get_absolute_inventory_path(data["name"])

    # generate missing attributes
    if data.get("id") is None:
        data["id"] = len(request.session["directories"])
    node_id = data.get("id")

    # if it already exists, don't overwrite
    if submitted_path.exists():
        return HttpResponse(status="409") # Conflict

    # edit is essentially a rename
    if action == "edit":
        inventory_to_rename = get_absolute_inventory_path(request.session["directories"][node_id]["name"])

        if inventory_to_rename.exists():
            inventory_to_rename.rename(submitted_path)
            request.session["directories"][node_id] = data
            request.session.modified = True
            return JsonResponse(data, safe=False)
    # if it doesn't exist, just continue to the add routine

    # not edit, not delete, so this is an add
    shutil.copytree(str(DEFAULT_INVENTORY), str(submitted_path))
    request.session["directories"].append(data)
    request.session.modified = True
    return JsonResponse(data, safe=False)


def submit_batch(request, data, action):

    name = data["name"]
    dataout = copy(data)
    if "id" in dataout:
        dataout.pop("id", None)
    # dataout.pop("name")
    if data.get("id") is None:
        data["id"] = len(request.session["batches"])
    node_id = data.get("id")

    # add the batch to the global batch_definitions
    with open(request.session["directory"] + "/group_vars/all/batch_definitions.yml") as batch_defs_file:
        batch_defs_yml = yaml.load(batch_defs_file, Loader=SafeLoader)
        batch_defs_yml = batch_defs_yml["batches"]
        if action == "add":
            for i in request.session["batches"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            # add the batch to django session and ansible yaml
            request.session["batches"].append(dataout)
            batch_defs_yml.append(dataout)
        elif action == "edit":
            new_name = dataout["name"]
            old_name = request.session["batches"][node_id]["name"]

            # update the batch in the django session
            replaceByKeyVal(batch_defs_yml, "name", old_name, dataout)
            
            hostvardir = request.session["directory"] + \
                "/host_vars/"
            groupvardir = request.session["directory"] + \
                "/group_vars/"
            
            # update the batches listed in the host_vars
            for directory in os.listdir(hostvardir):
                with open(hostvardir + directory + "/pssid_conf.yml", "r") as hosts_yml_file:
                    hosts_yml = yaml.load(hosts_yml_file, Loader=SafeLoader)

                    try:
                        hosts_yml["host_batches"].remove(old_name)
                        hosts_yml["host_batches"].append(new_name)
                    except ValueError: pass

                with open(hostvardir + directory + "/pssid_conf.yml", "w") as hosts_yml_file:
                    yaml.dump(hosts_yml, hosts_yml_file, indent=2,
                                sort_keys=False)
            
            # update the batches listed in groups
            for directory in [i["name"] for i in request.session["groups"]]:
                with open(groupvardir + directory + "/batches.yml", "r") as groups_yml_file:
                    groups_yml = yaml.load(groups_yml_file, Loader=SafeLoader)
                    batches_key = f"{directory}_batches"

                    try:
                        groups_yml[batches_key].remove(old_name)
                        groups_yml[batches_key].append(new_name)
                    except ValueError: pass

                with open(groupvardir + directory + "/batches.yml", "w") as groups_yml_file:
                    yaml.dump(groups_yml, groups_yml_file, indent=2,
                                sort_keys=False)

            request.session["batches"][node_id] = data

        elif action == "delete":
            request.session["batches"].pop(node_id)

            removeByKeyVal(batch_defs_yml, "name", name)
            hostvardir = request.session["directory"] + \
                "/host_vars/"
            groupvardir = request.session["directory"] + \
                "/group_vars/"

            # remove from host_vars
            for directory in os.listdir(hostvardir):
                with open(hostvardir + directory + "/pssid_conf.yml", "r") as hosts_yml_file:

                    hosts_yml = yaml.load(hosts_yml_file, Loader=SafeLoader)

                    try: hosts_yml["host_batches"].remove(name)
                    except ValueError: pass # fine if not present

                with open(hostvardir + directory + "/pssid_conf.yml", "w") as hosts_yml_file:
                    yaml.dump(hosts_yml, hosts_yml_file, indent=2,
                                sort_keys=False)

            # remove from group_vars
            for directory in os.listdir(groupvardir):
                with open(groupvardir + directory + "/batches.yml", "r") as groups_yml_file:
                    batches_key = f"{directory}_batches"

                    groups_yml = yaml.load(groups_yml_file, Loader=SafeLoader)

                    try: groups_yml[batches_key].remove(name)
                    except ValueError: pass # fine if not present
                
                with open(groupvardir + directory + "/batches.yml", "w") as groups_yml_file:
                    yaml.dump(groups_yml, groups_yml_file, indent=2,
                                sort_keys=False)

        with open(request.session["directory"] + "/group_vars/all/batch_definitions.yml", "w") as batch_defs_file:
            yaml.dump({"batches": batch_defs_yml}, batch_defs_file, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)


def submit_job(request, data, action):
    if data.get("id") is None:
        data["id"] = len(request.session["jobs"])

    with open(request.session["directory"] + "/group_vars/all/jobs.yml", "r") as f:
        jobs = yaml.load(f, Loader=SafeLoader)
    jobs = jobs["jobs"]

    if action == "edit" or action == "delete":
        # remove any that already exists with this name
        jobs = [job for job in jobs if job["id"] != data["id"]]
        request.session["jobs"] \
            = [job for job in request.session["jobs"] if job["id"] != data["id"]]
    
    if action == "edit" or action == "add":
        # add this job in as long as it doesn't already exist
        if any(job["name"] == data["name"] for job in jobs) \
            or any(job["name"] == data["name"] for job in request.session["jobs"]):
            return HttpResponse(status="403")

        request.session["jobs"].append(data)
        jobs.append(data)

    with open(request.session["directory"] + "/group_vars/all/jobs.yml", "w") as f:
        yaml.dump({"jobs": jobs}, f, indent=2, sort_keys=False)
    return JsonResponse(data, safe=False)

def submit_test(request, data, action):

    try:
        name = data["name"]
        dataout = copy(data)
        if "id" in dataout:
            dataout.pop("id", None)
        dataout["extra"] = []
        if "spec" not in dataout:
            dataout["spec"] = {}
        for i in dataout["meta"]:
            key = list(i.keys())[0]
            val = list(i.values())[0]
            dataout["extra"].append(key)
            dataout["spec"][key] = val
        dataout.pop("meta", None)
        # dataout.pop("meta", None)
        # dataout.pop("name")
        print(name)
        if data.get("id") is None:
            data["id"] = len(request.session["tests"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/tests.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["tests"]
        if action == "add":
            for i in request.session["tests"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["tests"].append(data)
            # yamlfile[name] = dataout
            yamlfile.append(dataout)
        elif action == "edit":
            # yamlfile.pop(request.session["tests"][node_id]["name"])
            # yamlfile[name] = dataout
            replaceByKeyVal(yamlfile, "name", request.session["tests"][node_id]["name"], dataout)
            request.session["tests"][node_id] = data
        elif action == "delete":
            request.session["tests"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/tests.yml", "w") as f:
            yaml.dump({"tests": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())

def submit_archiver(request, data, action):

    try:
        name = data["name"]
        dataout = copy(data)
        if "id" in dataout:
            dataout.pop("id", None)
        dataout["extra"] = []
        if "spec" not in dataout:
            dataout["spec"] = {}
        for i in dataout["meta"]:
            key = list(i.keys())[0]
            val = list(i.values())[0]
            dataout["extra"].append(key)
            dataout["spec"][key] = val
        dataout.pop("meta", None)
        # dataout.pop("meta", None)
        # dataout.pop("name")
        if data.get("id") is None:
            data["id"] = len(request.session["archivers"])
        node_id = data.get("id")
        with open(request.session["directory"] + "/group_vars/all/archivers.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["archivers"]
        if action == "add":
            for i in request.session["archivers"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            request.session["archivers"].append(data)
            # yamlfile[name] = dataout
            yamlfile.append(dataout)
        elif action == "edit":
            # yamlfile.pop(request.session["archivers"][node_id]["name"])
            # yamlfile[name] = dataout
            replaceByKeyVal(yamlfile, "name", request.session["archivers"][node_id]["name"], dataout)
            request.session["archivers"][node_id] = data
        elif action == "delete":
            request.session["archivers"].pop(node_id)
            # yamlfile.pop(name, None)
            removeByKeyVal(yamlfile, "name", name)
        with open(request.session["directory"] + "/group_vars/all/archivers.yml", "w") as f:
            yaml.dump({"archivers": yamlfile}, f, indent=2, sort_keys=False)
        request.session.modified = True
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def get_inventories(request, token):
    # returns JSON suitable for GET /init/ endpoint,
    # also resyncs the inventories on disk with Django's,
    # state: request.session["directories"]

    request.session["directories"] = []

    for index, inventory in enumerate(INVENTORIES_DIRECTORY.iterdir()):
        request.session["directories"].append({
            "name": inventory.name,
            "id": index
        })

    return JsonResponse({
        "directories": request.session["directories"],
        "token": token
    }, safe=False)


def init(request):
    token = get_token(request)

    # if the directory query param is absent, we should return all
    # inventories present
    if request.GET.get("directory", None) is None:
        return get_inventories(request, token)

    return get_inventory(request, token)


def get_inventory(request, token):

    request.session["directory"] = str(get_absolute_inventory_path(request.GET.get("directory")))

    node_id = 0
    batch_id = 0
    test_id = 0
    hosts = []
    groups = []
    schedules = []
    bssid_channels = []
    ssid_profiles = []
    ssid_groups = []
    network_interfaces = []
    bssid_scans = []
    archivers = []
    tests = []
    batches = []
    testnames = []
    archivernames = []

    with open(request.session["directory"] + "/hosts.yml", "r") as f:
        hosts_yml = yaml.safe_load(f)
        group_id = 0
        
        # gather the global batches into the response
        with open(request.session["directory"] + "/group_vars/all/batch_definitions.yml", "r") as f:
            batch_defs_yml = yaml.load(f, Loader=SafeLoader)
            batches = batch_defs_yml["batches"]
            for i, batch in enumerate(batches):
                batch["id"] = i

        for group, group_content in hosts_yml.items():

            currentgroup = group

            with open(request.session["directory"] + "/group_vars/" + currentgroup + "/meta.yml", "r") as f:
                group_meta_yml = yaml.load(f, Loader=SafeLoader)
                meta_key = f"{group}_meta"
                meta = group_meta_yml[meta_key]
            with open(request.session["directory"] + "/group_vars/" + currentgroup + "/batches.yml", "r") as f:
                group_batches_yml = yaml.load(f, Loader=SafeLoader)
                batches_key = f"{group}_batches"
                new_batches = group_batches_yml[batches_key]
            groups.append(
                {"name": currentgroup, "nodes": [], "id": group_id, "meta": meta, "batches": new_batches})

            Path(request.session["directory"] + "/group_vars/" + currentgroup).mkdir(parents=True,exist_ok=True)

            group_id += 1

            if group_content["hosts"] is None:
                hosts_entry = {}
            else:
                hosts_entry = group_content["hosts"]

            for host in hosts_entry:
                ip = host

                with open(request.session["directory"] + "/host_vars/"
                            + ip + "/pssid_conf.yml", "r") as f:
                    f.seek(0)
                    new_node = {}

                    new_node = yaml.load(f, Loader=SafeLoader)
                    new_node["id"] = node_id
                    new_node["batches"] = new_node.pop("host_batches")

                    test_id += 1
                    
                    with open(request.session["directory"] + "/host_vars/"
                            + ip + "/meta.yml", "r") as f2:
                        meta = yaml.load(f2, Loader=SafeLoader)
                        new_node["meta"] = meta["host_meta"]

                    # this is to avoid adding the same host from two different groups
                    # to the same host list multiple times
                    if all(host_candidate["name"] != new_node["name"] for host_candidate in hosts):
                        hosts.append(new_node)

                groups[-1]["nodes"].append(host)
                node_id += 1

    with open(request.session["directory"] + "/group_vars/all/schedules.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = [{"id": index, "name": i["name"],
                     "repeatstring": i["repeat"],
                     "repeat": dict(zip(["minute", "hour", "day", "month", "year"],
                                        i["repeat"].split(" ")))}
                    for index, i in enumerate(yamlfile["schedules"])]
        # shh dont tell anyone

        schedules = yamlfile
    with open(request.session["directory"] + "/group_vars/all/bssid_channels.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'

        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["bssid_channels"]
        for index, i in enumerate(yamlfile):
            i["id"] = index

        bssid_channels = yamlfile

    with open(request.session["directory"] + "/group_vars/all/ssid_profiles.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["ssid_profiles"]

        for index, i in enumerate(yamlfile):
            i["id"] = index

        # yamlfile = [{**{"id": index, "name": list(i.keys())[0]}, **list(i.values())[
        #     0]} for index, i in enumerate(yamlfile)]
        # for i in yamlfile:
        #     for channel in bssid_channels:
        #         if channel["name"] == i["channels"]:
        #             i["channels"] = channel["id"]

        ssid_profiles = yamlfile

    with open(request.session["directory"] + "/group_vars/all/ssid_groups.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["ssid_groups"]

        for index, i in enumerate(yamlfile):
            i["id"] = index

        ssid_groups = yamlfile

    with open(request.session["directory"] + "/group_vars/all/network_interfaces.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["network_interfaces"]

        for index, i in enumerate(yamlfile):
            i["id"] = index

        # yamlfile = [{"id": index, "name": list(i.keys())[0], "interface": list(
        #     i.values())[0]} for index, i in enumerate(yamlfile)]

        network_interfaces = yamlfile

    with open(request.session["directory"] + "/group_vars/all/bssid_scans.yml") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["bssid_scans"]

        for index, i in enumerate(yamlfile):
            i["id"] = index

        # yamlfile = [{**{"id": index, "name": list(i.keys())[0]}, **list(i.values())[
        #     0]} for index, i in enumerate(yamlfile)]

        bssid_scans = yamlfile

    # this adds the inventories to `request.session["directories"]`
    get_inventories(request, token)

    with open(request.session["directory"] + "/group_vars/all/jobs.yml", "r") as f:
        jobs = yaml.load(f, Loader=SafeLoader)["jobs"]

    with open(request.session["directory"] + "/group_vars/all/tests.yml", "r") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["tests"]

        for index, i in enumerate(yamlfile):
            i["id"] = index
            i["meta"] = []
            for extrakey in i["extra"]:
                i["meta"].append({extrakey: i["spec"][extrakey]})
                i["spec"].pop(extrakey, None)
                
            # i["meta"] = []
        # yamlfile = [{**{"id": index, "name": list(i.keys())[0]}, **list(i.values())[
        #     0]} for index, i in enumerate(yamlfile)]

        tests = yamlfile
    with open(request.session["directory"] + "/group_vars/all/archivers.yml", "r") as f:
        f.seek(0)
        fileread = f.read()
        # fileread = '[' + fileread[1:-1] + ']'
        yamlfile = yaml.load(fileread, Loader=SafeLoader)

        yamlfile = yamlfile["archivers"]

        for index, i in enumerate(yamlfile):
            i["id"] = index
            i["meta"] = []
            for extrakey in i["extra"]:
                i["meta"].append({extrakey: i["spec"][extrakey]})
                i["spec"].pop(extrakey, None)

        archivers = yamlfile

    with open(request.session["directory"] + "/group_vars/all/testnames.yml", "r") as f:
        testnames = (yaml.load(f, Loader=SafeLoader))["testnames"]

    with open(request.session["directory"] + "/group_vars/all/archivernames.yml", "r") as f:
        archivernames = (yaml.load(f, Loader=SafeLoader))["archivernames"]

    request.session["hosts"] = hosts
    request.session["groups"] = groups
    request.session["schedules"] = schedules
    request.session["bssid_channels"] = bssid_channels
    request.session["ssid_profiles"] = ssid_profiles
    request.session["ssid_groups"] = ssid_groups
    request.session["network_interfaces"] = network_interfaces
    request.session["bssid_scans"] = bssid_scans
    request.session["archivers"] = archivers
    request.session["jobs"] = jobs
    request.session["tests"] = tests
    request.session["batches"] = batches
    request.session["testnames"] = testnames
    request.session["archivernames"] = archivernames

    request.session.modified = True

    return JsonResponse({
        "hosts": hosts,
        "groups": groups,
        "schedules": schedules,
        "bssid_channels": bssid_channels,
        "ssid_profiles": ssid_profiles,
        "ssid_groups": ssid_groups,
        "network_interfaces": network_interfaces,
        "bssid_scans": bssid_scans,
        "archivers": archivers,
        "tests": tests,
        "jobs": jobs,
        "batches": batches,
        "directories": request.session["directories"],
        "testnames": testnames,
        "archivernames": archivernames,
        "token": token
    }, safe=False)


def submit(request):

    response = yaml.load(request.body, Loader=SafeLoader)
    print(response)
    tab = response["tab"]
    data = response["data"]
    action = response["action"]

    if tab == "host":
        return submit_host(request, data, action)
    if tab == "group":
        return submit_group(request, data, action)
    if tab == "schedule":
        return submit_schedule(request, data, action)
    if tab == "bssid_channel":
        return submit_bssid_channel(request, data, action)
    if tab == "ssid_profile":
        return submit_ssid_profile(request, data, action)
    if tab == "ssid_group":
        return submit_ssid_group(request, data, action)
    if tab == "network_interface":
        return submit_network_interface(request, data, action)
    if tab == "bssid_scan":
        return submit_bssid_scan(request, data, action)
    elif tab == "archiver":
        return submit_archiver(request, data, action)
    if tab == "test":
        return submit_test(request, data, action)
    if tab == "job":
        return submit_job(request, data, action)
    if tab == "batch":
        return submit_batch(request, data, action)
    if tab == "directory":
        return submit_inventory(request, data, action)
    print(tab)
    return False


def index(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    template = loader.get_template("index.html")

    context = {

    }
    return HttpResponse(template.render(context, request))
