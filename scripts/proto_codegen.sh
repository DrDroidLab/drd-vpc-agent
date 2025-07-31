#!/bin/bash
# This has been picked from https://github.com/open-telemetry/opentelemetry-python/blob/e4a4410dc046f011194eff78e801fb230961eec8/scripts/proto_codegen.sh
# This doesn't generate the grpc stubs
set -ex

repo_root="$(git rev-parse --show-toplevel)"
PROTO_REPO_DIR="$repo_root/protos"

cd "$repo_root"/

# clean up old generated code
find "$repo_root"/protos/ -regex ".*_pb2.*\.pyi?" -exec rm {} +

# generate proto code for all protos using existing environments
all_protos=$(find "$PROTO_REPO_DIR" -iname "*.proto")
uv run python3 -m grpc_tools.protoc \
    -I "$repo_root" \
    --python_out=. \
    --mypy_out=. \
    $all_protos
uv pip show protobuf
echo "Latest proto generation done."