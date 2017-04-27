#!/usr/bin/env python3
import argparse
import csv
import os
import importer_utils as utils
import wikidataStuff.wdqsLookup as lookup
from NatureArea import NatureArea
from Uploader import Uploader

DATA_DIRECTORY = "data"
reserves_file = "NR_polygon.csv"
nationalparks_file = "NP_polygon.csv"


def get_data_from_csv_file(filename):
    """Load data from csv file into a list."""
    with open(filename, "r") as f_obj:
        reader = csv.DictReader(f_obj, delimiter=',')
        csv_data = list(reader)
    return csv_data


def load_nature_area_file(which_one):
    """
    Load source file with nature area data.

    :param which_one: nr for reserves or np for parks.
    """
    if which_one == "nr":
        filepath = os.path.join(DATA_DIRECTORY, reserves_file)
    elif which_one == "np":
        filepath = os.path.join(DATA_DIRECTORY, nationalparks_file)
    print("Loading dataset: {}".format(filepath))
    return get_data_from_csv_file(filepath)


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


def load_mapping_files():
    """Load the files with mappings of various values."""
    mapping_files = {}
    files_to_get = ["glossary.json",
                    "forvaltare.json",
                    "iucn_categories.json",
                    "mapping_nationalparks.json",
                    "municipalities.json",
                    "items.json",
                    "properties.json"]
    for filename in files_to_get:
        filename_base = os.path.splitext(os.path.basename(filename))[0]
        file_content = utils.load_json(os.path.join(DATA_DIRECTORY, filename))
        mapping_files[filename_base] = file_content
    return mapping_files


def main(arguments):
    """Process the arguments and fetch data according to them"""
    arguments = vars(arguments)
    wikidata_site = utils.create_site_instance("wikidata", "wikidata")
    #  existing_areas = get_wd_items_using_prop("P3613")
    area_data = load_nature_area_file(arguments["dataset"])
    data_files = load_mapping_files()
    for area in area_data:
        reserve = NatureArea(area, wikidata_site, data_files)
        #  print(reserve.raw_data["NAMN"])
        if arguments["upload"]:
            live = True if arguments["upload"] == "live" else False
            uploader = Uploader(reserve, repo=wikidata_site, live=live)
            uploader.upload()


if __name__ == "__main__":
    arguments = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--upload", action='store')
    args = parser.parse_args()
    main(args)
