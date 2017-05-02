# -*- coding: utf-8 -*-
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

    def make_table(self):
        """Generate a wikitext preview table of the data item."""
        table = self.print_raw_data()
        labels = self.wd_item["labels"]
        descriptions = self.wd_item["descriptions"]
        table = table + "'''Labels'''\n\n"
        for label in labels:
            language = label["language"]
            text = label["value"]
            table = table + "* '''" + language + "''': " + text + "\n\n"
        table = table + "'''Descriptions'''\n\n"
        for desc in descriptions:
            language = desc["language"]
            text = desc["value"]
            table = table + "* '''" + language + "''': " + text + "\n\n"
        if self.wd_item["wd-item"] is not None:
            table = table + "'''Possible item''': " + \
                utils.wd_template("Q", self.wd_item["wd-item"]) + "\n\n"
        else:
            table = table + "'''Possible item''': \n\n"
        table_head = "{| class='wikitable'\n|-\n! Property\n! Value\n! Qualifiers\n! References\n"
        table = table + table_head
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
                if isinstance(part_content, pywikibot.page.ItemPage):
                    ref_content = utils.wd_template(
                        "Q", part.getTarget().getID())
                elif isinstance(part_content, str):
                    ref_content = part_content
                ref_prop = utils.wd_template("P", part.id)
                ref_to_print += "{} : {}\n".format(ref_prop,
                                                   ref_content)
            table = table + "|-\n"
            table = table + "| " + utils.wd_template("P", prop) + "\n"
            table = table + "| " + value_to_print + "\n"
            table = table + "| " + qual_to_print + "\n"
            table = table + "| " + ref_to_print + "\n"
        table = table + "|}\n"
        table = table + "----------\n"
        return table

    def __init__(self, WD_object):
        self.wd_item = WD_object.wd_item
        self.raw_data = WD_object.raw_data
