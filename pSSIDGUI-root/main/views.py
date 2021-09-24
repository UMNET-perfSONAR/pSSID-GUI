'''
Main Backend File
'''

from copy import deepcopy as copy  # forgive me for my sins
import os
import shutil
import traceback


from django.http import HttpResponse
from django.http.response import JsonResponse
from django.template import loader
from django.middleware.csrf import get_token
import requests
from urllib3.exceptions import InsecureRequestWarning
import yaml
from yaml.loader import SafeLoader


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

def hosts_add(ip, group, request):
    # add a host to hosts.ini
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)
        contents = f.readlines()
        contents.insert(contents.index("[" + group + "]\n") + 1, ip + "\n")

    with open(request.session["directory"] + "/hosts", "w") as f:
        f.seek(0)
        f.write("".join(contents))


def hosts_remove(ip, request):
    # remove a host from hosts.ini
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)
        count = 0
        contents = f.readlines()
        for line in contents:
            if line == ip + "\n":
                contents.pop(count)
            count += 1

    with open(request.session["directory"] + "/hosts", "w") as f:
        f.seek(0)
        f.write("".join(contents))


def hosts_edit(oldip, newip, request):
    # edit the name of a host in hosts.ini
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)
        count = 0
        contents = f.readlines()
        for line in contents:
            if line == oldip + "\n":
                contents[count] = newip + "\n"
                continue
            count += 1

    with open(request.session["directory"] + "/hosts", "w") as f:
        f.seek(0)
        f.write("".join(contents))


def group_add(group, request):
    # add a group to hosts.ini
    with open(request.session["directory"] + "/hosts", "a") as f:
        f.write("\n[" + group + "]\n")


def group_remove(group, request):
    # remove a group from hosts.ini
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)

        contents = f.readlines()
        start = contents.index("[" + group + "]\n")

        while start < len(contents) and contents[start] != "\n":

            contents.pop(start)

        # extra \n vvv
        if start != len(contents):
            contents.pop(start)
        else:
            contents.pop(start-1)

    with open(request.session["directory"] + "/hosts", "w") as f:
        f.seek(0)
        f.write("".join(contents))


def group_edit(oldgroup, new_group, hosts, request):
    # edit the name of a group from hosts.ini
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)
        contents = f.readlines()
        start = contents.index("[" + oldgroup + "]\n")
        contents[start] = "[" + new_group + "]\n"
        start += 1
        for host in hosts:
            if start == len(contents) or contents[start] == "\n":
                contents.insert(start, host + "\n")
            else:
                contents[start] = host + "\n"
            start += 1
        while start < len(contents) and contents[start] != "\n":
            contents.pop(start)
    with open(request.session["directory"] + "/hosts", "w") as f:
        f.seek(0)
        f.write("".join(contents))


