FROM ubuntu:22.04
USER root 

RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN export ubuntu_name="ubuntu-22.04-jammy"

RUN mkdir -p /etc/yandex/unified_agent
RUN touch config.yml
COPY config.yml /etc/yandex/unified_agent/config.yml

RUN bash -c 'curl --silent --remote-name https://storage.yandexcloud.net/yc-unified-agent/releases/25.12.20/deb/ubuntu-22.04-jammy/yandex-unified-agent_25.12.20_amd64.deb'
RUN dpkg -i yandex-unified-agent_25.12.20_amd64.deb

RUN unified_agent check-config -c /etc/yandex/unified_agent/config.yml
CMD ["unified_agent", "-c", "/etc/yandex/unified_agent/config.yml"]
