from wikidataStuff.WikidataStuff import WikidataStuff as WDS
import pywikibot
import importer_utils as utils
from os import path

MAPPING_DIR = "data"
PROPS = utils.load_json(path.join(MAPPING_DIR, "properties.json"))


class Uploader(object):

    TEST_ITEM = "Q4115189"

    def add_labels(self, target_item, labels, log):
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
            if log:
                t_id = target_item.getID()
                message = "{} ADDED LABEL {} {}".format(
                    t_id, language, label_content)
                log.logit(message)

    def add_descriptions(self, target_item, descriptions, log):
        for description in descriptions:
            target_item.get()
            desc_content = description['value']
            lang = description['language']
            self.wdstuff.add_description(
                lang, desc_content, target_item)
            if log:
                t_id = target_item.getID()
                message = "{} ADDED DESCRIPTION {} {}".format(
                    t_id, lang, desc_content)
                log.logit(message)

    def add_claims(self, wd_item, claims, log):
        if wd_item:
            for claim in claims:
                wd_item.get()
                print(claim)
                prop = claim["prop"]
                value = claim["value"]
                ref = claim["ref"]
                quals = claim["quals"]
                if quals and len(quals) > 0:
                    for qualifier in quals:
                        value.addQualifier(qualifier)
                self.wdstuff.addNewClaim(prop, value, wd_item, ref)

    def create_new_item(self, log):
        item = self.wdstuff.make_new_item({}, self.summary)
        if log:
            t_id = item.getID()
            message = "{} CREATE".format(t_id)
            log.logit(message)
        return item

    def get_username(self):
        """Get Wikidata login that will be used to upload."""
        return pywikibot.config.usernames["wikidata"]["wikidata"]

    def upload(self):
        if self.data["upload"] is False:
            print("SKIPPING ITEM")
            return
        # labels = self.data["labels"]
        # descriptions = self.data["descriptions"]
        # aliases = self.make_aliases()
        claims = self.data["statements"]
        # self.add_labels(self.wd_item, labels, self.log)
        # self.add_descriptions(self.wd_item, descriptions, self.log)
        self.add_claims(self.wd_item, claims, self.log)

    def set_wd_item(self):
        """
        Determine WD item to manipulate.

        In live mode, if data object has associated WD item,
        edit it. Otherwise, create a new WD item.
        In sandbox mode, all edits are done on the WD Sandbox item.
        """
        if self.live:
            if self.data["wd-item"] is None:
                self.wd_item = self.create_new_item(self.log)
                self.wd_item_q = self.wd_item.getID()
            else:
                item_q = self.data["wd-item"]
                self.wd_item = self.wdstuff.QtoItemPage(item_q)
                self.wd_item_q = item_q
        else:
            self.wd_item = self.wdstuff.QtoItemPage(self.TEST_ITEM)
            self.wd_item_q = self.TEST_ITEM

    def __init__(self,
                 monument_object,
                 repo,
                 log=None,
                 tablename=None,
                 live=False,
                 edit_summary=None):
        """
        Initialize an Upload object for a single Monument.

        :param monument_object: Dictionary of Monument data
        :param repo: Data repository of site to work on (Wikidata)
        :param log: Enable logging to file
        :param tablename: Name of db table, used in edit summary
        :param live: Whether to work on real WD items or in the sandbox
        """
        self.repo = repo
        self.log = False
        self.summary = edit_summary or "test"
        self.live = live
        print("User: {}".format(self.get_username()))
        print("Edit summary: {}".format(self.summary))
        if self.live:
            print("LIVE MODE")
        else:
            print("SANDBOX MODE: {}".format(self.TEST_ITEM))
        print("---------------")
        if log is not None:
            self.log = log
        self.data = monument_object.wd_item
        self.wdstuff = WDS(self.repo, edit_summary=self.summary)
        self.set_wd_item()
