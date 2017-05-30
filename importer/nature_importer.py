#!/usr/bin/env python3
import argparse
import os

import wikidataStuff.wdqsLookup as lookup

from NatureArea import NatureArea
from PreviewTable import PreviewTable
from Uploader import Uploader
import importer_utils as utils

reserves_file = "NR_polygon.csv"
nationalparks_file = "NP_polygon.csv"
edit_summary = "test"


def get_status(row):
    """Get the validity status of reserve."""
    return row["BESLSTATUS"]


def get_name(row):
    """Get the name of reserve."""
    return row["NAMN"]


def get_nature_id(row):
    """Get the nature ID of reserve."""
    return row["NVRID"]


def get_row_by_nature_id(nature_id, nature_dataset):
    """Get the row(s) in source file with certain ID."""
    return [x for x in nature_dataset if get_nature_id(x) == nature_id]


def remove_invalid_entries(nature_dataset):
    """
    Remove entries of absolutely invalid reserves from dataset.

    Absolutely invalid reserves are those whose status
    is not "Gällande" and there is no other entry
    in the dataset with the particular ID (which could change
    the status to valid)-
    """
    new_dataset = []
    for row in nature_dataset:
        n_id = get_nature_id(row)
        status = get_status(row)
        if status != "Gällande":
            all_rows_with_this_id = get_row_by_nature_id(
                n_id, nature_dataset)
            if len(all_rows_with_this_id) == 1:
                pass
            else:
                new_dataset.append(row)
        else:
            new_dataset.append(row)
    return new_dataset


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
        n_id = get_nature_id(row)
        if n_id in unique_ids:
            new_status = row["BESLSTATUS"]
            if new_status == "Gällande":
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
        filepath = utils.get_file_from_subdir("data", reserves_file)
    elif which_one == "np":
        filepath = utils.get_file_from_subdir("data", nationalparks_file)
    print("Loading dataset: {}".format(filepath))
    dataset = utils.get_data_from_csv_file(filepath)
    print("Source dataset: {} rows.".format(str(len(dataset))))
    no_invalid = remove_invalid_entries(dataset)
    no_duplicates = remove_duplicate_entries(no_invalid)
    print("Cleaned up duplicates and invalid items: {} rows left.".format(
        str(len(no_duplicates))))
    return no_duplicates


def get_wd_items_using_prop(prop):
    """
    Get WD items that already have some value of a unique ID.

    Even if there are none before we start working,
    it's still useful to have in case an upload is interrupted
    and has to be restarted, or if we later want to enhance
    some items. When matching, these should take predecence
    over any hardcoded matching files.

    The output is a dictionary of ID's and items
    that looks like this:
    {'4420': 'Q28936211', '2041': 'Q28933898'}
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
        filename_base = os.path.splitext(filename)[0]
        file_content = utils.load_json(
            utils.get_file_from_subdir("data", filename))
        mapping_files[filename_base] = file_content
    return mapping_files


def main(arguments):
    """Process the arguments and fetch data according to them"""
    arguments = vars(arguments)
    current_time = utils.get_current_timestamp()
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
            filename = "{}_{}.txt".format(arguments["dataset"], current_time)
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
