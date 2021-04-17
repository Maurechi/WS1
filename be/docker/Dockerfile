FROM debian:buster
ENV LANG C.UTF-8
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update -y
RUN apt-get install -y apt-utils
RUN apt-get install -y ca-certificates git curl wget jq moreutils apt-transport-https ca-certificates gnupg
RUN apt-get install -y default-libmysqlclient-dev libpq-dev gcc

RUN echo "dash dash/sh boolean false" | debconf-set-selections
RUN dpkg-reconfigure dash

RUN curl -L https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | bash
RUN echo -e 'export PATH="/root/.pyenv/bin:$PATH"\neval "$(pyenv init -)"\neval "$(pyenv virtualenv-init -)"\n' >> ~/.bashrc
RUN apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev xz-utils tk-dev libffi-dev liblzma-dev python-openssl git
RUN bash -l -c 'pyenv install 3.9.2'
RUN bash -l -c 'pyenv global 3.9.2'
RUN bash -l -c 'pip install -U pip wheel'

RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add -
RUN apt-get update -y
RUN apt-get install google-cloud-sdk -y

RUN mkdir -p /diaas/be
COPY ./be/requirements.txt ./diaas/be/

RUN bash -l -c 'pip install -r /diaas/be/requirements.txt'
CMD ["/diaas/be/docker/up"]
