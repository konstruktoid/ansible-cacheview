FROM konstruktoid/alpine

LABEL "com.github.actions.name"="Konstruktoid Python linting"
LABEL "com.github.actions.description"="Python black and flake8"
LABEL "com.github.actions.icon"="mic"
LABEL "com.github.actions.color"="purple"

LABEL "repository"="https://github.com/konstruktoid/ansible-cacheview"
LABEL "homepage"="https://github.com/konstruktoid/ansible-cacheview"
LABEL "maintainer"="Thomas Sjögren <konstruktoid@users.noreply.github.com>"

RUN apk update && \
    apk upgrade && \
    apk --update add gcc musl-dev python3-dev python3 && \
    pip3 install --upgrade pip && \
    pip3 install black flake8 && \
    apk del gcc musl-dev python3-dev && \
    rm -rf /var/cache/apk/

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
