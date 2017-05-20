# -*- coding: utf-8 -*-
"""
An object that represent a Wikidata item.

This is a basic object used to construct
a Wikidata item. It contains the basic functions
to create statements, qualifiers and sources,
as well as labels and descriptions with specified
languages.

The purpose of it is to serve as a base for a
data-specific object that will turn some data
into Wikidata objects. It can then be uploaded
to Wikidata using the uploader script.
"""
from wikidataStuff.WikidataStuff import WikidataStuff as WDS
from wikidataStuff import helpers as helpers
import pywikibot

import importer_utils as utils

DATA_DIR = "data"


class WikidataItem(object):
    """Basic data object for upload to Wikidata."""

    def __init__(self, db_row_dict, repository, data_files, existing):
        """
        Initialize the data object.

        :param db_row_dict: raw data from the data source
        :param db_row_dict: Expected type: string
        :param repository: data repository (Wikidata site)
        :param repository: Expected type: site instance
        :param data_files: dict of various mapping files
        :param data_files: Expected type: dictionary
        :param existing: WD items that already have an unique id
        :param existing: Expected type: dictionary

        :return: nothing
        """
        self.repo = repository
        self.existing = existing
        self.wdstuff = WDS(self.repo)
        self.raw_data = db_row_dict
        self.props = data_files["properties"]
        self.items = data_files["items"]
        self.construct_wd_item()

        self.problem_report = {}

    def make_q_item(self, qnumber):
        """
        Create a regular Wikidata ItemPage.

        :param qnumber: Q-item that we want to get an ItemPage of
        :param qnumber: Expected type: string

        :return: an ItemPage for pywikibot
        """
        return self.wdstuff.QtoItemPage(qnumber)

    def make_pywikibot_item(self, value):
        """
        Create a statement in pywikibot-ready format.

        The statement can be either:
        * a string (value is string)
        * an item (value is Q-string)
        * an amount with or without unit (value is dic)

        :param value: the content of the item
        :param value: Expected type: it can be a string or
                      a dictionary, see above.

        :return: a pywikibot item of the type determined
                 by the input data, either ItemPage or Quantity
                 or string.
        """
        val_item = None
        if isinstance(value, list) and len(value) == 1:
            value = value[0]
        if utils.string_is_q_item(value):
            val_item = self.make_q_item(value)
        elif isinstance(value, dict) and 'quantity_value' in value:
            number = value['quantity_value']
            if 'unit' in value:
                unit = self.wdstuff.QtoItemPage(value["unit"])
            else:
                unit = None
            val_item = pywikibot.WbQuantity(
                amount=number, unit=unit, site=self.repo)
        elif isinstance(value, dict) and 'date_value' in value:
            date_dict = value["date_value"]
            val_item = pywikibot.WbTime(year=date_dict["year"],
                                        month=date_dict["month"],
                                        day=date_dict["day"])
        elif value == "novalue":
            #  raise NotImplementedError
            #  implement Error
            print("Status: novalue will be added here")
        else:
            val_item = value
        return val_item

    def make_statement(self, value):
        """
        Create a Wikidatastuff statement.

        :prop value: the content of the statement
        :prop value: Expected type: pywikibot item

        :return: a wikidatastuff statement
        """
        return self.wdstuff.Statement(value)

    def make_qualifier_applies_to(self, value):
        """
        Create a qualifier to a statement with type 'applies to part'.

        :param value: Q-item that this applies to
        :param value: Expected type: string

        :return: a wikidatastuff Qualifier
        """
        prop_item = self.props["applies_to_part"]
        target_item = self.wdstuff.QtoItemPage(value)
        return self.wdstuff.Qualifier(prop_item, target_item)

    def make_qualifier_startdate(self, value):
        """
        Create a qualifier to a statement with type 'start date'.

        :param value: date in the format "1999-09-31"
        :param value: Expected type: string

        :return: a wikidatastuff Qualifier
        """
        prop_item = self.props["start_time"]
        value_dic = utils.date_to_dict(value, "%Y-%m-%d")
        value_pwb = self.make_pywikibot_item({"date_value": value_dic})
        return self.wdstuff.Qualifier(prop_item, value_pwb)

    def add_statement(self, prop_name, value, quals=None, ref=None):
        """
        Add a statement to the data object.

        :param prop_name: P-item representing property
        :param prop_name: Expected type: string
        :param value: content of the statement
        :param value: Expected type: it can be a string representing
                      a Q-item or a dictionary of an amount
        :param quals: possibly qualifier items
        :param quals: Expected type: a wikidatastuff Qualifier item,
                      or a list of them
        :param ref: reference item
        :param ref: Expected type: a wikidatastuff Reference item

        :return: nothing
        """
        base = self.wd_item["statements"]
        prop = self.props[prop_name]
        if quals is None:
            quals = []
        wd_claim = self.make_pywikibot_item(value)
        statement = self.make_statement(wd_claim)
        for qual in helpers.listify(quals):
            statement.addQualifier(qual)
        base.append({"prop": prop,
                     "value": statement,
                     "ref": ref})

    def make_stated_in_ref(self,
                           value,
                           pub_date,
                           ref_url=None,
                           retrieved_date=None):
        """
        Make a reference object of type 'stated in'.

        :param value: Q-item where sth is stated
        :param value: Expected type: string
        :param pub_date: timestamp in format "1999-09-31"
        :param pub_date: Expected type: string
        :param ref_url: optionally a reference url
        :param ref_url: Expected type: string
        :param retrieved_date: timestamp in format "1999-09-31"
        :param retrieved_date: Expected type: string

        :return: a wikidatastuff Reference item
        """
        item_prop = self.props["stated_in"]
        published_prop = self.props["publication_date"]
        pub_date = utils.date_to_dict(pub_date, "%Y-%m-%d")
        timestamp = self.make_pywikibot_item({"date_value": pub_date})
        published_claim = self.wdstuff.make_simple_claim(
            published_prop, timestamp)
        source_item = self.wdstuff.QtoItemPage(value)
        source_claim = self.wdstuff.make_simple_claim(item_prop, source_item)
        if ref_url and retrieved_date:
            ref_url_prop = self.props["reference_url"]
            retrieved_date_prop = self.props["retrieved"]

            retrieved_date = utils.date_to_dict(retrieved_date, "%Y-%m-%d")
            retrieved_date = self.make_pywikibot_item(
                {"date_value": retrieved_date})

            ref_url_claim = self.wdstuff.make_simple_claim(
                ref_url_prop, ref_url)
            retrieved_on_claim = self.wdstuff.make_simple_claim(
                retrieved_date_prop, retrieved_date)

            ref = self.wdstuff.Reference(
                source_test=[source_claim, ref_url_claim],
                source_notest=[published_claim, retrieved_on_claim])
        else:
            ref = self.wdstuff.Reference(
                source_test=[source_claim],
                source_notest=published_claim
            )
        return ref

    def associate_wd_item(self, wd_item):
        """
        Associate the data object with a Wikidata item.

        :param wd_item: Q-item that shall be assigned to the
                        data object.
        :param wd_item: Expected type: string

        :return: nothing
        """
        if wd_item is not None:
            self.wd_item["wd-item"] = wd_item
            print("Associated WD item: ", wd_item)

    def add_label(self, language, text):
        """
        Add a label in a specific language.

        :param language: code of language, e.g. "fi"
        :param language: Expected type: string
        :param text: content of the label
        :param text: Expected type: string

        :return: nothing
        """
        base = self.wd_item["labels"]
        base.append({"language": language, "value": text})

    def add_description(self, language, text):
        """
        Add a description in a specific language.

        :param language: code of language, e.g. "fi"
        :param language: Expected type: string
        :param text: content of the description
        :param text: Expected type: string

        :return: nothing
        """
        base = self.wd_item["descriptions"]
        base.append({"language": language, "value": text})

    def construct_wd_item(self):
        """
        Create the empty structure of the data object.

        This creates self.wd_item -- a dict container
        of all the data content of the item.

        :return: nothing
        """
        self.wd_item = {}
        self.wd_item["upload"] = True
        self.wd_item["statements"] = []
        self.wd_item["labels"] = []
        self.wd_item["descriptions"] = []
        self.wd_item["wd-item"] = None
