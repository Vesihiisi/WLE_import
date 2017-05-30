# -*- coding: utf-8 -*-
"""
A script to gather Wikidata IDs of Swedish nature reserves.

The input is a Petscan dump from svwp category "Naturreservat i Sverige",
two levels deep (naturreservat -> nr i <län> -> nr i <kommun>):
https://petscan.wmflabs.org/?psid=914993

Then it's compared to NR_polygon.csv the following way:

* The municipalities of each wp article are extracted
* If a reserve in the csv file has exactly the same set of municipalities,
as well as an identical or very similar name (Foo / Foo natturreservat),
it's added to the exact matches file: svwp_to_nature_id_exact.json
* If more than one match is found, they're added to
svwp_to_nature_id_multiple.json, which can be reviewed manually.
* If there's no match, the svwp article is added to
svwp_to_nature_id_none, which can be reviewed manually.

When running, if an svwp article with no WD item is encountered,
it is created automatically. Thus, all the articles in the mapping
files have corresponding WD items.

CAVEATS
=======

Sometimes a reserve described in one article has two
separate nature IDs, when it spans across several
counties, eg. Sandsjöbacka naturreservat is two separate reserves
in VG and Halland. How to handle those?

In a considerable number of cases, the svwp article describes
both a natural feature (island, lake, valley) and a reserve.
Because of that, its WD item can have its P31 set to this
natural feature. This script collects all WD items associated
with articles, without checking the P31, this check should probably
be done as part of the actual upload.
"""
import pywikibot

import importer_utils as utils

reserves_file = "petscan_naturreservat.json"
reserves_source = "NR_polygon.csv"

municip_cache_global = {}


def read_reserve_csv():
    """
    Load source data about nature reserves from csv file.

    Since we don't need all the data, only the name, nature ID,
    protection status and municipalities are extracted.
    """
    reserves = []
    filepath = utils.get_file_from_subdir("data", reserves_source)
    reserves_raw = utils.get_data_from_csv_file(filepath)
    for area in reserves_raw:
        reserve = {}
        reserve["name"] = area["NAMN"]
        reserve["municipalities"] = area["KOMMUN"].split(", ")
        reserve["nature_id"] = area["NVRID"]
        reserve["status"] = area["BESLSTATUS"]
        reserves.append(reserve)
    return reserves


def read_wp_nr_list():
    """Load the content of petscan list of nature reserves."""
    filepath = utils.get_file_from_subdir("data", reserves_file)
    content = utils.load_json(filepath)
    return content["*"][0]["a"]["*"]


def get_municipalities(title):
    """
    Extract the municipalities from svwp article of nature reserve.

    Get the names of categories to which the article
    belongs, and extract the names of municipalities
    from them.
    """
    municipalities = []
    site = pywikibot.Site("sv", "wikipedia")
    page = pywikibot.Page(site, title)
    for cat in page.categories():
        cat_title = cat.titleWithoutNamespace()
        if cat_title not in municip_cache_global:
            possible_m = utils.extract_municipality_name(cat_title)
            municip_cache_global[cat_title] = possible_m
        if municip_cache_global[cat_title] is not None:
                municipalities.append(municip_cache_global[cat_title])
    return municipalities


def process_wp_reserves():
    """
    Process a Petscan-generated list of nature reserves on svwp.

    Attempt to find matches in the source file
    and save them to appropriate report depending
    on the reliability of the match (one match, multiple matches,
    zero matches).
    The whole updated report is dumped to file immediately
    after every lookup rather than after the finished run,
    so that the current result can be peeked into
    before the processing is done.
    """
    results_file_exact = "svwp_to_nature_id_exact.json"
    results_file_none = "svwp_to_nature_id_none.json"
    results_file_multiple = "svwp_to_nature_id_multiple.json"
    results = []
    results_none = []
    results_multiple = []
    reserves_on_wp = read_wp_nr_list()
    article_count = len(reserves_on_wp)
    reserves_source = read_reserve_csv()
    print("Processing {} svwp articles.".format(article_count))
    counter = 0
    for article_title in reserves_on_wp:
        if (not article_title.startswith("Lista") and
                "nationalpark" not in article_title.lower()):
            counter += 1
            if counter % 10 == 0:
                print("Processed {}/{}...".format(counter, article_count))
            guesses = find_wp_reserve_in_data_file(
                article_title, reserves_source)
            if len(guesses) == 1:
                entry = {}
                entry["wp_article"] = article_title
                entry["source_name"] = guesses[0]["name"]
                entry["nature_id"] = guesses[0]["nature_id"]
                entry["item"] = utils.q_from_wikipedia("sv", article_title)
                results.append(entry)
                utils.json_to_file(results_file_exact, results)
            elif len(guesses) > 1:
                entry = {}
                entry["wp_article"] = article_title
                nature_ids = []
                for row in guesses:
                    nature_ids.append(row["nature_id"])
                entry["nature_id"] = nature_ids
                results_multiple.append(entry)
                utils.json_to_file(results_file_multiple, results_multiple)
            else:
                entry = {}
                entry["wp_article"] = article_title
                entry["nature_id"] = ""
                results_none.append(entry)
                utils.json_to_file(results_file_none, results_none)


def find_wp_reserve_in_data_file(article_title, reserves_source):
    """
    Taking an article title on svwp, make an attempt
    to match it to a nature ID in the source file.

    The output is a list of possible matches, containing either
    zero, one or multiple dictionaries that consist of the name,
    ID and municipalities of the reserve in the source file, eg.:

    [{'nature_id': '2004578', 'municipalities': ['Örnsköldsvik'], 'name': 'Granliden'}]

    Notes on matching:

    * 100% kommun match (the wp article and the entry in the source file
    have exactly the same set of municipalities), and either:
        * 100% name match
        * source file name starts the same way as wp name,
        e.g. source: "Foo", wp: "Foo naturreservat"
        * wp name starts the same way as source name,
        e.g. source: "Foo naturreservat", wp: "Foo"

    TODO:
    * Don't require 100% kommun match? Have a look at list
    of no-matches and see how common that is. Sometimes if the
    reserve stretches across many kommuner, the
    wp article is not categorized in all of them.
    * Look through the multiple matches file and figure out
    what's going on in there.
    * Look through the zero matches file. Looks like there are
    wp articles categorized as naturreservat that are missing
    in the source file (even with similar looking name).
    """
    guesses = []
    article_title = article_title.replace("_", " ")
    municipalities = get_municipalities(article_title)
    if municipalities:
        guesses = [x for x in
                   reserves_source if
                   (x["name"] == article_title or x["name"].startswith(
                       article_title) or
                    article_title.startswith(x["name"])) and
                   x["municipalities"] == municipalities and
                   x["status"] == "Gällande"]
    return guesses


if __name__ == "__main__":
    process_wp_reserves()
