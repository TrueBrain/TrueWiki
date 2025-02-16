FROM python:3.11-slim

ARG BUILD_VERSION="dev"

# git is needed to clone the wiki data
# openssh-client is needed to git clone over ssh
RUN apt-get update && apt-get install -y --no-install-recommends \
        git \
        openssh-client \
    && rm -rf /var/lib/apt/lists/*

# We might be connecting to github.com / gitlab.com, so populate their key already.
RUN mkdir -p ~/.ssh \
    && ssh-keyscan -t rsa github.com >> ~/.ssh/known_hosts \
    && ssh-keyscan -t rsa gitlab.com >> ~/.ssh/known_hosts

WORKDIR /code

COPY requirements.txt \
        LICENSE \
        README.md \
        /code/
# Needed for Sentry to know what version we are running
RUN echo "${BUILD_VERSION}" > /code/.version

RUN pip --no-cache-dir install -r requirements.txt

# Validate that what was installed was what was expected
RUN pip freeze 2>/dev/null > requirements.installed \
        && diff -u --strip-trailing-cr requirements.txt requirements.installed 1>&2 \
        || ( echo "!! ERROR !! requirements.txt defined different packages or versions for installation" \
                && exit 1 ) 1>&2

COPY static /code/static
COPY templates /code/templates
COPY truewiki /code/truewiki
RUN mkdir /data

ENTRYPOINT ["python", "-m", "truewiki"]
CMD ["--bind", "0.0.0.0", "--storage", "local", "--storage-folder", "/data", "--cache-metadata-file", "/cache/metadata.json", "--cache-page-folder", "/cache/pages", "--user", "developer"]
