#!/usr/bin/python
# -*- coding: utf-8  -*-
import datetime
import json
import re
import pywikibot
import os
from wikidataStuff.WikidataStuff import WikidataStuff as wds

site_cache = {}

DATA_DIRECTORY = "data"


def load_json(filename):
    try:
        with open(filename) as f:
            try:
                return json.load(f)
            except ValueError:
                print("Failed to decode file {}.".format(filename))
    except OSError:
        print("File {} does not exist.".format(filename))


def json_to_file(filename, json_content):
    with open(filename, 'w') as f:
        json.dump(json_content, f, sort_keys=True,
                  indent=4,
                  ensure_ascii=False,
                  default=datetime_convert)


def append_line_to_file(text, filename):
    with open(filename, 'a') as f:
        f.write(text + "\n")


def get_current_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')


def string_is_q_item(text):
    """Check if a string looks like a WD ID."""
    pattern = re.compile("^Q[0-9]+$", re.I)
    try:
        m = pattern.match(text)
    except TypeError:
        return False
    if m:
        return True
    else:
        return False


def datetime_convert(dt_object):
    if isinstance(dt_object, datetime.datetime):
        return dt_object.__str__()


def wd_template(template_type, value):
    return "{{" + template_type + "|" + value + "}}"


def dict_to_iso_date(date_dict):
    """
    Convert pywikiboty-style date dictionary
    to ISO string ("2002-10-23").

    @param date_dict: dictionary like
    {"year" : 2002, "month" : 10, "day" : 23}
    """
    iso_date = ""
    if "year" in date_dict:
        iso_date += str(date_dict["year"])
    if "month" in date_dict:
        iso_date += "-" + str(date_dict["month"])
    if "day" in date_dict:
        iso_date += "-" + str(date_dict["day"])
    return iso_date


def create_site_instance(language, family):
    """Create an instance of a Wiki site (convenience function)."""
    site_key = (language, family)
    site = site_cache.get(site_key)
    if not site:
        site = pywikibot.Site(language, family)
        site_cache[site_key] = site
    return site


def is_vowel(char):
    vowels = "auoiyéeöåäáæø"
    if char.lower() in vowels:
        return True
    else:
        return False


def get_last_char(text):
    """Return the last character of string."""
    return text[-1]


def last_char_is_vowel(text):
    """Check if last char of string is vowel."""
    return is_vowel(get_last_char(text))


def date_to_dict(datestring, dateformat):
    """Convert a date to a pwb-friendly dictionary."""
    date_dict = {}
    date_obj = datetime.datetime.strptime(datestring, dateformat)
    date_dict["year"] = date_obj.year
    if "%m" in dateformat:
        date_dict["month"] = date_obj.month
    if "%d" in dateformat:
        date_dict["day"] = date_obj.day
    return date_dict


def hectares_to_km(hectares):
    """Convert a value in hectares to km."""
    one_hectare_in_km = 0.01
    return one_hectare_in_km * float(hectares)


def extract_municipality_name(category_name):
    """
    Extract base municipality name from category name.

    Since we can't guess whether an "s" ending the first
    part of the name belongs to the town name or is
    a genitive ending (and should be dropped), we have to
    compare against (English) list of known municipalities:

    Halmstads kommun -> Halmstad
    Kramfors kommun -> Kramfors
    Pajala kommun -> Pajala

    Known caveats:
    * Reserves in Gotland are categorized in "Gotlands län"

    :param category_name: Category of Swedish nature reserves,
                          like "Naturreservat i Foo kommun"
    """
    legit_municipalities = load_json(
        os.path.join(DATA_DIRECTORY, "municipalities.json"))
    m = re.search('(\w?)[N|n]aturreservat i (.+?) [kommun|län]', category_name)
    if m:
        municipality = m.group(2)
        municipality_clean = [x["en"].split(" ")[0] for
                              x in legit_municipalities if
                              x["sv"] == municipality + " kommun"]
        if municipality_clean:
            municipality = municipality_clean[0]
            if municipality == "Gothenburg":
                municipality = "Göteborg"
            return municipality


def q_from_wikipedia(language, page_title):
    """
    Get the ID of the WD item linked to a wp page.
    If the page has no item and is in the article
    namespace, create an item for it.
    """
    wp_site = pywikibot.Site(language, "wikipedia")
    page = pywikibot.Page(wp_site, page_title)
    summary = "Creating item for {} on {}wp."
    summary = summary.format(page_title, language)
    wd_repo = create_site_instance("wikidata", "wikidata")
    wdstuff = wds(wd_repo, edit_summary=summary)
    if page.exists():
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        try:
            item = pywikibot.ItemPage.fromPage(page)
        except pywikibot.NoPage:
            if page.namespace() != 0:  # main namespace
                return
            item = wdstuff.make_new_item_from_page(page, summary)
        return item.getID()


def remove_dic_from_list_by_value(diclist, key, value):
    """
    Remove a dictionary from a list of dictionaries by certain value.

    :param diclist: List of dictionaries
    :param key: The key whose value to check
    :param value: The value of that key that should cause removal
                  of dictionary from list.
    """
    return [x for x in diclist if not (value == x.get(key))]
