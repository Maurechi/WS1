FROM postgres:13 AS pg_hashids
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y git build-essential postgresql-server-dev-13
WORKDIR /opt/
RUN git clone 'https://github.com/iCyberon/pg_hashids.git' && cd pg_hashids && git reset --hard 83398bcbb616aac2970f5e77d93a3200f0f28e74 # 83398bcbb616aac2970f5e77d93a3200f0f28e74
RUN cd pg_hashids && make && make install
RUN cd / && find ./usr/ -name "*pg_hashids*" -print0 | xargs -0 tar -cvpf /opt/pg_hashids.tar

FROM postgres:13
COPY --from=pg_hashids /opt/pg_hashids.tar /opt/pg_hashids.tar
RUN cd / && tar -xvf /opt/pg_hashids.tar
