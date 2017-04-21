#!/usr/bin/python
# -*- coding: utf-8  -*-
import datetime
import json
import re
import pywikibot

site_cache = {}


def load_json(filename):
    try:
        with open(filename) as f:
            try:
                return json.load(f)
            except ValueError:
                print("Failed to decode file {}.".format(filename))
    except OSError:
        print("File {} does not exist.".format(filename))


def string_is_q_item(text):
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
    return text[-1]


def last_char_is_vowel(text):
    return is_vowel(get_last_char(text))


def date_to_dict(datestring, dateformat):
    date_dict = {}
    date_obj = datetime.datetime.strptime(datestring, dateformat)
    date_dict["year"] = date_obj.year
    if "%m" in dateformat:
        date_dict["month"] = date_obj.month
    if "%d" in dateformat:
        date_dict["day"] = date_obj.day
    return date_dict


def tuple_is_coords(sometuple):
    result = False
    if isinstance(sometuple, tuple) and len(sometuple) == 2:
        if all(isinstance(x, float) for x in sometuple):
            result = True
    return result
