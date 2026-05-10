# Helper script to run the CY16 toolchain via Docker on Windows

# Ensure the build directory exists locally so Docker can write to it if needed
if (-not (Test-Path "build")) {
    New-Item -ItemType Directory -Force -Path "build"
}

# Run the container with the current directory mapped to /work
# Passing all script arguments directly to the container's entrypoint (cy16-cc)
docker run --rm -v "${PWD}:/work" cy16-toolchain $args
