#!/usr/bin/python3
from flask import Flask, render_template, request
from pymongo import MongoClient
from version import __version__
import json
import os
import random
import sys
import time


def read_configuration():
    global CACHE_STALE_SECONDS, CACHEVIEW_PORT, CACHEVIEW_HOST, FLASK_DEBUG, MONGODB_PORT, MONGODB_HOST

    try:
        configuration_file = "cacheview.cfg"
        variables = {}

        if os.path.isfile(configuration_file):
            with open(configuration_file) as f:
                for line in f:
                    name, value = line.split("=")
                    variables[name] = value.rstrip()

            CACHE_STALE_SECONDS = int(variables["CACHE_STALE_SECONDS"])
            CACHEVIEW_PORT = variables["CACHEVIEW_PORT"]
            CACHEVIEW_HOST = variables["CACHEVIEW_HOST"]
            FLASK_DEBUG = variables["FLASK_DEBUG"]
            MONGODB_PORT = variables["MONGODB_PORT"]
            MONGODB_HOST = variables["MONGODB_HOST"]
        else:
            print(configuration_file + " can't be found. Setting defaults.")
            CACHE_STALE_SECONDS = 3600
            CACHEVIEW_PORT = 5000
            CACHEVIEW_HOST = "127.0.0.1"
            FLASK_DEBUG = "0"
            MONGODB_PORT = 27017
            MONGODB_HOST = "127.0.0.1"
    except Exception as e:
        raise Exception(e)


def mongodb_connection():
    global collection

    h = "mongodb://%s:%d/" % (MONGODB_HOST, int(MONGODB_PORT))
    c = MongoClient(h)

    try:
        c.admin.command("ismaster")
    except Exception as e:
        raise Exception(e)

    db = c["ansible_cache"]
    collection = db["cache"]


def website():
    app = Flask(__name__)

    @app.route("/")
    def website_index():
        try:
            cacheview_version = __version__
            os_distribution = "na"
            hosts = []
            ansible_cache_update_avg = 0
            stale_cache_hosts = 0

            if FLASK_DEBUG == "1":
                for x in range(150):
                    test_node_distribution = random.choice(
                        ["alpine", "centos", "debian", "redhat", "ubuntu"]
                    )
                    test_node_name = str(test_node_distribution) + "0" + str(x)
                    test_node_cache = random.choice(["true", "false"])
                    test_node = [
                        test_node_name,
                        test_node_distribution,
                        test_node_cache,
                    ]

                    hosts.append(test_node)

            for q in collection.find(
                {"data.ansible_hostname": {"$regex": "^.*$", "$options": "i"}},
                {"_id": 0, "data": 1},
            ):
                ansible_hostname = q["data"]["ansible_hostname"]
                ansible_os_family = q["data"]["ansible_os_family"]
                ansible_date_time_epoch = q["data"]["ansible_date_time"]["epoch"]
                ansible_distribution = q["data"]["ansible_distribution"]
                ansible_cache_update = int(time.time()) - int(ansible_date_time_epoch)
                if ansible_distribution.lower() in (
                    "alpine",
                    "centos",
                    "debian",
                    "redhat",
                    "ubuntu",
                ):
                    os_distribution = q["data"]["ansible_distribution"]
                else:
                    os_distribution = ansible_os_family

                if ansible_cache_update >= CACHE_STALE_SECONDS:
                    ansible_stale_cache = "true"
                    stale_cache_hosts += 1
                else:
                    ansible_stale_cache = "false"

                ansible_cache_update_avg = (
                    ansible_cache_update_avg + ansible_cache_update
                )

                node_info = [
                    ansible_hostname,
                    os_distribution,
                    ansible_stale_cache,
                ]
                hosts.append(node_info)

        except KeyError:
            pass
        except Exception as e:
            raise Exception(e)

        host_count = len(hosts)
        if host_count < 1:
            update_avg = "NA"
        else:
            update_avg = round(ansible_cache_update_avg / host_count)

        return render_template(
            "index.html",
            host_count=host_count,
            hosts=hosts,
            update_avg=update_avg,
            stale_cache_hosts=stale_cache_hosts,
            cache_stale=CACHE_STALE_SECONDS,
            cacheview_version=cacheview_version,
        )

    @app.route("/node/<hostname>")
    def website_hostname(hostname):
        try:
            nodeinfo = "%s not found." % (hostname)
            os_distribution = "na"
            for q in collection.find(
                {"data.ansible_hostname": hostname}, {"_id": 0, "data": 1}
            ):
                data = q["data"]
                ansible_distribution = q["data"]["ansible_distribution"]
                ansible_os_family = q["data"]["ansible_os_family"]

                if data["ansible_hostname"] == hostname:
                    if ansible_distribution.lower() in (
                        "alpine",
                        "centos",
                        "debian",
                        "redhat",
                        "ubuntu",
                    ):
                        os_distribution = q["data"]["ansible_distribution"]
                    else:
                        os_distribution = ansible_os_family
                    nodeinfo = json.dumps(data, sort_keys=True, indent=4)
        except KeyError:
            pass
        except Exception as e:
            raise Exception(e)

        return render_template(
            "node.html",
            hostname=hostname,
            nodeinfo=nodeinfo,
            os_distribution=os_distribution,
        )

    @app.route("/info")
    def website_status():
        try:
            cacheview_version = __version__
            python_version = sys.version
            return render_template(
                "info.html", version=cacheview_version, python=python_version,
            )
        except Exception as e:
            raise Exception(e)

    @app.route("/result", methods=["POST", "GET"])
    def result():
        try:
            if request.method == "POST":
                query = request.form["query"]
                if collection.count_documents({"data.ansible_hostname": query}) <= 0:
                    result = "Query " + query + " didn't return anything."
                    return render_template("result.html", result=result, query=query)

                for q in collection.find(
                    {"data.ansible_hostname": query}, {"_id": 0, "data": 1}
                ):
                    if q:
                        result = json.dumps(q, sort_keys=True, indent=4)
                        return render_template(
                            "result.html", result=result, query=query
                        )
                    else:
                        return render_template("result.html", result="", query="")
        except Exception as e:
            result = e
            return render_template("result.html", result=result, query=query)
            raise Exception(e)

    if FLASK_DEBUG == "1":
        app.run(host=CACHEVIEW_HOST, port=CACHEVIEW_PORT, debug="True")
    else:
        app.run(host=CACHEVIEW_HOST, port=CACHEVIEW_PORT)


if __name__ == "__main__":
    read_configuration()
    mongodb_connection()
    website()
