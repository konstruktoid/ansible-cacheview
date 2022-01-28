#!/usr/bin/python3
"""Very basic Flask app to view Ansible cache stored in MongoDB."""
import json
import os
import random
import sys
import time

from flask import Flask, render_template, request
from pymongo import MongoClient
from pymongo.errors import OperationFailure
from version import __version__

CACHEVIEW_HOST = None
CACHEVIEW_PORT = None
CACHE_STALE_SECONDS = None
COLLECTION = None
FLASK_TEST = None
MONGODB_HOST = None
MONGODB_PORT = None


def read_configuration():
    """Read and import configuration or use the default."""
    global CACHE_STALE_SECONDS, CACHEVIEW_PORT, CACHEVIEW_HOST, FLASK_TEST, MONGODB_PORT, MONGODB_HOST

    try:
        configuration_file = "cacheview.cfg"
        variables = {}

        if os.path.isfile(configuration_file):
            with open(configuration_file, encoding="UTF-8") as conf_file:
                for line in conf_file:
                    name, value = line.split("=")
                    variables[name] = value.rstrip()

            CACHE_STALE_SECONDS = int(variables["CACHE_STALE_SECONDS"])
            CACHEVIEW_PORT = variables["CACHEVIEW_PORT"]
            CACHEVIEW_HOST = variables["CACHEVIEW_HOST"]
            FLASK_TEST = variables["FLASK_TEST"]
            MONGODB_PORT = variables["MONGODB_PORT"]
            MONGODB_HOST = variables["MONGODB_HOST"]
        else:
            print(configuration_file + " can't be found. Using defaults.")
            CACHE_STALE_SECONDS = 3600
            CACHEVIEW_PORT = 5000
            CACHEVIEW_HOST = "127.0.0.1"
            FLASK_TEST = 0
            MONGODB_PORT = 27017
            MONGODB_HOST = "127.0.0.1"
    except Exception as read_configuration_exception:
        raise Exception from read_configuration_exception


def mongodb_connection():
    """Connect to the MongoDB database."""
    global COLLECTION

    db_host = "mongodb://%s:%d/" % (MONGODB_HOST, int(MONGODB_PORT))
    db_client = MongoClient(db_host)

    try:
        db_client.admin.command("ismaster")
    except Exception as mongodb_connection_exception:
        raise Exception from mongodb_connection_exception

    ansible_db = db_client["ansible_cache"]
    COLLECTION = ansible_db["cache"]


def website_index():
    """Generate the website index."""
    try:
        cacheview_version = __version__
        os_distribution = "na"
        hosts = []
        ansible_cache_update_avg = 0
        stale_cache_hosts = 0

        if FLASK_TEST == "1":
            system_random = random.SystemRandom()
            for distribution in range(150):
                test_distributions = [
                    "alpine",
                    "centos",
                    "debian",
                    "macosx",
                    "redhat",
                    "ubuntu",
                ]
                test_node_distribution = system_random.choice(test_distributions)
                test_node_name = str(test_node_distribution) + "0" + str(distribution)
                test_cache = ["true", "false"]
                test_node_cache = system_random.choice(test_cache)
                test_node = [
                    test_node_name,
                    test_node_distribution,
                    test_node_cache,
                ]

                hosts.append(test_node)

        for document in COLLECTION.find(
            {"data.ansible_hostname": {"$regex": "^.*$", "$options": "i"}},
            {"_id": 0, "data": 1},
        ):
            ansible_hostname = document["data"]["ansible_hostname"]
            ansible_os_family = document["data"]["ansible_os_family"]
            ansible_date_time_epoch = document["data"]["ansible_date_time"]["epoch"]
            ansible_distribution = document["data"]["ansible_distribution"]
            ansible_cache_update = int(time.time()) - int(ansible_date_time_epoch)
            if ansible_distribution.lower() in (
                "alpine",
                "centos",
                "debian",
                "macosx",
                "redhat",
                "ubuntu",
            ):
                os_distribution = document["data"]["ansible_distribution"].lower()
            else:
                os_distribution = ansible_os_family

            if ansible_cache_update >= CACHE_STALE_SECONDS:
                ansible_stale_cache = "true"
                stale_cache_hosts += 1
            else:
                ansible_stale_cache = "false"

            ansible_cache_update_avg = ansible_cache_update_avg + ansible_cache_update

            node_info = [
                ansible_hostname,
                os_distribution,
                ansible_stale_cache,
            ]
            hosts.append(node_info)

    except KeyError:
        pass

    except Exception as website_index_exception:
        raise Exception from website_index_exception

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


def cache_vm_hostname(hostname):
    """Get hostnames and distributions."""
    try:
        nodeinfo = "%s not found." % (hostname)
        os_distribution = "na"
        for document in COLLECTION.find(
            {"data.ansible_hostname": hostname}, {"_id": 0, "data": 1}
        ):
            data = document["data"]
            ansible_distribution = document["data"]["ansible_distribution"]
            ansible_os_family = document["data"]["ansible_os_family"]

            if data["ansible_hostname"] == hostname:
                if ansible_distribution.lower() in (
                    "alpine",
                    "centos",
                    "debian",
                    "macosx",
                    "redhat",
                    "ubuntu",
                ):
                    os_distribution = document["data"]["ansible_distribution"].lower()
                else:
                    os_distribution = ansible_os_family.lower()
                nodeinfo = json.dumps(data, sort_keys=True, indent=4)

    except KeyError:
        pass

    except Exception as cache_vm_hostname_exception:
        raise Exception from cache_vm_hostname_exception

    try:
        return render_template(
            "node.html",
            hostname=hostname,
            nodeinfo=nodeinfo,
            os_distribution=os_distribution,
        )

    except Exception as render_template_exception:
        raise Exception from render_template_exception


def website_status():
    """Print cacheview and Python version."""
    try:
        cacheview_version = __version__
        python_version = sys.version

        return render_template(
            "info.html",
            version=cacheview_version,
            python=python_version,
        )
    except Exception as website_status_exception:
        raise Exception from website_status_exception


def result():
    """Render query results."""
    try:
        query_result = []
        if request.method == "POST":
            try:
                query = request.form["query"]
                query = json.loads(str(query))
            except ValueError as result_query_exception:
                query_result.append(result_query_exception)
            try:
                if COLLECTION.count_documents(query) <= 0:
                    query_result.append("Your query didn't return anything.")

                for documents in COLLECTION.find(query):
                    if documents:
                        query_result.append(
                            json.dumps(documents, sort_keys=True, indent=4, default=str)
                        )

                return render_template("result.html", result=query_result, query=query)
            except KeyError:
                pass
        else:
            query_result.append("Incorrect request method.")
            return render_template("result.html", result=query_result, query=query)

    except OperationFailure:
        return render_template("result.html", result=query_result, query="Exception")


def website():
    """Add website paths and run the app."""
    app = Flask(__name__)

    app.add_url_rule("/", "website_index", website_index)
    app.add_url_rule("/info", "website_status", website_status)
    app.add_url_rule("/node/<hostname>", "cache_vm_hostname", cache_vm_hostname)
    app.add_url_rule("/result", "result", result, methods=["POST", "GET"])

    app.run(host=CACHEVIEW_HOST, port=CACHEVIEW_PORT)


if __name__ == "__main__":
    read_configuration()
    mongodb_connection()
    website()
