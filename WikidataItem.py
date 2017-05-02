# -*- coding: utf-8 -*-
import json
import importer_utils as utils
from wikidataStuff.WikidataStuff import WikidataStuff as WDS
import pywikibot


DATA_DIR = "data"


class WikidataItem(object):
    """Basic data object for upload to Wikidata."""

    def print_wd_to_table(self):
        """Generate a wikitext preview table of the data item."""
        table = ""
        labels = self.wd_item["labels"]
        descriptions = self.wd_item["descriptions"]
        aliases = self.wd_item["aliases"]
        table = table + "'''Labels'''\n\n"
        for l in labels:
            table = table + "* '''" + l + "''': " + labels[l] + "\n\n"
        table = table + "'''Descriptions'''\n\n"
        for d in descriptions:
            table = table + "* '''" + d + "''': " + descriptions[d] + "\n\n"
        table = table + "'''Aliases'''\n\n"
        for a in aliases:
            for single_alias in aliases[a]:
                table = table + "* '''" + a + "''': " + single_alias + "\n\n"
        if self.wd_item["wd-item"] is not None:
            table = table + "'''Possible item''': " + \
                utils.wd_template("Q", self.wd_item["wd-item"]) + "\n\n"
        else:
            table = table + "'''Possible item''': \n\n"
        table_head = "{| class='wikitable'\n|-\n! Property\n! Value\n! Qualifiers\n! References\n"
        table = table + table_head
        statements = self.wd_item["statements"]
        for statement in statements:
            claims = statements[statement]
            for claim in claims:
                value = claim["value"]
                value_to_print = ""
                if utils.string_is_q_item(value):
                    value = utils.wd_template("Q", value)
                    value_to_print += str(value)
                elif "quantity_value" in value:
                    quantity = str(value["quantity_value"])
                    if "unit" in value:
                        value_to_print += "{quantity} {unit}".format(
                            quantity=quantity,
                            unit=utils.wd_template("Q", value["unit"]))
                    else:
                        value_to_print += quantity
                elif "time_value" in value:
                    value_to_print += utils.dict_to_iso_date(
                        value["time_value"])
                else:
                    value_to_print += str(value)
                quals = claim["quals"]
                refs = claim["refs"]
                if len(quals) == 0:
                    qual_to_print = ""
                else:
                    for q in quals:
                        qual_to_print = utils.wd_template(
                            "P", q) + " : " + json.dumps(quals[q])
                if len(refs) == 0:
                    ref_to_print = ""
                else:
                    for r in refs:
                        ref_to_print = json.dumps(
                            r, default=utils.datetime_convert)
                table = table + "|-\n"
                table = table + "| " + utils.wd_template("P", statement) + "\n"
                table = table + "| " + value_to_print + "\n"
                table = table + "| " + qual_to_print + "\n"
                table = table + "| " + ref_to_print + "\n"
        table = table + "|}\n"
        table = table + "----------\n"
        return table

    def make_q_item(self, qnumber):
        """Create a regular Item."""
        return self.wdstuff.QtoItemPage(qnumber)

    def make_pywikibot_item(self, value, prop=None):
        val_item = None
        if type(value) is list and len(value) == 1:
            value = value[0]
        if utils.string_is_q_item(value):
            val_item = self.make_q_item(value)
        elif isinstance(value, dict) and 'quantity_value' in value:
            number = value['quantity_value']
            if 'unit' in value:
                unit = self.make_q_item(value['unit'])
            else:
                unit = None
            val_item = pywikibot.WbQuantity(
                amount=number, unit=unit, site=self.repo)
        elif value == "novalue":
            #  to do - no_value
            print("")
        else:
            val_item = value
        return val_item

    def make_statement(self, value):
        return self.wdstuff.Statement(value)

    def make_qualifier_applies_to(self, value):
        prop_item = self.props["applies_to_part"]
        target_item = self.wdstuff.QtoItemPage(value)
        return self.wdstuff.Qualifier(prop_item, target_item)

    def make_qualifier_startdate(self, value):
        prop_item = self.props["start_time"]
        value_dic = utils.date_to_dict(value, "%Y-%m-%d")
        value_pwb = pywikibot.WbTime(year=value_dic["year"], month=value_dic[
                                     "month"], day=value_dic["day"])
        return self.wdstuff.Qualifier(prop_item, value_pwb)

    def add_statement(self, prop_name, value, quals=None, ref=None):
        """
        """
        base = self.wd_item["statements"]
        prop = self.props[prop_name]
        wd_claim = self.make_pywikibot_item(value, prop)
        statement = self.make_statement(wd_claim)
        base.append({"prop": prop,
                     "value": statement,
                     "quals": quals,
                     "ref": ref})

    def make_stated_in_ref(self, value, pub_date):
        item_prop = self.props["stated_in"]
        published_prop = self.props["publication_date"]
        pub_date = utils.date_to_dict(pub_date, "%Y-%m-%d")
        timestamp = pywikibot.WbTime(year=pub_date["year"], month=pub_date[
                                     "month"], day=pub_date["day"])
        source_item = self.wdstuff.QtoItemPage(value)
        source_claim = self.wdstuff.make_simple_claim(item_prop, source_item)
        ref = self.wdstuff.Reference(
            source_test=[source_claim],
            source_notest=self.wdstuff.make_simple_claim(
                published_prop, timestamp)
        )
        return ref

    def associate_wd_item(self, wd_item):
        """Associate the data object with a Wikidata item."""
        if wd_item is not None:
            self.wd_item["wd-item"] = wd_item
            print("Associated WD item: ", wd_item)

    def add_label(self, language, text):
        """
        Add a label in a specific language.

        :param language: code of language, e.g. "fi"
        :param text: content of the label
        """
        base = self.wd_item["labels"]
        base.append({"language": language, "value": text})

    def add_description(self, language, text):
        """
        Add a description in a specific language.

        :param language: code of language, e.g. "fi"
        :param text: content of the description
        """
        base = self.wd_item["descriptions"]
        base.append({"language": language, "value": text})

    def construct_wd_item(self):
        """Create the empty structure of the data object."""
        self.wd_item = {}
        self.wd_item["upload"] = True
        self.wd_item["statements"] = []
        self.wd_item["labels"] = []
        self.wd_item["descriptions"] = []
        self.wd_item["wd-item"] = None

    def __init__(self, db_row_dict, repository, data_files):
        """
        Initialize the data object.

        :param db_row_dict: raw data from the database
        :param repository: data repository (Wikidata site)
        """
        self.repo = repository
        self.wdstuff = WDS(self.repo)
        self.raw_data = db_row_dict
        self.props = data_files["properties"]
        self.items = data_files["items"]
        self.municipalities = data_files["municipalities"]
        self.iucn = data_files["iucn_categories"]
        self.forvaltare = data_files["forvaltare"]
        self.glossary = data_files["glossary"]
        self.construct_wd_item()

        self.problem_report = {}
