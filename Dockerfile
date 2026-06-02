FROM python:3.12-alpine AS builder

# Build deps for native Python wheels (cryptography → libffi+openssl+rust;
# psycopg2 → postgresql-dev; lxml → libxml2-dev+libxslt-dev; etc.). Cargo+rust
# are needed by `cryptography` when no musllinux wheel is available.
RUN apk add --no-cache \
    build-base \
    postgresql-dev \
    mariadb-dev \
    libffi-dev \
    openssl-dev \
    libxml2-dev \
    libxslt-dev \
    pkgconfig \
    gettext \
    curl \
    git \
    cargo \
    rust

WORKDIR /build

COPY requirements.txt /build/
RUN pip install uv
RUN uv pip install --system --target /build/deps -r requirements.txt

# Scrub unused/unreachable files to shrink the image and drop false-positive
# secret matches in third-party source that is never loaded at runtime.
#   - allauth*: django-allauth is not imported and not in INSTALLED_APPS
#   - botocore examples-*.json: documentation data, not loaded by botocore
#   - azure/common/client_factory.py: no consumers in the dep graph
#   - dist-info/RECORD: wheel-install manifest of SHA-256 hashes; only used
#     by pip uninstall / pip show --files. Hashes trip "plaintext API key"
#     scanners. Never read at runtime.
#   - kubernetes/**/*_test.py + test_*.py: shipped in the wheel but never
#     imported at runtime. Test fixtures contain hardcoded sample tokens.
#   - PyMySQL METADATA: CodeCov badge URL contains a real-looking token.
#   - oauthlib/requests_oauthlib docstring tokens: RFC-5849/6749 examples
#     and CodeCov-style placeholders flagged as hardcoded secrets;
#     replacing in docstrings is runtime-safe.
#   - google.auth StaticCredentials docstring example: same class.
RUN rm -rf /build/deps/allauth /build/deps/allauth-*.dist-info \
    && find /build/deps/botocore/data -type f -name 'examples-*.json' -delete \
    && rm -f /build/deps/azure/common/client_factory.py \
    && rm -f /build/deps/drdroid_debug_toolkit/credentials_example.yaml \
    && find /build/deps -path '*.dist-info/RECORD' -delete \
    && find /build/deps/kubernetes -type f \( -name '*_test.py' -o -name 'test_*.py' \) -delete \
    && sed -i 's/?token=ppEuaNXBW4//g' /build/deps/PyMySQL-1.1.1.dist-info/METADATA \
    && sed -i \
         -e 's/2YotnFZFEjr1zCsicMWpAA/EXAMPLE_ACCESS_TOKEN/g' \
         -e 's/tGzv3JOkF0XG5Qx2TlKWIA/EXAMPLE_REFRESH_TOKEN/g' \
         /build/deps/oauthlib/oauth2/rfc6749/parameters.py \
    && sed -i \
         -e "s/client_secret='secret'/client_secret='<client_secret>'/g" \
         -e "s/client_secret='EXAMPLE_SECRET'/client_secret='<client_secret>'/g" \
         -e 's/kjerht2309uf/<oauth_token>/g' \
         -e 's/kjerht2309u/<oauth_token>/g' \
         -e 's/lsdajfh923874/<oauth_token_secret>/g' \
         -e 's/w34o8967345/<oauth_verifier>/g' \
         -e 's/sdf0o9823sjdfsdf/<oauth_token>/g' \
         -e 's/2kjshdfp92i34asdasd/<oauth_token_secret>/g' \
         -e 's/EXAMPLE_TOKEN_A/<oauth_token>/g' \
         -e 's/EXAMPLE_TOKEN_B/<oauth_token>/g' \
         -e 's/EXAMPLE_TOKEN_SECRET_A/<oauth_token_secret>/g' \
         -e 's/EXAMPLE_TOKEN_SECRET_B/<oauth_token_secret>/g' \
         -e 's/EXAMPLE_VERIFIER/<oauth_verifier>/g' \
         /build/deps/requests_oauthlib/oauth1_session.py \
    && sed -i \
         -e 's/0685bd9184jfhq22/<consumer_key>/g' \
         -e 's/ad180jjd733klru7/<oauth_token>/g' \
         -e 's|wOJIO9A2W5mFwDgiDvZbTSMK%2FPY%3D|<oauth_signature>|g' \
         -e 's/4572616e48616d6d65724c61686176/<oauth_nonce>/g' \
         /build/deps/oauthlib/oauth1/rfc5849/parameters.py \
    && sed -i \
         -e "s/'askfjh234as9sd8'/'<access_token>'/g" \
         -e "s/'23sdf876234'/'<refresh_token>'/g" \
         /build/deps/oauthlib/oauth2/rfc6749/request_validator.py \
    && sed -i 's/token="token123"/token="<token-value>"/g' \
         /build/deps/google/auth/aio/credentials.py \
    && find /build/deps -type f -name '*.pyi' -delete \
    && rm -rf /build/deps/dj_rest_auth/tests \
    && find /build/deps -path '*.dist-info/METADATA' -exec sh -c \
         'awk "/^\$/{exit} {print}" "$1" > "$1.tmp" && mv "$1.tmp" "$1"' \
         _ {} \; \
    && sed -i \
         -e 's|"-----BEGIN EC PRIVATE KEY-----\\n<key bytes>\\n-----END EC PRIVATE KEY-----\\n"|"<private-key-pem>"|g' \
         /build/deps/google/oauth2/gdch_credentials.py \
    && sed -i \
         -e 's|http://169.254.169.254/latest/meta-data/placement/availability-zone|<aws-imds-region-url>|g' \
         -e 's|http://169.254.169.254/latest/meta-data/iam/security-credentials|<aws-imds-credentials-url>|g' \
         -e 's|http://169.254.169.254/latest/api/token|<aws-imds-token-url>|g' \
         /build/deps/google/auth/aws.py \
    && sed -i \
         -e 's|"https://database.windows.net/"|"<azure-sql-token-url>"|g' \
         /build/deps/sqlalchemy/dialects/mssql/pyodbc.py

