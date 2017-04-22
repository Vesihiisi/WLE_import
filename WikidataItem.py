from os import path
import json
import importer_utils as utils

DATA_DIR = "data"


class WikidataItem(object):

    def print_wd(self):
        """Print the data object dictionary on screen."""
        print(
            json.dumps(self.wd_item,
                       sort_keys=True,
                       indent=4,
                       ensure_ascii=False,
                       default=utils.datetime_convert)
        )

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

    def add_statement(self, prop_name, value, quals=None, refs=None):
        """
        Add a statement to the data object.

        If the given property already exists, this will
        append another value to the array,
        i.e. two statements with the same prop.

        Refs is None as default. This means that
        if it's left out, the WLM reference will be inserted
        into the statement. The same if its value is
        set to True. In order to use a custom reference
        or more than one reference, it is inserted here as
        either a single reference or a list of references,
        respectively.
        In order to not use any reference whatsoever,
        the value of refs is to be set to False.

        :param prop_name: name of the property,
            as stated in the props library file
        :param value: the value of the property
        :param quals: a dictionary of qualifiers
        :param refs: a list of references or a single reference.
            Set None/True for the default reference,
            set False to not add a reference.
        """
        base = self.wd_item["statements"]
        prop = self.props[prop_name]
        qualifiers = {}
        if prop not in base:
            base[prop] = []
        if quals is not None and len(quals) > 0:
            for k in quals:
                prop_name = self.props[k]
                qualifiers[prop_name] = quals[k]
        refs = []
        if refs and not isinstance(refs, list):
            refs = [refs]
        statement = {"value": value, "quals": qualifiers, "refs": refs}
        base[prop].append(statement)

    def remove_statement(self, prop_name):
        """
        Remove all statements with a given property from the data object.

        :param prop_name: name of the property,
            as stated in the props library file
        """
        base = self.wd_item["statements"]
        prop = self.props[prop_name]
        if prop in base:
            del base[prop]

    def substitute_statement(self, prop_name, value, quals=None, refs=None):
        """
        Instead of adding to the array, replace the statement.

        This is so that instances of child classes
        can override default values...
        For example p31 museum -> art museum
        """
        base = self.wd_item["statements"]
        prop = self.props[prop_name]
        if prop not in base:
            base[prop] = []
            self.add_statement(prop_name, value, quals, refs)
        else:
            self.remove_statement(prop_name)
            self.add_statement(prop_name, value, quals, refs)

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
        base[language] = text

    def add_alias(self, language, text):
        """
        Add an alias in a specific language.

        :param language: code of language, e.g. "fi"
        :param text: content of the alias
        """
        base = self.wd_item["aliases"]
        if language not in base:
            base[language] = []
        base[language].append(text)

    def add_description(self, language, text):
        """
        Add a description in a specific language.

        :param language: code of language, e.g. "fi"
        :param text: content of the description
        """
        base = self.wd_item["descriptions"]
        base[language] = text

    def create_stated_in_source(self, source_item, pub_date):
        """
        Create a 'stated in' reference.

        :param source_item: Wikidata item or URL used as a source
        :param pub_date: publication date in the format 2014-12-23
        """
        prop_stated = self.props["stated_in"]
        prop_date = self.props["publication_date"]
        pub_date = utils.date_to_dict(pub_date, "%Y-%m-%d")
        return {"source": {"prop": prop_stated, "value": source_item},
                "published": {"prop": prop_date, "value": pub_date}}

    def add_to_report(self, key_name, raw_data):
        """
        Add data to problem report json.

        Check if item has an associated Q-number,
        and if that's the case and it's missing
        in the report,
        add it to the report automatically.
        Add direct URL to item in WLM API.
        """
        self.problem_report[key_name] = raw_data
        if "wd-item" not in self.problem_report:
            if self.wd_item["wd-item"] is not None:
                self.problem_report["Q"] = self.wd_item["wd-item"]
            else:
                self.problem_report["Q"] = ""
        if "url" not in self.problem_report:
            self.problem_report["url"] = self.wlm_url

    def print_report(self):
        """Print the problem report on screen."""
        print(
            json.dumps(self.problem_report,
                       sort_keys=True,
                       indent=4,
                       ensure_ascii=False,
                       default=utils.datetime_convert)
        )

    def get_report(self):
        """Retrieve the problem report."""
        return self.problem_report

    def construct_wd_item(self):
        """Create the empty structure of the data object."""
        self.wd_item = {}
        self.wd_item["upload"] = True
        self.wd_item["statements"] = {}
        self.wd_item["labels"] = {}
        self.wd_item["aliases"] = {}
        self.wd_item["descriptions"] = {}
        self.wd_item["wd-item"] = None

    def __init__(self, db_row_dict, repository):
        """
        Initialize the data object.

        :param db_row_dict: raw data from the database
        :param repository: data repository (Wikidata site)
        """
        self.raw_data = db_row_dict
        self.props = utils.load_json(
            path.join(DATA_DIR, "properties.json"))
        self.items = utils.load_json(
            path.join(DATA_DIR, "items.json"))
        self.municipalities = utils.load_json(
            path.join(DATA_DIR, "municipalities.json"))
        self.iucn = utils.load_json(
            path.join(DATA_DIR, "iucn_categories.json"))
        self.forvaltare = utils.load_json(
            path.join(DATA_DIR, "forvaltare.json"))
        self.construct_wd_item()
        self.repo = repository
        self.problem_report = {}
