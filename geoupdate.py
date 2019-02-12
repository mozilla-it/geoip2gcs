#!/bin/env python
from os.path import join as pjoin
import argparse
import json
import logging
import os
import re
import requests
import tarfile

from google.cloud import storage

logging.basicConfig(format='%(asctime)s - %(levelname)s %(message)s')

LICENSE_KEY = os.getenv('GEO_LICENSE_KEY')
GCS_BUCKET = os.getenv('GCS_BUCKET')

STATE_PATH = 'state'
DOWNLOAD_DIR = pjoin(os.getcwd(), 'download')
TMP_DIR = pjoin(os.getcwd(), 'tmp')


def setup():
    if not os.path.isdir(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)
    if not os.path.isdir(TMP_DIR):
        os.mkdir(TMP_DIR)

    if not LICENSE_KEY:
        logging.error('GEO_LICENSE_KEY environment variable is not set.')
        exit(1)


def update(product_name, product):

    if 'zip' in product['format']:
        raise NotImplementedError('zip archives are '
                                  'not supported: {0}.'.format(product_name))
    elif 'tar.gz' in product['format']:
        pass

    download_url = 'https://www.maxmind.com/app/geoip_download?' \
                   'edition_id={0}&suffix={1}&' \
                   'license_key={2}'.format(product['id'],
                                            product['format'], LICENSE_KEY)

    version = get_latest_version(download_url)

    if check_version(product_name, version):
        geo_file = '{0}-{1}.{2}'.format(product_name,
                                        version, product['format'])
        downloaded_file = download(download_url, geo_file)
        extract_and_upload(downloaded_file, product_name, version)

        os.unlink(downloaded_file)
        write_version(product_name, version)
        return True
    else:
        return False


def extract_and_upload(filename, product_name, version):
    extract_file = '{0}_{1}/{0}.mmdb'.format(product_name, version)
    with tarfile.open(filename, 'r:gz') as tf:
        tf.extract(extract_file, path=TMP_DIR)

    source_file = '{}/{}'.format(TMP_DIR, extract_file)
    dest_obj_key = '{0}/{1}/{0}.mmdb'.format(product_name, version)
    upload_blob(source_file, dest_obj_key)


def upload_blob(source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(GCS_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    logging.info('File {} uploaded to {}.'.format(
        source_file_name,
        destination_blob_name))


# get latest version based on filename
def get_latest_version(url):
    # use head request so we don't have to download the whole file
    logging.debug(url)
    r = requests.head(url)
    filename_header = r.headers['content-disposition']
    m = re.search('^\w+\W\s\w+=[\W\w\d]+_(\d+)', filename_header)
    return m.group(1)


def download(url, filename):
    download_file = pjoin(DOWNLOAD_DIR, filename)
    with open(download_file, 'wb') as fp:
        r = requests.get(url, stream=True)

        for block in r.iter_content(1024):
            if not block:
                break
            fp.write(block)

    logging.info('Downloaded file to {0}'.format(download_file))
    return download_file


def write_version(product_name, version):
    current_version_path = pjoin(STATE_PATH, product_name)

    client = storage.Client()
    bucket = client.get_bucket(GCS_BUCKET)
    current_version_file = bucket.blob(current_version_path)
    current_version_file.upload_from_string(version)


def get_current_state_version(product_name):
    current_version_path = pjoin(STATE_PATH, product_name)

    client = storage.Client()
    bucket = client.get_bucket(GCS_BUCKET)
    current_version_file = bucket.blob(current_version_path)
    if current_version_file.exists():
        return current_version_file.download_as_string().decode('utf-8')
    else:
        return None


# returns True if file is not current
def check_version(product_name, version):
    current_version = get_current_state_version(product_name)
    if current_version:
        logging.info('%s, %s' % (current_version, version))
        if current_version == version:
            logging.info('{0} is up to date. Version: '
                         '{1}'.format(product_name, current_version))
            return False
        elif current_version < version:
            logging.info('New version found for '
                         '{0}: {1}'.format(product_name, version))
            return True
        else:
            logging.info('Could not figure out version.')
            exit(1)
    else:
        logging.info('No version file found for '
                     'product {0}'.format(product_name))
        return True


def main():
    update_results = []
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--products",
                        default="products.json")

    args = parser.parse_args()

    with open(args.products) as f:
        PRODUCTS = json.load(f)

    setup()
    for k, v in PRODUCTS.items():
        update_results.append(update(k, v))


if __name__ == '__main__':
    main()
