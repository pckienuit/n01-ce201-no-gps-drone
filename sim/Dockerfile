FROM ubuntu@sha256:008173c23f95b170204355c12626cb5a965d779a7e1283b09e9cffbb1bf33ca3
ARG PX4_COMMIT=6ea3539157ca358c70a515878b77077af7d4611d
ARG USER_ID=1000
ARG GROUP_ID=1000
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update -qq && apt-get install -y --no-install-recommends ca-certificates curl \
    && mkdir -p /opt/px4-setup \
    && curl -fsSL https://raw.githubusercontent.com/PX4/PX4-Autopilot/${PX4_COMMIT}/Tools/setup/ubuntu.sh -o /opt/px4-setup/ubuntu.sh \
    && curl -fsSL https://raw.githubusercontent.com/PX4/PX4-Autopilot/${PX4_COMMIT}/Tools/setup/requirements.txt -o /opt/px4-setup/requirements.txt \
    && bash /opt/px4-setup/ubuntu.sh --no-nuttx \
    && apt-get install -y --no-install-recommends python3-venv libegl1-mesa-dev libgl1-mesa-dri mesa-utils xvfb xauth \
    && python3 -m venv --system-site-packages /opt/n01-venv \
    && /opt/n01-venv/bin/pip install mavsdk==4.1.0 \
    && /opt/n01-venv/bin/pip freeze > /opt/n01-python-lock.txt \
    && dpkg-query -W > /opt/n01-dpkg-lock.txt \
    && rm -rf /var/lib/apt/lists/*
RUN if getent passwd ${USER_ID}; then userdel $(getent passwd ${USER_ID} | cut -d: -f1); fi \
    && (getent group ${GROUP_ID} || groupadd -g ${GROUP_ID} sim) \
    && useradd -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash sim
ARG MAVSDK_VERSION=3.17.4
# Keep dependency installation cached; v4 uses a different native API.
RUN /opt/n01-venv/bin/pip install mavsdk==${MAVSDK_VERSION} \
    && /opt/n01-venv/bin/pip freeze > /opt/n01-python-lock.txt
ENV PATH=/opt/n01-venv/bin:$PATH HOME=/home/sim QT_X11_NO_MITSHM=1
USER sim
WORKDIR /px4
CMD ["bash"]
