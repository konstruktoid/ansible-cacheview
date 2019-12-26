FROM konstruktoid/alpine

LABEL org.label-schema.name="ansible-cacheview" \
      org.label-schema.vcs-url="git@github.com:konstruktoid/ansible-cacheview.git"

COPY ./cacheview /opt/cacheview/
COPY ./requirements.txt /opt/cacheview/

RUN apk update && \
    apk upgrade && \
    apk --no-cache --update add python3 py-pip && \
    pip3 install --upgrade pip && \
    pip3 install -r /opt/cacheview/requirements.txt && \
    apk del --purge py-pip && \
    rm -rf /var/cache/apk/ && \
    adduser -h /home/cacheview -s /bin/sh -D cacheview

WORKDIR /home/cacheview
USER cacheview

CMD ["/usr/bin/python3","/opt/cacheview/cacheview.py"]
