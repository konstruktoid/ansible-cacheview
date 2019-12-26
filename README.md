# cacheview

`cacheview` is a basic [Ansible](https://www.ansible.com/) cache viewer using
[python](https://www.python.org/), [MongoDB](https://www.mongodb.com/)
and the [Flask](https://palletsprojects.com/p/flask/) framework.

## configuration

### cacheview.cfg

```
CACHEVIEW_HOST=127.0.0.1
CACHEVIEW_PORT=5000
CACHE_STALE_SECONDS=3600
FLASK_DEBUG=0
MONGODB_HOST=127.0.0.1
MONGODB_PORT=27017
```

`CACHEVIEW_HOST` is the listening IP address.

`CACHEVIEW_PORT` configures the listening port.

`CACHE_STALE_SECONDS` is the amount of seconds before we consider a cache entry old.

`FLASK_DEBUG` will enable Flask debug mode and create 150 fake nodes for layout
  testing if set to `1`.

`MONGODB_HOST` is the MongoDB server IP address.

`MONGODB_PORT` is the listening port of the MongoDB server.

#### note

[Flask’s built-in server is not suitable for production](https://flask.palletsprojects.com/en/1.1.x/deploying/)
and the MongoDB connection does not use any form of authentication or encrypted
communication.

Handle with care, and don't allow connections from other IP
addresses than `127.0.0.1` unless there's proper protection and a configured
server in place.

### ansible.cfg

Ansible MongoDB cache plugin documentation is available at
[https://docs.ansible.com/ansible/latest/plugins/cache/mongodb.html](https://docs.ansible.com/ansible/latest/plugins/cache/mongodb.html)

```
[defaults]
fact_caching = mongodb
fact_caching_timeout = 86400
fact_caching_connection = mongodb://localhost:27017/ansible_cache
```

### website routes

```
@app.route("/")
@app.route("/node/<hostname>")
@app.route("/info")
```

## usage

### building and running

```
pip3 install -r requirements.txt
python3 cacheview/cacheview.py
```

### building and running using Docker

```
docker build --no-cache --tag konstruktoid/cacheview:latest \
  --tag konstruktoid/cacheview:$(awk -F '"' '{print $2}' cacheview/version.py) \
  -f Dockerfile .
```

```
docker run -d --cap-drop=all --publish=5000:5000 konstruktoid/cacheview:latest
```

## contributing

Do you want to contribute? That's great! Contributions are always welcome,
no matter how large or small. If you found something odd, feel free to submit a
new issue, improve the code by creating a pull request],
or by [https://github.com/sponsors/konstruktoid](sponsoring this project).

If you're submitting code, please use [https://github.com/psf/black](_Black_) with
default settings and `python3 -m flake8 --ignore=E501`.

