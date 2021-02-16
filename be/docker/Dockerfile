FROM debian:buster

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y apt-utils
RUN apt-get install -y ca-certificates git curl wget jq moreutils
RUN apt-get install -y libpq-dev gcc

RUN echo "dash dash/sh boolean false" | debconf-set-selections
RUN dpkg-reconfigure dash

RUN apt-get install -y python3-dev=3.7.3-1 python3-venv=3.7.3-1
RUN mkdir /diaas
WORKDIR /diaas
RUN python3 -mvenv .venv ; source .venv/bin/activate ; pip install -U pip wheel
COPY ./requirements.txt ./
RUN source .venv/bin/activate ; pip install -r requirements.txt
COPY ./ ./

ENV PYTHONPATH=/diaas/src/
ENTRYPOINT ["/diaas/docker/entrypoint"]
