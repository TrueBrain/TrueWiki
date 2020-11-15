FROM python:3.8-slim

ARG BUILD_DATE=""
ARG BUILD_VERSION="dev"

LABEL maintainer="TrueBrain <truebrain@truebrain.nl>"
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.authors="TrueBrain <truebrain@truebrain.nl>"
LABEL org.opencontainers.image.url="https://github.com/TrueBrain/TrueWiki"
LABEL org.opencontainers.image.source="https://github.com/TrueBrain/TrueWiki"
LABEL org.opencontainers.image.version=${BUILD_VERSION}
LABEL org.opencontainers.image.licenses="AGPLv3"
LABEL org.opencontainers.image.title="Wiki Server"
LABEL org.opencontainers.image.description="TrueWiki is a wikitext server similar to mediawiki and gollum"

# git is needed to clone the wiki data
# openssh-client is needed to git clone over ssh
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

# We will be connecting to github.com, so populate their key already.
RUN mkdir -p ~/.ssh \
    && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts

COPY requirements.txt .

# Needed for Sentry to know what version we are running
RUN echo "${BUILD_VERSION}" > ./.version

RUN pip --no-cache-dir install -r requirements.txt

# Validate that what was installed was what was expected
RUN pip freeze 2>/dev/null > requirements.installed \
        && diff -u --strip-trailing-cr requirements.txt requirements.installed 1>&2 \
        || ( echo "!! ERROR !! requirements.txt defined different packages or versions for installation" \
                && exit 1 ) 1>&2

# NOTE don't forget to create the subfolders manually : /data/File, /data/Category, /data/Page, /data/Template
VOLUME /data 
VOLUME /cache
VOLUME /code
WORKDIR /code

ENTRYPOINT ["python", "-m", "truewiki"]
CMD ["--bind", "0.0.0.0", "--storage", "local", "--storage-folder", "/data", "--cache-metadata-file", "/cache/metadata.json", "--cache-page-folder", "/cache/pages", "--user", "developer"]

EXPOSE 80
