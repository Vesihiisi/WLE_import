#!/usr/bin/env python3
import argparse
import csv
import os
import importer_utils as utils
import wikidataStuff.wdqsLookup as lookup
from NatureArea import NatureArea
from PreviewTable import PreviewTable
from Uploader import Uploader

DATA_DIRECTORY = "data"
reserves_file = "NR_polygon.csv"
nationalparks_file = "NP_polygon.csv"
edit_summary = "test"


def get_data_from_csv_file(filename):
    """Load data from csv file into a list."""
    with open(filename, "r") as f_obj:
        reader = csv.DictReader(f_obj, delimiter=',')
        csv_data = list(reader)
    return csv_data


def remove_duplicate_entries(nature_dataset):
    """
    Remove duplicate entries from Nature Reserve file.

    In cases where a reserve occurs twice, it's because
    of different values of "BESLSTATUS". Whenever that happens,
    one of them is always "gällande". This is the one we keep,
    and the other one is removed.
    """
    results = []
    unique_ids = []
    for row in nature_dataset:
        n_id = row["NVRID"]
        if n_id in unique_ids:
            new_status = row["BESLSTATUS"]
            status_in_results = [x["BESLSTATUS"]
                                 for x in results if x["NVRID"] == n_id]
            if status_in_results[0] == "Gällande":
                pass
            elif new_status == "Gällande":
                utils.remove_dic_from_list_by_value(results, "NVRID", n_id)
                results.append(row)
        else:
            unique_ids.append(n_id)
            results.append(row)
    return results


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
    dataset = get_data_from_csv_file(filepath)
    no_duplicates = remove_duplicate_entries(dataset)
    return no_duplicates


def get_wd_items_using_prop(prop):
    """
    Get WD items that already have some value of a unique ID.

    Even if there are none before we start working,
    it's still useful to have in case an upload is interrupted
    and has to be restarted, or if we later want to enhance
    some items. When matching, these should take predecence
    over any hardcoded matching files.
    """
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
                    "svwp_to_nature_id_exact.json",
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
    existing_areas = get_wd_items_using_prop("P3613")
    area_data = load_nature_area_file(arguments["dataset"])
    data_files = load_mapping_files()
    if arguments["offset"]:
        print("Using offset: {}.".format(str(arguments["offset"])))
        area_data = area_data[arguments["offset"]:]
    if arguments["limit"]:
        print("Using limit: {}.".format(str(arguments["limit"])))
        area_data = area_data[:arguments["limit"]]
    for area in area_data:
        reserve = NatureArea(area, wikidata_site, data_files, existing_areas)
        if arguments["table"]:
            filename = "{}_{}.txt".format(arguments["dataset"],
                                          utils.get_current_timestamp())
            preview = PreviewTable(reserve)
            utils.append_line_to_file(preview.make_table(), filename)
        if arguments["upload"]:
            live = True if arguments["upload"] == "live" else False
            uploader = Uploader(reserve,
                                repo=wikidata_site,
                                live=live,
                                edit_summary=edit_summary)
            uploader.upload()


if __name__ == "__main__":
    arguments = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--upload", action='store')
    parser.add_argument("--table", action='store_true')
    parser.add_argument("--offset",
                        nargs='?',
                        type=int,
                        action='store')
    parser.add_argument("--limit",
                        nargs='?',
                        type=int,
                        action='store')
    args = parser.parse_args()
    main(args)
