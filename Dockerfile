FROM python:3.12.3-slim

ARG UID=10001
ARG GID=10001

WORKDIR /app

RUN groupadd -g ${GID} app; \
  useradd -g ${GID} -u ${UID} -m -s /usr/sbin/nologin app

RUN python -m pip install poetry==1.8.2

COPY . .

USER app

RUN poetry install --without dev

CMD ["poetry", "run", "geoip2gcs"]
