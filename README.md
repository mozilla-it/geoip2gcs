GeoIP2 Database to GCS
===================

This script will:
* Fetch GeoIP2 database and copy it to GCS
* Maintains state of version and only updates when new version is available

## Requirements ##
* GCS Bucket
* Some scheduler to run script periodicallly

## Usage ##
```
export GEO_LICENSE_KEY='license'
export GCS_BUCKET='bucket'

./geoupdate.py
```
