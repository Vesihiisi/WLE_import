from WikidataItem import WikidataItem

import importer_utils as utils


class NatureArea(WikidataItem):
    """
    Extension of WikidataItem to create nature area objects.

    Handles both nature reserves and national parks.
    """

    def __init__(self, raw_data, repository, data_files, existing):
        """
        Initialize the NatureArea object.

        :param raw_data: Row from csv file.
        :param raw_data: Expected type: string
        :param repository: Wikidata site instance.
        :param repository: Expected type: site instance
        :param data_files: Dict of various mapping files.
        :param data_files: Expected type: dictionary
        :param existing: WD items that already have an unique id
        :param existing: Expected type: dictionary

        :return: nothing
        """
        WikidataItem.__init__(self, raw_data, repository, data_files, existing)
        self.municipalities = data_files["municipalities"]
        self.iucn = data_files["iucn_categories"]
        self.forvaltare = data_files["forvaltare"]
        self.glossary = data_files["glossary"]
        self.match_wikidata(data_files)
        self.create_sources()
        self.set_labels()
        self.set_descriptions()
        self.set_is()
        self.set_country()
        self.set_municipalities()
        self.set_forvaltare()
        self.set_natur_id()
        self.set_iucn_status()
        self.set_area()

    def generate_ref_url(self):
        """
        Create url to nature authority API with specific ID.

        :return: url pointing to the post of the specific nature area
        """
        url = ("http://nvpub.vic-metria.nu/"
               "naturvardsregistret/rest/omrade/{}/G%C3%A4llande")
        return url.format(self.raw_data["NVRID"])

    def create_sources(self):
        """
        Create the references for all statements.

        Information about the source datasets comes
        from the metadata supplied by Naturvårdsverket.

        :return: nothing
        """
        self.sources = {}
        item_nr = self.items["source_nr"]
        item_np = self.items["source_np"]
        url = self.generate_ref_url()
        self.sources["np"] = self.make_stated_in_ref(item_np,
                                                     "2015-12-18",
                                                     url)
        self.sources["nr"] = self.make_stated_in_ref(item_nr,
                                                     "2015-12-18",
                                                     url)

    def set_labels(self):
        """
        Add labels, optionally in multiple languages.

        A number of items have the word natur/domän etc. reservat
        included in the name. In this case, the name is
        added only in Swedish. Otherwise, if it's a pure
        geographical name, it is added in a number of Latin script
        languages.

        :return: nothing
        """
        swedish_name = self.raw_data["NAMN"]
        exclude_words = ["nationalpark", "reservat", "skärgård"]
        if any(word in swedish_name.lower() for word in exclude_words):
            languages = ["sv"]
        else:
            languages = [
                "sv", "en", "da", "fi", "fr", "pt",
                "pl", "nb", "nn", "nl", "de", "es"
            ]
        for language in languages:
            self.add_label(language, swedish_name)

    def set_descriptions(self):
        """
        Add descriptions in various languages.

        National park format: "national park in Sweden".
        Reserve format: "nature reserve in <län>, Sweden".

        :return: nothing
        """
        if self.raw_data["SKYDDSTYP"] == "Nationalpark":
            np_dictionary = self.glossary["np_description"]
            for language in np_dictionary:
                description = np_dictionary[language]
                self.add_description(language, description)
        elif self.raw_data["SKYDDSTYP"] == "Naturreservat":
            county_without_lan = self.raw_data["LAN"].split(" ")[:-1]
            county_name = " ".join(county_without_lan)
            if utils.get_last_char(county_name) == "s":
                county_name = county_name[:-1]

            nr_dictionary = self.glossary["nr_description"]
            fi_locations = self.glossary["location_in"]["fi"]
            ru_locations = self.glossary["location_in"]["ru"]
            for language in nr_dictionary:
                if language == "fi":
                    description = nr_dictionary[language].format(
                        fi_locations[county_name])
                elif language == "ru":
                    description = nr_dictionary[language].format(
                        ru_locations[county_name])
                else:
                    description = nr_dictionary[language].format(county_name)
                self.add_description(language, description)

    def set_country(self):
        """
        Set the country to Sweden.

        :return: nothing
        """
        sweden = self.items["sweden"]
        self.add_statement("country", sweden)

    def set_iucn_status(self):
        """
        Set the IUCN category of the area.

        :return: nothing
        """

        raw_status = self.raw_data["IUCNKAT"]
        raw_timestamp = self.raw_data["URSBESLDAT"][1:11]
        status_item = [x["item"] for
                       x in self.iucn
                       if x["sv"].lower() == raw_status.lower()]
        qualifier = self.make_qualifier_startdate(raw_timestamp)
        self.add_statement("iucn", status_item, quals=[qualifier])
        #  To do: add no_value...

    def set_is(self):
        """
        Set the P31 property - nature reserve or national park.

        :return: nothing
        """
        skyddstyp = self.raw_data["SKYDDSTYP"]
        if skyddstyp == "Nationalpark":
            status = self.items["national_park"]
        elif skyddstyp == "Naturreservat":
            status = self.items["nature_reserve"]
        self.add_statement("is", status)

    def set_municipalities(self):
        """
        Set the municipalities where the area is located.

        Can be more than one claim if the area stretches across
        several municipalities.

        :return: nothing
        """
        municipalities_raw = self.raw_data["KOMMUN"].split(",")
        for municipality in municipalities_raw:
            municipality = municipality.strip()
            if municipality == "Malung":  # Changed in 2007.
                municipality = "Malung-Sälen"
            elif municipality == "Göteborg":
                municipality = "Gothenburg"

            municipality_long = municipality.lower() + " municipality"
            m_item = [x["item"] for
                      x in self.municipalities
                      if x["en"].lower() == municipality_long]
            self.add_statement("located_adm", m_item[0])

    def set_natur_id(self):
        """
        Set the Naturvårdsverket ID number.

        :return: nothing
        """
        nid = self.raw_data["NVRID"]
        self.add_statement("nature_id", nid)

    def set_forvaltare(self):
        """
        Set the operator of the area.

        :return: nothing
        """
        forvaltare_raw = self.raw_data["FORVALTARE"]
        try:
            f = [x["item"] for
                 x in self.forvaltare
                 if x["sv"].lower() == forvaltare_raw.lower()]
            forvaltare = f[0]
        except IndexError:
            if "kommun" in forvaltare_raw.lower():
                if forvaltare_raw == "Hässelholms kommun":
                    forvaltare_raw = "Hässleholms kommun"
                elif forvaltare_raw == "Malungs kommun":
                    forvaltare_raw = "Malung-Sälens kommun"
                forvaltare = [x["item"] for
                              x in self.municipalities
                              if x["sv"].lower() == forvaltare_raw.lower()]
        if forvaltare:
            self.add_statement("forvaltare", forvaltare)

    def set_area(self):
        """
        Set the area values of nature monument.

        The source data has both the total area
        and separate values for land/water/woods.
        We add both: first the total area without any
        qualifiers, and then separately for every part,
        with "applies to part" qualifier.

        :return: nothing
        """
        area_total = self.raw_data["AREA_HA"]
        self.add_statement(
            "area", {"quantity_value": area_total, "unit": self.items["km"]})

        areas_parts = {"SKOG_HA": "woods",
                       "LAND_HA": "land",
                       "VATTEN_HA": "water"}
        for part in areas_parts:
            source_field = self.raw_data[part]
            target_item = self.items[areas_parts[part]]
            qualifier = self.make_qualifier_applies_to(target_item)
            self.add_statement(
                "area", {"quantity_value": source_field,
                         "unit": self.items["km"]},
                quals=[qualifier])

    def match_wikidata_existing(self, value):
        """
        Get WD item associated with certain value of unique ID.

        :param value: the ID to check
        :param value: Expected type: string

        :return: a match, if found
        """
        match = [self.existing[x] for x in self.existing if x == value]
        try:
            return match[0]
        except IndexError:
            return None

    def match_wikidata(self, data_files):
        """
        Read the assigned WD item from mapping file.

        For national parks, these have been controlled
        manually. For nature reserves, the mapping was
        generated by nature_harvester.py, see there for
        methodology used.
        TODO: check the P31 of matched reserve item.

        :param data_files: the library of files with area Wikidata mappings
        :param data_files: Expected type: dictionary

        :return: nothing
        """
        if self.raw_data["SKYDDSTYP"] == "Nationalpark":
            mapping = data_files["mapping_nationalparks"]
        elif self.raw_data["SKYDDSTYP"] == "Naturreservat":
            mapping = data_files["svwp_to_nature_id_exact"]
        nature_id = self.raw_data["NVRID"]

        match_via_id_on_wd = self.match_wikidata_existing(nature_id)
        if match_via_id_on_wd:
            self.associate_wd_item(match_via_id_on_wd)
        else:
            match = [x["item"] for x in mapping if x["nature_id"] == nature_id]
            try:
                self.associate_wd_item(match[0])
            except IndexError:
                print("{} has no WD match.".format(self.raw_data["NAMN"]))

    def add_statement(self, prop_name, value, quals=None, ref=None):
        """
        Overwrite plain add_statement with default sources.

        :param prop_name: P-item representing property
        :param prop_name: Expected type: string
        :param value: content of the statement
        :param value: Expected type: it can be a string representing
                      a Q-item or a dictionary of an amount
        :param quals: possibly qualifier items
        :param quals: Expected type: list of wikidatastuff Qualifier items
        :param ref: reference item
        :param ref: Expected type: a wikidatastuff Reference item

        :return: an add_statement function with the correct source set
                 as default depending on the type of the area.
        """
        if self.raw_data["SKYDDSTYP"] == "Nationalpark":
            source = self.sources["np"]
        elif self.raw_data["SKYDDSTYP"] == "Naturreservat":
            source = self.sources["nr"]
        return super().add_statement(prop_name, value, quals, source)
