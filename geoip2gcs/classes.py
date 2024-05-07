import logging
import re
import shutil
import sys

import requests
from google.cloud import storage
from pydantic import BaseModel, ValidationError

from .config import Settings


class GeoIPFile(BaseModel):
    # attributes
    edition_id: str
    suffix: str
    current_version: str | None = None
    latest_version: str | None = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # logger
        self.__logger = logging.getLogger("geoip2gcs")

        # settings
        self.__settings = Settings()

        # GCS
        self.__storage_client = storage.Client()
        self.__gcs_bucket = self.__storage_client.bucket(self.__settings.gcs_bucket)

        # session
        self.__session = requests.Session()

        # set versions
        self.get_state()
        self.get_latest_version()

    def clean_tmpfiles(self):
        for workdir in (self.__settings.tmp_dir, self.__settings.downloads_dir):
            for p in workdir.glob("*"):
                if p.is_file():
                    p.unlink()

                elif p.is_dir():
                    shutil.rmtree(p)

    def update(self, do_update=False):
        if not self.current_version or self.current_version < self.latest_version:
            do_update = True

        if do_update:
            self.__logger.info(f"updating {self.edition_id}")

            self.download()
            self.extract()
            self.upload()
            self.write_state()
            self.clean_tmpfiles()

            return True

        self.__logger.info(f"{self.edition_id} is up-to-date.")

        return False

    def get_state(self):
        blob = self.__gcs_bucket.blob(f"state/{self.edition_id}")

        if blob.exists():
            self.current_version = blob.download_as_string().decode()

        self.__logger.debug(
            f"{self.edition_id}'s current version is {self.current_version}"
        )

        return self.current_version

    def write_state(self):
        blob = self.__gcs_bucket.blob(f"state/{self.edition_id}")
        blob.upload_from_string(self.latest_version)

    def upload_blob(self, src, dst):
        blob = self.__gcs_bucket.blob(dst)
        blob.upload_from_filename(src)

        self.__logger.debug(f"uploaded {src.name} to {dst}")

    def __make_request(self, method):
        req = requests.Request(
            method,
            f"{self.__settings.maxmind_base_url}",
            params={
                "edition_id": self.edition_id,
                "suffix": self.suffix,
                "license_key": self.__settings.maxmind_license_key,
            },
        )

        prepped = req.prepare()

        return prepped

    def get_latest_version(self):
        response = self.__session.send(
            self.__make_request("HEAD"),
        )

        match = re.search(
            r"^\w+\W\s\w+=[\W\w\d]+_(?P<version>\d+)",
            response.headers["content-disposition"],
        )

        self.latest_version = match.group("version")

        self.__logger.debug(
            f"{self.edition_id}'s latest version is {self.latest_version}"
        )

        return self.latest_version

    def download(self):
        if not self.__settings.downloads_dir.exists():
            self.__settings.downloads_dir.mkdir()

        download_file = (
            self.__settings.downloads_dir
            / f"{self.edition_id}_{self.latest_version}.{self.suffix}"
        )

        response = self.__session.send(
            self.__make_request("GET"),
            stream=True,
        )

        with download_file.open("wb") as fh:
            for chunk in response.iter_content(1024):
                if not chunk:
                    break

                fh.write(chunk)

        self.__logger.debug(f"downloaded {download_file.name}")

    def extract(self):
        if not self.__settings.tmp_dir.exists():
            self.__settings.tmp_dir.mkdir()

        shutil.unpack_archive(
            self.__settings.downloads_dir
            / f"{self.edition_id}_{self.latest_version}.{self.suffix}",
            self.__settings.tmp_dir / f"{self.edition_id}",
        )

    def upload(self):
        if self.suffix == "zip":
            for file in (self.__settings.tmp_dir / f"{self.edition_id}").glob(
                "**/*.csv"
            ):
                self.upload_blob(
                    file, f"{self.edition_id}/{self.latest_version}/{file.name}"
                )

        if self.suffix == "tar.gz":
            for file in (self.__settings.tmp_dir / f"{self.edition_id}").glob(
                "**/*.mmdb"
            ):
                self.upload_blob(
                    file, f"{self.edition_id}/{self.latest_version}/{file.name}"
                )
