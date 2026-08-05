# Stage 1: Base system setup
FROM nvidia/cuda:12.4.1-cudnn-runtime-ubuntu20.04 AS base-system

ENV DEBIAN_FRONTEND=noninteractive

# Stage 2: Update system packages and install basic tools
FROM base-system AS update-system

RUN apt-get -qq update && \
    apt-get  --yes --force-yes install software-properties-common curl git wget gnupg

# Stage 3: Install Python 3.10
FROM update-system AS install-python

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get -qq update && \
    apt-get -y install python3.10 python3.10-venv python3.10-dev && \
    ln -sf /usr/bin/python3.10 /usr/bin/python3

# Stage 3: Install pip
FROM install-python AS install-pip

RUN curl -sS https://bootstrap.pypa.io/get-pip.py | python3.10

# Stage 4: Install dependencies
FROM install-pip AS install-dependencies

RUN python3 -m pip install pip --upgrade && \
    python3 -m pip install \
                git+https://github.com/sccn/eegdash.git \
                braindecode \
                scikit-learn \
                mne \
                pandas \
                numpy

# Stage 5: Clean up
FROM copy-restore-data AS clean

RUN apt-get clean && \
    rm -rf /var/lib/apt/lists/* /var/tmp/* && \
    rm -rf ~/.cache/pip

WORKDIR /app/codalab

# Debug: Create entrypoint script
# RUN echo '#!/bin/bash\n\
# set -e\n\
# echo "Starting debug..."\n\
# ls -l /\n\
# exec "$@"' > /entrypoint.sh && \
#     chmod +x /entrypoint.sh

# ENTRYPOINT ["/entrypoint.sh"]
