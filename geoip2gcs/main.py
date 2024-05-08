import json

import click
import functions_framework
from flask import Request, abort
from pydantic import BaseModel

from . import logging
from .classes import GeoIPFile


@functions_framework.http
def webhook(request: Request):
    if not request.is_json:
        abort(400)

    data = request.get_json()

    edition_id = data.get("edition_id", None)
    suffix = data.get("suffix", None)

    if edition_id and suffix:
        g = GeoIPFile(edition_id=edition_id, suffix=suffix)
        r = g.update(do_update=data.get("force_update", False))

        return {
            "edition_id": edition_id,
            "updated": r,
            "latest_version": g.latest_version,
        }

    abort(400)


@click.command()
@click.argument("products", type=click.File("r"), default="products.json")
@click.option("--force", is_flag=True, default=False)
def cli(products, force):
    PRODUCTS = json.load(products)

    for k, v in PRODUCTS.items():
        g = GeoIPFile(edition_id=v["id"], suffix=v["format"])
        result = g.update(do_update=force)

        if result:
            print(f"updated {g.edition_id}")