def make_node(name, ip, meta, node_id):
    # construct a host from arguments, pings pscheduler to check if a host is online
    # (yes i know it says node im sorry)
    try:
        response = requests.get("https://" + ip + "/pscheduler", verify=False)

        if response.ok:
            tests = requests.get(
                "https://" + ip + "/pscheduler/tests", verify=False).json()
            archivers = requests.get(
                "https://" + ip + "/pscheduler/archivers", verify=False).json()
            new_node = {"name": name, "ip": ip, "meta": meta, "status": bootstrap_bg(
                True), "id": node_id, "tests": tests, "archivers": archivers, "tasks": []}
            # i tried really hard to make this a class but django disagreed please forgive me
        else:
            new_node = {"name": name, "ip": ip, "meta": meta, "status": bootstrap_bg(
                False), "id": node_id, "tests": [], "archivers": [], "tasks": []}
        return new_node
    except Exception:
        new_node = {"name": name, "ip": ip, "meta": meta, "status": bootstrap_bg(
            False), "id": node_id, "tests": [], "archivers": [], "tasks": []}
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
    meta = response["meta"]
    tasks = response["tasks"]
    try:

        new_node = make_node(name, ip, meta, node_id)
        new_node.pop("meta")
        # new_node["tasks"] = tasks
        # new_node["tasks"] = dict(zip([i for i in tasks], [
        #     {i: d[i] for i in d if i != "name"} for d in
        #     request.session["tasks"] if d["name"] in tasks]))
        new_node["tasks"] = [{i:d[i] for i in d if i!='id'} for d in request.session["tasks"] if d["name"] in data["tasks"]]
        
        if action == "add":
            for i in request.session["hosts"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            os.mkdir(request.session["directory"] + "/host_vars/" + ip)
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
            yaml.dump({"meta": meta}, f, indent=2, sort_keys=False)

        request.session.modified = True
        new_node["tasks"] = tasks
        return JsonResponse(new_node, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


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
    tasks = response["tasks"]
    if not set(nodes).issubset(set(i["ip"] for i in request.session["hosts"])):
        # security check i guess? this is kinda stupid idk why i included it
        return HttpResponse(status="403")
    new_group = {"name": name, "nodes": nodes, "meta": meta, "id": node_id, "tasks": tasks}
    try:

        if action == "add":
            for i in request.session["groups"]:
                if i["name"] == name:
                    return HttpResponse(status="503")
            os.mkdir(request.session["directory"] + "/group_vars/" + name)
            # new_tasks = dict(zip([i for i in data["tasks"]], [
            #     {i: d[i] for i in d if i != "name"} for d in
            #     request.session["tasks"] if d["name"] in data["tasks"]]))
            new_tasks = [{i:d[i] for i in d if i!='id'} for d in request.session["tasks"] if d["name"] in data["tasks"]]

            with open(request.session["directory"] + "/group_vars/" + name + "/meta.yml", "w") as f:
                yaml.dump({"meta": new_group["meta"]}, f, indent=2, sort_keys=False)
            with open(request.session["directory"] + "/group_vars/" + name + "/tasks.yml", "w") as f:

                yaml.dump({"tasks": new_tasks}, f, indent=2, sort_keys=False)
            group_add(name, request)
            request.session["groups"].append(new_group)
            for host in new_group["nodes"]:

                hosts_add(host, name, request)

        elif action == "edit":
            oldname = request.session["groups"][node_id]["name"]
            # new_tasks = dict(zip([i for i in data["tasks"]], [
            #     {i: d[i] for i in d if i != "name"} for d in
            #     request.session["tasks"] if d["name"] in data["tasks"]]))
            new_tasks = [{i:d[i] for i in d if i!='id'} for d in request.session["tasks"] if d["name"] in data["tasks"]]



            os.rename(request.session["directory"] + "/group_vars/" +
                      oldname, request.session["directory"] + "/group_vars/" + name)
            with open(request.session["directory"] + "/group_vars/" + name + "/meta.yml", "w") as f:
                yaml.dump({"meta": new_group["meta"]}, f, indent=2, sort_keys=False)
            with open(request.session["directory"] + "/group_vars/" + name + "/tasks.yml", "w") as f:

                yaml.dump({"tasks": new_tasks}, f, indent=2, sort_keys=False)
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


def submit_directory(request, data, action):

    try:
        path = data["path"]
        if data.get("id") is None:
            data["id"] = len(request.session["directories"])
        node_id = data.get("id")
        created = False
        if os.path.isdir(path):
            dir = os.listdir(path)
            if len(dir) == 0:
                os.mkdir(path + "/host_vars")
                os.mkdir(path + "/group_vars")
                os.mkdir(path + "/group_vars/all")
                with open(path + "/hosts", 'w') as f:
                    f.write("[all]\n")
                with open(path + "/group_vars/all/archivernames.yml", 'w') as f:
                    yaml.dump([], f)
                with open(path + "/group_vars/all/archivers.yml", 'w') as f:
                    yaml.dump({"archivers": []}, f)
                with open(path + "/group_vars/all/bssid_channels.yml", 'w') as f:
                    yaml.dump({"bssid_channels": []}, f)
                with open(path + "/group_vars/all/bssid_scans.yml", 'w') as f:
                    yaml.dump({"bssid_scans": []}, f)
                with open(path + "/group_vars/all/meta.yml", 'w') as f:
                    yaml.dump({"meta": []}, f)
                with open(path + "/group_vars/all/network_interfaces.yml", 'w') as f:
                    yaml.dump({"network_interfaces": []}, f)
                with open(path + "/group_vars/all/schedules.yml", 'w') as f:
                    yaml.dump({"schedules": []}, f)
                with open(path + "/group_vars/all/ssid_groups.yml", 'w') as f:
                    yaml.dump({"ssid_groups": []}, f)
                with open(path + "/group_vars/all/ssid_profiles.yml", 'w') as f:
                    yaml.dump({"ssid_profiles": []}, f)
                with open(path + "/group_vars/all/task_list.yml", 'w') as f:
                    yaml.dump({"task_list": []}, f)
                with open(path + "/group_vars/all/tasks.yml", 'w') as f:
                    yaml.dump({"tasks": []}, f)
                with open(path + "/group_vars/all/testnames.yml", 'w') as f:
                    yaml.dump([], f)
                with open(path + "/group_vars/all/tests.yml", 'w') as f:
                    yaml.dump({"tests": []}, f)
                created = True
            data["created"] = created
            if action == "add":
                request.session["directories"].append(data)
            elif action == "edit":
                request.session["directories"][node_id] = data
            elif action == "delete":
                request.session["directories"].pop(node_id)
            request.session.modified = True
            print(data)
            return JsonResponse(data, safe=False)
        return HttpResponse(status="403")
    except Exception as e:
        print(e)
        print(traceback.format_exc())


def submit_task(request, data, action):

    try:
        name = data["name"]
        dataout = copy(data)
        if "id" in dataout:
            dataout.pop("id", None)
        # dataout.pop("name")
        if data.get("id") is None:
            data["id"] = len(request.session["tasks"])
        node_id = data.get("id")
        print(request.session["tasks"][node_id])
        with open(request.session["directory"] + "/group_vars/all/task_list.yml") as f:
            yamlfile = yaml.load(f, Loader=SafeLoader)
            yamlfile = yamlfile["tasks"]
            if action == "add":
                for i in request.session["tasks"]:
                    if i["name"] == name:
                        return HttpResponse(status="503")
                request.session["tasks"].append(data)
                # yamlfile[name] = dataout
                yamlfile.append(dataout)
            elif action == "edit":
                # yamlfile.pop(request.session["tasks"][node_id]["name"])
                # yamlfile[name] = dataout
                print(request.session["tasks"][node_id]["name"])
                print("test")
                print(yamlfile)
                replaceByKeyVal(yamlfile, "name", request.session["tasks"][node_id]["name"], dataout)
                print(yamlfile)
                
                try:
                    hostvardir = request.session["directory"] + \
                        "/host_vars/"
                    groupvardir = request.session["directory"] + \
                        "/group_vars/"
                    for directory in os.listdir(hostvardir):
                        with open(hostvardir + directory + "/pssid_conf.yml", "r+") as f2:
                            yamlfile2 = yaml.load(f2, Loader=SafeLoader)

                            yamlfile2["tasks"] = [data if task["name"] == request.session["tasks"][node_id]["name"] else task for task in yamlfile2["tasks"]]
                            print(yamlfile2["tasks"])
                            # for task in tasks:
                            #     if task["name"] == name:
                            #         task = data

                                    
                            f2.seek(0)
                            yaml.dump(yamlfile2, f2, indent=2,
                                      sort_keys=False)
                    
                    # for directory in os.listdir(groupvardir):
                    for directory in [i["name"] for i in request.session["groups"]]:
                        with open(groupvardir + directory + "/tasks.yml", "r+") as f2:
                            yamlfile2 = yaml.load(f2, Loader=SafeLoader)
                            # for task in yamlfile2["tasks"]:
                            #     if task["name"] == name:
                            #         task = data
                            print("groups")
                            print(yamlfile2)
                            yamlfile2["tasks"] = [data if task["name"] == request.session["tasks"][node_id]["name"] else task for task in yamlfile2["tasks"]]
                            print(yamlfile2)
                            f2.seek(0)
                            yaml.dump(yamlfile2, f2, indent=2,
                                      sort_keys=False)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())
                request.session["tasks"][node_id] = data

            elif action == "delete":
                request.session["tasks"].pop(node_id)
                # yamlfile.pop(name, None)
                removeByKeyVal(yamlfile, "name", name)
                try:
                    hostvardir = request.session["directory"] + \
                        "/host_vars/"
                    groupvardir = request.session["directory"] + \
                        "/group_vars/"
                    for directory in os.listdir(hostvardir):
                        with open(hostvardir + directory + "/pssid_conf.yml", "r") as f2:

                            yamlfile2 = yaml.load(f2, Loader=SafeLoader)

                            for task in yamlfile2["tasks"]:

                                if task == name:
                                    yamlfile2["tasks"].pop(task)
                                    break
                        with open(hostvardir + directory + "/pssid_conf.yml", "w") as f2:
                            yaml.dump(yamlfile2, f2, indent=2,
                                      sort_keys=False)
                    for directory in os.listdir(groupvardir):
                        with open(groupvardir + directory + "/tasks.yml", "r") as f2:
                            yamlfile2 = yaml.load(f2, Loader=SafeLoader)
                            for task in yamlfile2["tasks"]:
                                if task == name:
                                    yamlfile2["tasks"].pop(task)
                                    break
                        with open(groupvardir + directory + "/tasks.yml", "w") as f2:
                            yaml.dump(yamlfile2, f2, indent=2,
                                      sort_keys=False)
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())

            with open(request.session["directory"] + "/group_vars/all/task_list.yml", "w") as f:
                yaml.dump({"tasks": yamlfile}, f, indent=2, sort_keys=False)
            request.session.modified = True
            print(data)
            return JsonResponse(data, safe=False)
    except Exception as e:
        print(e)
        print(traceback.format_exc())


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

