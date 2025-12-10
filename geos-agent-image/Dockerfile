# Base GEOS toolchain + TPLs
# docker pull geosx/ubuntu22.04-gcc11:326-878
# FROM geosx/ubuntu22.04-gcc12:main
FROM geosx/ubuntu22.04-gcc11:326-878

# 1. Create non-root user and workspace
RUN useradd -m -s /bin/bash geos && \
    mkdir -p /workspace && \
    chown -R geos:geos /workspace /home/geos

# 2. Install system tools *as root*
RUN apt-get update && \
    apt-get install -y \
        build-essential \
        git \
        git-lfs \
        cmake \
        python3 python3-pip python3-venv \
        vim \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

# 3. Switch to non-root user for normal use
USER geos
WORKDIR /workspace

# 4. (later) clone & build GEOS, install your agent deps, etc.
# RUN git clone https://github.com/GEOS-DEV/GEOS.git
#     cd GEOS
#     git lfs install
#     git submodule init
#     git submodule update
#     cd ..

# NOTE: TPL dependencies from docker hub may be incomplete...



CMD ["/bin/bash"]

