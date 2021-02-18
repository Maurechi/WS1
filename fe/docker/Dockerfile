FROM debian:buster AS builder

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y curl gnupg2
# RUN apt-get install -y apt-utils
# RUN apt-get install -y ca-certificates git curl wget jq moreutils

RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | env APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=yes apt-key add -

RUN echo "deb https://deb.nodesource.com/node_14.x buster main" > /etc/apt/sources.list.d/nodesource.list
RUN echo "deb-src https://deb.nodesource.com/node_14.x buster main" >> /etc/apt/sources.list.d/nodesource.list

RUN apt-get update
RUN apt-get install -y nodejs

RUN mkdir /diaas/
WORKDIR /diaas/
COPY ./package.json ./package-lock.json ./
RUN npm ci

COPY jsconfig.json jsconfig.json
COPY public public
COPY src src

RUN npm run build

FROM nginx:stable
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y python3=3.7.3-1

COPY --from=builder /diaas/build/ /usr/share/nginx/html/
COPY ./docker/build-diaas-js.py /docker-entrypoint.d/
COPY ./docker/99-build-diaas-js.sh /docker-entrypoint.d/