def init(request):
    token = get_token(request)
    if request.GET.get("directory", None) is None:
        for i in request.session.get("directories", []):
            i["created"] = False
        request.session["directories"] = [{**i, **{"id": index}} for index, i in enumerate(
            request.session.get("directories", [])) if os.path.isdir(i["path"])]
        return JsonResponse({
            "directories": request.session["directories"],
            "token": token
        }, safe=False)

    

    request.session["directory"] = request.GET.get("directory")

    node_id = 0
    task_id = 0
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
    tasks = []
    testnames = []
    archivernames = []
    with open(request.session["directory"] + "/hosts", "r") as f:
        f.seek(0)
        group_id = 0
        seenset = set()
        for line in f.readlines():
            if line[0] != '#' and ':' not in line and line != "\n":

                if line[0] == '[' and line[-2] == ']':  # if group
                    currentgroup = line[1:-2]


                    with open(request.session["directory"] + "/group_vars/" + currentgroup + "/meta.yml", "r") as f:
                        yamlfile = yaml.load(f, Loader=SafeLoader)
                        meta = yamlfile["meta"]
                    with open(request.session["directory"] + "/group_vars/" + currentgroup + "/tasks.yml", "r") as f:
                        yamlfile = yaml.load(f, Loader=SafeLoader)
                        new_tasks = [i["name"] for i in yamlfile["tasks"]]
                    groups.append(
                        {"name": currentgroup, "nodes": [], "id": group_id, "meta": meta, "tasks": new_tasks})

                    with open(request.session["directory"] + "/group_vars/" + currentgroup + "/tasks.yml", "r") as f:
                        yamlfile = yaml.load(f, Loader=SafeLoader)
                        new_tasks = yamlfile["tasks"]
                        # tasks += [{**{"name": i["name"], "id": task_id}, **
                                    # i} for i in new_tasks if i["name"] not in [j["name"] for j in tasks]]
                        # task_id += 1
                        for i in new_tasks:
                            if i["name"] not in [j["name"] for j in tasks]:
                                tasks.append({**{"id": task_id}, **i})
                                task_id += 1
                    try:
                        os.mkdir(
                            request.session["directory"] + "/group_vars/" + currentgroup)
                    except FileExistsError as e:
                        print(e)
                        print(traceback.format_exc())

                    group_id += 1

                else:  # else host name
                    if line[:-1] in seenset:
                        groups[-1]["nodes"].append(line[:-1])
                    else:
                        ip = line[:-1]
                        try:

                            with open(request.session["directory"] + "/host_vars/"
                                      + ip + "/pssid_conf.yml", "r") as f:
                                f.seek(0)
                                new_node = {}
                                # try:
                                    # new_node = yaml.load(f, Loader=SafeLoader)
                                # except json.decoder.JSONDecodeError:
                                new_node = yaml.load(f, Loader=SafeLoader)
                                new_node["id"] = node_id
                                # tasks += [{**{"name": i, "id": task_id}, **
                                #            i} for i in new_node["tasks"]]
                                # task_id += 1
                                for i in new_node["tasks"]:
                                    if i["name"] not in [j["name"] for j in tasks]:
                                        tasks.append({**{"id": task_id}, **i})
                                        task_id += 1

                                # print(new_node)
                                testnames += [
                                    {"name": i.split("/")[-1]} for i in new_node["tests"]]
                                archivernames += [
                                        {"name": i.split("/")[-1]} for i in new_node["archivers"]]

                                test_id += 1
                                new_node["tasks"] = [i["name"] for i in new_node["tasks"]]
                                
                                with open(request.session["directory"] + "/host_vars/"
                                      + ip + "/meta.yml", "r") as f2:
                                    meta = yaml.load(f2, Loader=SafeLoader)
                                    meta["meta"] = [i for i in meta["meta"] if i is not None]
                                    new_node["meta"] = meta["meta"]
                                    print(new_node)
                                hosts.append(new_node)
                        except Exception as e:
                            print(e)
                            print(traceback.format_exc())

                        seenset.add(line[:-1])
                        # groups[0]["nodes"].append(node_id)
                        groups[-1]["nodes"].append(line[:-1])
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
            i["nodes"] = i.pop("profiles")
        # yamlfile = [{"id": index, "name": list(i.keys())[0], "nodes": list(i.values())[
        #     0]} for index, i in enumerate(yamlfile)]

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

    request.session["directories"] = [{**i, **{"id": index}} for index, i in enumerate(
        request.session.get("directories", [])) if os.path.isdir(i["path"])]

    # with open("rtt.json") as f:
    #     rttjson = yaml.load(f, Loader=SafeLoader)
    #     tests.append({"name": "rtt", "spec": rttjson})

    with open(request.session["directory"] + "/group_vars/all/task_list.yml", "w") as f:
        # yaml.dump(dict(zip([i["name"] for i in tasks], [
        #     {i: d[i] for i in d if i != "name"} for d in tasks])), f, indent=2, sort_keys=False)
        yaml.dump({"tasks": tasks}, f, indent=2, sort_keys=False)
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
                
            # i["meta"] = []
        # yamlfile = [{**{"id": index, "name": list(i.keys())[0]}, **list(i.values())[
        #     0]} for index, i in enumerate(yamlfile)]

        archivers = yamlfile

    with open(request.session["directory"] + "/group_vars/all/testnames.yml", "w") as f:
        yaml.dump(testnames, f, indent=2, sort_keys=False)
    with open(request.session["directory"] + "/group_vars/all/archivernames.yml", "w") as f:
        yaml.dump(archivernames, f, indent=2, sort_keys=False)
    # try:
    #     for directory in os.listdir(hostvardir):
    #         with open(hostvardir + directory + "/pssid_conf.yml") as f:
    #             yamlfile = yaml.load(f, Loader = SafeLoader)
    #             for task in yamlfile["tasks"]:
    #                 tasks.append({**{"name": task}, **yamlfile["tasks"][task]})
    #     for directory in os.listdir(groupvardir):
    #         with open(groupvardir + directory + "/tasks.yml") as f:
    #             yamlfile = yaml.load(f, Loader = SafeLoader)
    #             for task in yamlfile["tasks"]:
    #                 tasks.append({**{"name": task}, **yamlfile["tasks"][task]})
    # except Exception as e:
    #

    request.session["hosts"] = hosts
    request.session["groups"] = groups
    request.session["schedules"] = schedules
    request.session["bssid_channels"] = bssid_channels
    request.session["ssid_profiles"] = ssid_profiles
    request.session["ssid_groups"] = ssid_groups
    request.session["network_interfaces"] = network_interfaces
    request.session["bssid_scans"] = bssid_scans
    request.session["archivers"] = archivers
    request.session["tests"] = tests
    request.session["tasks"] = tasks
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
        "tasks": tasks,
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
    if tab == "task":
        return submit_task(request, data, action)
    if tab == "directory":
        return submit_directory(request, data, action)
    print(tab)
    return False


def index(request):
    if not request.session.exists(request.session.session_key):
        request.session.create()

    template = loader.get_template("index.html")

    context = {

    }
    return HttpResponse(template.render(context, request))
