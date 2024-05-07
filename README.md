# GeoIP2 Database to GCS

This script will:

* Fetch GeoIP2 database and copy it to GCS
* Maintains state of version and only updates when new version is available

## Requirements

* GCS Bucket
* Some scheduler to run script periodicallly

## Usage

### local

> [!NOTE]
> We're managing dependencies with [poetry](https://python-poetry.org/), please install first.

```
poetry install

export MAXMIND_LICENSE_KEY='license'
export GCS_BUCKET='bucket'

poetry run geoip2gcs
```

### local - docker

`geoip2gcs` can be executed with docker.

> [!IMPORTANT]
> In order for containers to succeed, you additionally need to take care of authenticating the container env with GCP.
> Please choose one of the existing [options](https://cloud.google.com/docs/authentication) to do so.

```
docker build -t geoip2gcs:latest .

export MAXMIND_LICENSE_KEY='license'
export GCS_BUCKET='bucket'

docker run \
    --rm \
    --name geoip2gcs \
    -e MAXMIND_LICENSE_KEY=$MAXMIND_LICENSE_KEY \
    -e GCS_BUCKET=$GCS_BUCKET \
    geoip2gcs:latest
```
