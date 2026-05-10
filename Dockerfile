# Build and Test stage
FROM debian:trixie-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    git \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /build
COPY . .

# Build the C-based compiler
RUN make clean && make CC=gcc

# Install Python tools and dependencies
# Using --break-system-packages as this is an isolated container environment
RUN pip install --break-system-packages . pycparser pytest

# Run the validation ladder
RUN pytest -q && \
    mkdir -p build && \
    cy16-as examples/setup_stub.s -o build/setup_stub.bin --base 0x1000 && \
    cy16-dis build/setup_stub.bin --base 0x1000 && \
    cy16-sim build/setup_stub.bin --base 0x1000 --pc 0x1000 --dump 0xc03a && \
    ./chibicc examples/c/write_memctl.c -S > build/write_memctl.s && \
    cy16-as build/write_memctl.s -o build/write_memctl.bin --base 0x1000 && \
    cy16-sim build/write_memctl.bin --base 0x1000 --pc 0x1000 --dump 0xc03a

# Final Runtime stage
FROM debian:trixie-slim AS runtime

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy built binary
COPY --from=builder /build/chibicc /usr/local/bin/cy16-cc

# Install the Python package for the boot tools (assembler/sim)
COPY . /app/
RUN pip install --break-system-packages . pycparser

# Set environment
ENV PATH="/usr/local/bin:$PATH"

# Default volume for user code
WORKDIR /work
VOLUME /work

ENTRYPOINT ["cy16-cc"]
CMD ["--help"]
