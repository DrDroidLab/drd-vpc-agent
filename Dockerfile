FROM python:3.12-bullseye

RUN apt-get update \
  # dependencies for building Python packages \
  && apt-get install -y build-essential \
  # psycopg2 dependencies
  && apt-get install -y libpq-dev \
  # Translations dependencies
  && apt-get install -y gettext \
  # Nginx
  && apt-get install -y nginx vim procps curl libpq-dev -y --no-install-recommends \
  # Install kubectl
  && curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" \
  && install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/* \
  && rm kubectl

COPY nginx.default /etc/nginx/sites-available/default
RUN ln -sf /dev/stdout /var/log/nginx/access.log \
    && ln -sf /dev/stderr /var/log/nginx/error.log

# Set environment variables
ENV PIP_DISABLE_PIP_VERSION_CHECK 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install Rust for building dependencies
ENV PATH="/root/.cargo/bin:${PATH}"
RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

# Set work directory
WORKDIR /code

# Copy project
COPY . /code
RUN chown -R www-data:www-data /code

RUN pip install uv
RUN uv pip sync requirements.txt --system

COPY scripts/start-celery-worker.sh .
RUN sed -i 's/\r$//g' start-celery-worker.sh
RUN chmod +x start-celery-worker.sh

COPY scripts/start-celery-beat.sh .
RUN sed -i 's/\r$//g' start-celery-beat.sh
RUN chmod +x start-celery-beat.sh


EXPOSE 8080
STOPSIGNAL SIGTERM