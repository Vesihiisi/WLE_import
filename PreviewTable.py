# -*- coding: utf-8 -*-
"""
An object to generate preview tables of Wikidata-ready objects.

The preview includes:
* labels in all languages
* descriptions in all languages
* matched Wikidata item, if applicable
* claims, consisting of:
    * property
    * value
    * qualifier
    * reference

Example:
https://www.wikidata.org/w/index.php?title=User:Alicia_Fagerving_(WMSE)/sandbox3&oldid=480712165
"""
import pywikibot
import importer_utils as utils


class PreviewTable(object):
    """Generate preview for a WikidataItem object."""

    def itis_to_string(self, itis):
        """Represent the target of the statement in readable form."""
        if isinstance(itis, pywikibot.page.ItemPage):
            target_item = utils.wd_template("Q", itis.getID())
        elif isinstance(itis, pywikibot.WbQuantity):
            amount = str(itis.amount)
            unit = utils.wd_template("Q", itis.unit.split("/")[-1])
            target_item = "{} {}".format(amount, unit)
        elif isinstance(itis, pywikibot.WbTime):
            target_item = itis.toTimestr()
        else:
            target_item = str(itis)
        return target_item

    def print_raw_data(self):
        """Dump the data dictionary as string."""
        return "<pre>" + str(self.raw_data) + "</pre>\n"

    def make_text_bold(self, text):
        """Surround text with Wiki-tags that make it bold."""
        return "'''{}'''".format(text)

    def make_table(self):
        """Generate a wikitext preview table of the data item."""
        table = self.print_raw_data()
        labels = self.wd_item["labels"]
        descriptions = self.wd_item["descriptions"]
        table += self.make_text_bold("Labels") + "\n\n"
        for label in labels:
            language = label["language"]
            text = label["value"]
            table += "* {} : {}\n\n".format(
                self.make_text_bold(language), text)
        table += self.make_text_bold("Descriptions") + "\n\n"
        for desc in descriptions:
            language = desc["language"]
            text = desc["value"]
            table += "* {} : {}\n\n".format(
                self.make_text_bold(language), text)
        if self.wd_item["wd-item"] is not None:
            possible_item = utils.wd_template("Q", self.wd_item["wd-item"])
            table += "{} : {}\n\n".format(
                self.make_text_bold("Possible item"), possible_item)
        else:
            table += "{} : \n\n".format(self.make_text_bold("Possible item"))
        table_head = "{| class='wikitable'\n|-\n! Property\n! Value\n! Qualifiers\n! References\n"
        table += table_head
        statements = self.wd_item["statements"]
        for statement in statements:
            prop = statement["prop"]
            value_content = statement["value"].itis
            target_item = self.itis_to_string(value_content)
            value_to_print = ""
            value_to_print += target_item
            quals = statement["quals"]
            qual_to_print = ""
            if quals:
                for qual in quals:
                    q_prop = utils.wd_template("P", qual.prop)
                    content = self.itis_to_string(qual.itis)
                    qual_to_print += "{} : {}\n".format(q_prop, content)
            ref = statement["ref"]
            ref_to_print = ""
            for part in ref.source_test:
                part_content = part.getTarget()
                ref_content = self.itis_to_string(part_content)
                ref_prop = utils.wd_template("P", part.id)
                ref_to_print += "{} : {}\n".format(ref_prop,
                                                   ref_content)
            table += "|-\n"
            table += "| " + utils.wd_template("P", prop) + "\n"
            table += "| " + value_to_print + "\n"
            table += "| " + qual_to_print + "\n"
            table += "| " + ref_to_print + "\n"
        table += "|}\n"
        table += "----------\n"
        return table

    def __init__(self, WD_object):
        """
        Initialize the Preview Table object.

        :param WD_object: data object to be represented
        :param WD_object: Expected type: WikidataItem object
        """
        self.wd_item = WD_object.wd_item
        self.raw_data = WD_object.raw_data
