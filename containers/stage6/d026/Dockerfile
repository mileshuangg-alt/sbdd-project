# D026 molecular-identity transformation runtime.
# Immutable inputs:
# - Python: 3.11.11
# - Base image: local tag d026-python-base:3.11.11-pinned
# - Upstream base image: python:3.11.11@sha256:4ca910a51a1a474e5d95aa52455331b2a942eeae3c498be1ad7a2ff9b00bf
# - AiZynthFinder: v4.4.1, commit 9859f5bc6c04c342b828aff20001504c238d7ac1
# - RDKit: 2023.9.6
FROM d026-python-base:3.11.11-pinned

LABEL org.opencontainers.image.base.name="python:3.11.11"
LABEL org.opencontainers.image.base.digest="sha256:4ca910a51a1a474e5d95aa52455331b2a942eeae3c498be1ad7a2ff9b00bf"
LABEL org.opencontainers.image.title="SBDD D026 molecular identity runtime"
LABEL org.opencontainers.image.description="Scientific runtime for D026 molecular-identity transformation environment"
LABEL sbdd.d026.python.version="3.11.11"
LABEL sbdd.d026.rdkit.version="2023.9.6"
LABEL sbdd.d026.aizynthfinder.version="4.4.1"
LABEL sbdd.d026.aizynthfinder.commit="9859f5bc6c04c342b828aff20001504c238d7ac1"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    D026_AIZYNTHFINDER_COMMIT=9859f5bc6c04c342b828aff20001504c238d7ac1

RUN apt-get update \
    && apt-get install -y --no-install-recommends git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade "pip==25.3"

RUN printf '%s\n' \
    'rdkit==2023.9.6' \
    > /opt/d026-python-constraints.txt

RUN git clone https://github.com/MolecularAI/aizynthfinder.git /opt/aizynthfinder-src \
    && cd /opt/aizynthfinder-src \
    && git checkout 9859f5bc6c04c342b828aff20001504c238d7ac1 \
    && test "$(git rev-parse HEAD)" = "9859f5bc6c04c342b828aff20001504c238d7ac1"

RUN python -m pip install --no-cache-dir --constraint /opt/d026-python-constraints.txt "rdkit==2023.9.6" \
    && python -m pip install --no-cache-dir --constraint /opt/d026-python-constraints.txt /opt/aizynthfinder-src

COPY scripts/stage6/d026_runtime_probe.py /usr/local/bin/d026_runtime_probe.py
COPY scripts/stage6/d026_package_inventory.py /usr/local/bin/d026_package_inventory.py
COPY scripts/stage6/d026_smoke_test.py /usr/local/bin/d026_smoke_test.py

RUN chmod 0755 \
    /usr/local/bin/d026_runtime_probe.py \
    /usr/local/bin/d026_package_inventory.py \
    /usr/local/bin/d026_smoke_test.py

CMD ["python", "/usr/local/bin/d026_runtime_probe.py"]
