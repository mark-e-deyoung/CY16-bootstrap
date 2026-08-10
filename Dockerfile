# syntax=docker/dockerfile:1

ARG DEBIAN_BASE="debian:trixie-slim@sha256:3a39a0592364683e6bab97937b72cad5a8fa6dcbbee90edb3bb48c7f8e94f258"

# Build-only dependencies never enter the runtime image.
FROM ${DEBIAN_BASE} AS builder
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libc6-dev \
        make \
        python3 \
        python3-pip \
        python3-pycparser \
        python3-pytest \
        python3-setuptools \
        python3-wheel \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY pyproject.toml README.md Makefile ./
COPY src ./src
COPY include ./include
COPY libcy16 ./libcy16
COPY examples ./examples
COPY tests ./tests
COPY test*.py ./
COPY test*.c ./
COPY test*.s ./
COPY run_chibicc_test.py run_test_v0.py ./

# Build one wheel, use that exact wheel for the builder validation environment,
# and stage the same bytes for the final runtime. --ignore-installed prevents the
# staging install from uninstalling the builder's test copy.
RUN rm -rf /dist /runtime-root \
    && mkdir -p /dist \
    && python3 -m pip wheel --no-build-isolation --no-deps --wheel-dir=/dist . \
    && python3 -m pip install --break-system-packages --no-deps /dist/*.whl \
    && python3 -m pip install --break-system-packages --no-deps --ignore-installed \
         --root=/runtime-root /dist/*.whl

RUN make clean && make CC=gcc

# A clean Docker build of this target is the canonical isolated validation
# ladder. It intentionally does not persist a running container.
FROM builder AS test
RUN pytest -q \
    && mkdir -p build \
    && cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 \
         --lst build/setup_stub.lst --map build/setup_stub.map \
    && cy16-dis build/setup_stub.bin --base 0x1000 \
    && cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --dump 0xc03a \
    && cy16-scanwrap build/setup_stub.bin build/setup_stub.scan 0x1000 \
    && cy16-scan-decode build/setup_stub.scan \
    && ./chibicc examples/c/write_memctl.c -S > build/write_memctl.s \
    && cy16-as build/write_memctl.s -o build/write_memctl.bin --base 0x1000 \
    && cy16-sim build/write_memctl.bin --base 0x1000 --pc 0x1000 --dump 0xc03a

# Runtime contains Python, pycparser, installed CY16 Python CLIs, and the
# separately named compiled chibicc-derived binary. No compiler, make, pip,
# source checkout, test suite, or implicit volume is retained.
FROM ${DEBIAN_BASE} AS runtime
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-minimal \
        python3-pycparser \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /runtime-root/usr/local/ /usr/local/
COPY --from=builder /src/chibicc /usr/local/bin/cy16-chibicc

LABEL org.opencontainers.image.source="https://github.com/mark-e-deyoung/CY16-bootstrap"
LABEL org.opencontainers.image.description="Minimal CY16 bootstrap assembler/compiler/simulator toolchain"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/tmp

# Numeric non-root identity avoids adding account-management packages to the
# final image. Host wrappers may override this with the invoking non-root UID/GID
# on Linux so generated files have the developer's ownership.
USER 65532:65532
WORKDIR /work

ENTRYPOINT ["cy16-cc"]
CMD ["--help"]
