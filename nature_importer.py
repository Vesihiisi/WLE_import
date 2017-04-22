#!/usr/bin/env python3
import argparse
import csv
import importer_utils as utils
import wikidataStuff.wdqsLookup as lookup
from NatureReserve import NatureReserve
from Uploader import Uploader

reserves_file = "data/NR_polygon.csv"


def get_data_from_csv_file(filename):
    with open(filename, "r") as f_obj:
        reader = csv.DictReader(f_obj, delimiter=',')
        csv_data = list(reader)
    return csv_data


def get_wd_items_using_prop(prop):
    items = {}
    print("WILL NOW DOWNLOAD WD ITEMS THAT USE " + prop)
    query = "SELECT DISTINCT ?item ?value  WHERE {?item p:" + \
        prop + "?statement. OPTIONAL { ?item wdt:" + prop + " ?value. }}"
    data = lookup.make_simple_wdqs_query(query, verbose=False)
    for x in data:
        key = lookup.sanitize_wdqs_result(x['item'])
        value = x['value']
        items[value] = key
    print("FOUND {} WD ITEMS WITH PROP {}".format(len(items), prop))
    return items


def main(arguments):
    """Process the arguments and fetch data according to them"""
    arguments = vars(arguments)
    upload = arguments["upload"]
    wikidata_site = utils.create_site_instance("wikidata", "wikidata")
    #  existing_areas = get_wd_items_using_prop("P3613")
    nr_data = get_data_from_csv_file(reserves_file)
    for area in nr_data:
        reserve = NatureReserve(area, wikidata_site)
        # print(reserve.raw_data["NAMN"])
        if upload:
            live = True if upload == "live" else False
            uploader = Uploader(reserve, repo=wikidata_site, live=live)
            uploader.upload()


if __name__ == "__main__":
    arguments = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action='store')
    args = parser.parse_args()
    main(args)
