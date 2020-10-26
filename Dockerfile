FROM python:3.8-slim

ARG BUILD_DATE=""
ARG BUILD_VERSION="dev"

LABEL maintainer="TrueBrain <truebrain@truebrain.nl>"
LABEL org.opencontainers.image.created=${BUILD_DATE}
LABEL org.opencontainers.image.authors="TrueBrain <truebrain@truebrain.nl>"
LABEL org.opencontainers.image.url="https://github.com/TrueBrain/TrueWiki"
LABEL org.opencontainers.image.source="https://github.com/TrueBrain/TrueWiki"
LABEL org.opencontainers.image.version=${BUILD_VERSION}
LABEL org.opencontainers.image.licenses="GPLv2"
LABEL org.opencontainers.image.title="Wiki Server"
LABEL org.opencontainers.image.description="TrueWiki is a wikitext server similar to mediawiki and gollum"

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

COPY truewiki /code/truewiki

ENTRYPOINT ["python", "-m", "truewiki"]
CMD []
