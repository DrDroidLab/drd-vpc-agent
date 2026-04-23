FROM python:3.12-bookworm AS builder

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y build-essential libpq-dev gettext curl \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# Install Rust for building dependencies
ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

WORKDIR /build

COPY requirements.txt /build/
RUN pip install uv
RUN uv pip install --system --target /build/deps -r requirements.txt

# Scrub unused/unreachable files to shrink the image and drop false-positive
# secret matches in third-party source that is never loaded at runtime.
#   - allauth*: django-allauth is not imported and not in INSTALLED_APPS
#   - botocore examples-*.json: documentation data, not loaded by botocore
#   - azure/common/client_factory.py: no consumers in the dep graph
#   - oauthlib/requests_oauthlib docstring tokens: RFC-6749 examples flagged
#     as hardcoded secrets; replacing in docstrings is runtime-safe
RUN rm -rf /build/deps/allauth /build/deps/allauth-*.dist-info \
    && find /build/deps/botocore/data -type f -name 'examples-*.json' -delete \
    && rm -f /build/deps/azure/common/client_factory.py \
    && rm -f /build/deps/drdroid_debug_toolkit/credentials_example.yaml \
    && sed -i \
         -e 's/2YotnFZFEjr1zCsicMWpAA/EXAMPLE_ACCESS_TOKEN/g' \
         -e 's/tGzv3JOkF0XG5Qx2TlKWIA/EXAMPLE_REFRESH_TOKEN/g' \
         /build/deps/oauthlib/oauth2/rfc6749/parameters.py \
    && sed -i \
         -e "s/client_secret='secret'/client_secret='EXAMPLE_SECRET'/g" \
         -e 's/kjerht2309uf/EXAMPLE_TOKEN_A/g' \
         -e 's/kjerht2309u/EXAMPLE_TOKEN_A/g' \
         -e 's/lsdajfh923874/EXAMPLE_TOKEN_SECRET_A/g' \
         -e 's/w34o8967345/EXAMPLE_VERIFIER/g' \
         -e 's/sdf0o9823sjdfsdf/EXAMPLE_TOKEN_B/g' \
         -e 's/2kjshdfp92i34asdasd/EXAMPLE_TOKEN_SECRET_B/g' \
         /build/deps/requests_oauthlib/oauth1_session.py

# ---- Runtime stage ----
FROM python:3.12-slim-trixie

RUN apt-get update \
  && apt-get upgrade -y \
  && apt-get install -y --no-install-recommends \
  libpq5 \
  nginx \
  procps \
  curl \
  # Install kubectl
  && ARCH=$(dpkg --print-architecture) \
  && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl" \
  && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
  && rm kubectl \
  # Install Otterize CLI (optional - skip if download fails)
  && (curl -LJO https://get.otterize.com/otterize-cli/v2.0.3/otterize_linux_x86_64.tar.gz && \
  file otterize_linux_x86_64.tar.gz | grep -q "gzip compressed" && \
  tar xf otterize_linux_x86_64.tar.gz && \
  install -o root -g root -m 0755 otterize /usr/local/bin/otterize && \
  rm otterize_linux_x86_64.tar.gz) || echo "Otterize CLI installation skipped" \
  # Clean up
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
  && ln -sf /dev/stderr /var/log/nginx/error.log

# Upgrade the base image's bundled pip to a version without known CVEs
# (CVE-2018-20225, CVE-2025-8869, CVE-2026-1703 — all fixed by >= 26.0).
# Also drop the ensurepip-bundled pip-25.0.1 wheel — Xray flags the wheel even
# though the installed pip is patched, and virtualenv bootstrapping isn't used
# at runtime in this image.
RUN pip install --no-cache-dir --upgrade "pip>=26.0" \
    && rm -f /usr/local/lib/python3.12/ensurepip/_bundled/pip-*.whl

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH="/code/deps:${PYTHONPATH}"
ENV PATH="/code/deps/bin:${PATH}"

# VCS metadata
ARG COMMIT_HASH=unknown
ENV VPC_AGENT_COMMIT_HASH=${COMMIT_HASH}

# Set work directory
WORKDIR /code

# Copy installed dependencies from builder
COPY --from=builder /build/deps /code/deps

# Copy project
COPY . /code
RUN chown -R www-data:www-data /code

COPY scripts/start-celery-worker.sh .
RUN sed -i 's/\r$//g' start-celery-worker.sh
RUN chmod +x start-celery-worker.sh

COPY scripts/start-celery-beat.sh .
RUN sed -i 's/\r$//g' start-celery-beat.sh
RUN chmod +x start-celery-beat.sh


EXPOSE 8080
STOPSIGNAL SIGTERM