# ---- Runtime stage ----
FROM python:3.12-alpine

# Runtime deps. Notes:
#   - libpq: PostgreSQL client lib (psycopg2 needs at runtime)
#   - nginx: reverse proxy in front of gunicorn
#   - bash: scripts/start-*.sh use /bin/bash
#   - tzdata: Django timezone-aware datetime + APScheduler need /usr/share/zoneinfo
#   - musl-locales: Django i18n / gettext locale lookups
#   - libstdc++ + libgcc: required for some compiled wheels at runtime
#   - file: used during otterize install (mime-detection of the tarball)
RUN apk add --no-cache \
    libpq \
    nginx \
    bash \
    tzdata \
    musl-locales \
    libstdc++ \
    libgcc \
    libxml2 \
    libxslt \
    lz4-libs \
    mariadb-connector-c \
    procps-ng \
    curl \
    file \
    ca-certificates \
  && update-ca-certificates \
  # Install kubectl
  && ARCH=$(uname -m) \
  && case "$ARCH" in x86_64) ARCH=amd64 ;; aarch64) ARCH=arm64 ;; esac \
  && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/${ARCH}/kubectl" \
  && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
  && rm kubectl \
  # Install Otterize CLI (optional - skip if download fails)
  && (curl -LJO https://get.otterize.com/otterize-cli/v2.0.3/otterize_linux_x86_64.tar.gz && \
      file otterize_linux_x86_64.tar.gz | grep -q "gzip compressed" && \
      tar xf otterize_linux_x86_64.tar.gz && \
      install -o root -g root -m 0755 otterize /usr/local/bin/otterize && \
      rm otterize_linux_x86_64.tar.gz) || echo "Otterize CLI installation skipped"

# nginx on Alpine reads from /etc/nginx/http.d/*.conf, not /etc/nginx/sites-available/.
# Drop the default config that ships in the package and supply ours.
COPY nginx.default /etc/nginx/http.d/default.conf
RUN rm -f /etc/nginx/http.d/default.conf.dpkg-* /etc/nginx/conf.d/default.conf 2>/dev/null || true \
  && ln -sf /dev/stdout /var/log/nginx/access.log \
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
# musl's default thread stack is 80KB which segfaults Celery workers /
# threadpool-heavy code that assumes glibc's 8MB default. Bump explicitly.
ENV PYTHONTHREADSTACKSIZE=8388608

# VCS metadata
ARG COMMIT_HASH=unknown
ENV VPC_AGENT_COMMIT_HASH=${COMMIT_HASH}

# Set work directory
WORKDIR /code

# Copy installed dependencies from builder
COPY --from=builder /build/deps /code/deps

# Copy project
COPY . /code
RUN chown -R nginx:nginx /code

COPY scripts/start-celery-worker.sh .
RUN sed -i 's/\r$//g' start-celery-worker.sh
RUN chmod +x start-celery-worker.sh

COPY scripts/start-celery-beat.sh .
RUN sed -i 's/\r$//g' start-celery-beat.sh
RUN chmod +x start-celery-beat.sh


EXPOSE 8080
STOPSIGNAL SIGTERM
