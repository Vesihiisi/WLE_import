from os import path

from wikidataStuff.WikidataStuff import WikidataStuff as WDS
import pywikibot

import importer_utils as utils


MAPPING_DIR = "data"
PROPS = utils.load_json(path.join(MAPPING_DIR, "properties.json"))

SUMMARY_TEST = "nature test"
SUMMARY_LIVE = ""


class Uploader(object):
    """Upload a WikidataItem."""

    TEST_ITEM = "Q4115189"

    def add_labels(self, target_item, labels):
        """
        Add labels and aliases.

        Normally, if the WD item already has a label in $lang
        and the data object has another one, the new one
        will be automatically added as an alias. Otherwise
        (no existing label), it will be added as a label.
        """
        for label in labels:
            target_item.get()
            label_content = label['value']
            language = label['language']
            self.wdstuff.addLabelOrAlias(
                language, label_content, target_item)

    def add_descriptions(self, target_item, descriptions):
        """Add descriptions to the item."""
        for description in descriptions:
            target_item.get()
            desc_content = description['value']
            lang = description['language']
            self.wdstuff.add_description(
                lang, desc_content, target_item)

    def add_claims(self, wd_item, claims):
        """Add claims to the item."""
        if wd_item:
            for claim in claims:
                wd_item.get()
                prop = claim["prop"]
                value = claim["value"]
                ref = claim["ref"]
                quals = claim["quals"]
                if quals and len(quals) > 0:
                    for qualifier in quals:
                        value.addQualifier(qualifier)
                self.wdstuff.addNewClaim(prop, value, wd_item, ref)

    def create_new_item(self):
        """Create a new WD item and return it."""
        return self.wdstuff.make_new_item({}, self.summary)

    def get_username(self):
        """Get Wikidata login that will be used to upload."""
        return pywikibot.config.usernames["wikidata"]["wikidata"]

    def upload(self):
        """Upload a single WD item, or enrich an already existing one."""
        if self.data["upload"] is False:
            print("SKIPPING ITEM")
            return
        labels = self.data["labels"]
        descriptions = self.data["descriptions"]
        claims = self.data["statements"]
        self.add_labels(self.wd_item, labels)
        self.add_descriptions(self.wd_item, descriptions)
        self.add_claims(self.wd_item, claims)

    def set_wd_item(self):
        """
        Determine WD item to manipulate.

        In live mode, if data object has associated WD item,
        edit it. Otherwise, create a new WD item.
        In sandbox mode, all edits are done on the WD Sandbox item.
        """
        if self.live:
            if self.data["wd-item"] is None:
                self.wd_item = self.create_new_item()
                self.wd_item_q = self.wd_item.getID()
            else:
                item_q = self.data["wd-item"]
                self.wd_item = self.wdstuff.QtoItemPage(item_q)
                self.wd_item_q = item_q
        else:
            self.wd_item = self.wdstuff.QtoItemPage(self.TEST_ITEM)
            self.wd_item_q = self.TEST_ITEM

    def __init__(self,
                 data_object,
                 repo,
                 live=False,
                 edit_summary=None):
        """
        Initialize an Upload object for a single Nature Area.

        :param data_object: Dictionary of object data
        :param repo: Data repository of site to work on (Wikidata)
        :param live: Whether to work on real WD items or in the sandbox
        """
        self.repo = repo
        self.live = live
        print("User: {}".format(self.get_username()))
        print("Edit summary: {}".format(self.summary))
        if self.live:
            print("LIVE MODE")
            self.summary = edit_summary or SUMMARY_LIVE
        else:
            print("SANDBOX MODE: {}".format(self.TEST_ITEM))
            self.summary = SUMMARY_TEST
        print("---------------")
        self.data = data_object.wd_item
        self.wdstuff = WDS(self.repo, edit_summary=self.summary)
        self.set_wd_item()
