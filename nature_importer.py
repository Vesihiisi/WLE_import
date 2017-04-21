#!/usr/bin/env python3
import csv
from NatureReserve import NatureReserve
import importer_utils as utils

reserves_file = "data/NR_polygon.csv"


def csv_reader(file_obj):
    wikidata_site = utils.create_site_instance("wikidata", "wikidata")
    reader = csv.DictReader(file_obj, delimiter=',')
    for row in reader:
        reserve = NatureReserve(row, wikidata_site)


if __name__ == "__main__":
    with open(reserves_file, "r") as f_obj:
        csv_reader(f_obj)
