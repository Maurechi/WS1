FROM postgres:13 AS pg_hashids
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git build-essential postgresql-server-dev-13
WORKDIR /opt/
RUN git clone 'https://github.com/iCyberon/pg_hashids.git'
RUN cd pg_hashids && make && make install
RUN find /usr/ -name "*pg_hashids*" -print0 | xargs -0 tar -C / -cvpf /opt/pg_hashids.tar

FROM postgres:13
COPY --from=pg_hashids /opt/pg_hashids.tar /opt/pg_hashids.tar
RUN tar -C / -xvf /opt/pg_hashids.tar
