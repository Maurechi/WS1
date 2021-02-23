FROM debian:buster
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get install -y apt-utils
RUN apt-get install -y ca-certificates git curl wget jq moreutils
RUN apt-get install -y libpq-dev gcc

RUN echo "dash dash/sh boolean false" | debconf-set-selections
RUN dpkg-reconfigure dash

RUN apt-get install -y python3-dev=3.7.3-1 python3-venv=3.7.3-1
# RUN curl -o /tmp/docker.tgz https://download.docker.com/linux/static/stable/x86_64/docker-20.10.3.tgz && \
#     tar -C /tmp/ -zxvf /tmp/docker.tgz && \
#     cp /tmp/docker/docker /usr/bin/docker

RUN mkdir -p /diaas/be
WORKDIR /diaas/be
RUN python3 -mvenv .venv ; source .venv/bin/activate ; pip install -U pip wheel
COPY ./be/requirements.txt ./
RUN source .venv/bin/activate ; pip install -r requirements.txt
COPY ./be ./

ENTRYPOINT ["/diaas/be/docker/docker-entrypoint.sh"]
CMD ["/diaas/be/docker/up"]
