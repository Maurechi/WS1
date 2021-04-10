FROM debian:buster AS builder
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -y
RUN apt-get install -y curl gnupg2 git
# RUN apt-get install -y apt-utils
# RUN apt-get install -y ca-certificates git curl wget jq moreutils

RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource.gpg.key | env APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=yes apt-key add -

RUN echo "deb https://deb.nodesource.com/node_14.x buster main" > /etc/apt/sources.list.d/nodesource.list
RUN echo "deb-src https://deb.nodesource.com/node_14.x buster main" >> /etc/apt/sources.list.d/nodesource.list

RUN apt-get update
RUN apt-get install -y nodejs

RUN mkdir -p /diaas/fe/
WORKDIR /diaas/fe/
COPY ./fe/package.json package.json
COPY ./fe/package-lock.json package-lock.json
RUN npm ci

COPY ./fe/jsconfig.json jsconfig.json
COPY ./fe/.eslintrc.js .eslintrc.js
COPY ./fe/public public
COPY ./fe/src src

RUN npm run build

FROM nginx:stable
ENV LANG C.UTF-8
RUN DEBIAN_FRONTEND=noninteractive apt-get update && apt-get install -y python3=3.7.3-1

COPY --from=builder /diaas/fe/build/ /usr/share/nginx/html/
RUN rm -f /usr/share/nginx/html/diaas.js
COPY ./fe/docker /diaas/fe/docker
RUN mkdir /diaas/ops/
COPY ./ops/fe-build-diaas-js /diaas/ops/fe-build-diaas-js
CMD ["/diaas/fe/docker/up", "/usr/share/nginx/html/diaas.js"]
