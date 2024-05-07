import pathlib
import tempfile

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # enable verbose logging
    debug: bool = False

    tmp_dir: pathlib.Path = pathlib.Path(tempfile.gettempdir()) / "geoip2gcs_tmp"
    downloads_dir: pathlib.Path = (
        pathlib.Path(tempfile.gettempdir()) / "geoip2gcs_downloads"
    )

    # maxmind settings
    maxmind_base_url: str = "https://download.maxmind.com/app/geoip_download"
    maxmind_license_key: str

    # GCS settings
    gcs_bucket: str
