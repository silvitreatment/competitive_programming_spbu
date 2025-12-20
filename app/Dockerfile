FROM ubuntu:22.04

# Install prerequisites for downloading and installing the Unified Agent.
RUN apt-get update && \
    apt-get install -y --no-install-recommends ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Download and install the latest Yandex Unified Agent deb package.
RUN export ubuntu_name="ubuntu-22.04-jammy" 
RUN export ua_version=$(curl --silent https://storage.yandexcloud.net/yc-unified-agent/latest-version) 
RUN bash -c 'curl --silent --remote-name https://storage.yandexcloud.net/yc-unified-agent/releases/${ua_version}/deb/${ubuntu_name}/yandex-unified-agent_${ua_version}_amd64.deb'


# Copy agent configuration into the container.
COPY config.yml /etc/yandex/unified_agent/config.yml

# Validate configuration at build time to fail fast if invalid.
RUN unified_agent check-config -c /etc/yandex/unified_agent/config.yml

# Run the agent in the foreground with the provided config.
CMD ["unified_agent", "-c", "/etc/yandex/unified_agent/config.yml"]
