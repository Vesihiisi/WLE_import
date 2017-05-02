from WikidataItem import WikidataItem
import importer_utils as utils


class NatureArea(WikidataItem):
    """
    Extension of WikidataItem to create nature area objects.

    Handles both reserves and national parks.
    """

    def create_sources(self):
        """Create the references for all statements."""
        self.sources = {}
        item_nr = self.items["source_nr"]
        item_np = self.items["source_np"]
        self.sources["np"] = self.make_stated_in_ref(item_np, "2015-12-18")
        self.sources["nr"] = self.make_stated_in_ref(item_nr, "2015-12-18")

    def set_labels(self):
        """
        Add labels, optionally in multiple languages.

        A number of items have the word natur/domän etc. reservat
        included in the name. In this case, the name is
        added only in Swedish. Otherwise, if it's a pure
        geographical name, it is added in a number of Latin script
        languages.
        """
        swedish_name = self.raw_data["NAMN"]
        if ("reservat" in swedish_name.lower() or
                "nationalpark" in swedish_name.lower() or
                "skärgård" in swedish_name.lower()):
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
        """Set the country to Sweden."""
        sweden = self.items["sweden"]
        ref = self.make_stated_in_ref("Q29580583", "2009-12-09")
        self.add_statement("country", sweden, ref=ref)

    def set_iucn_status(self):
        """Set the IUCN category of the area."""
        #  To do: add no_value...
        raw_status = self.raw_data["IUCNKAT"]
        raw_timestamp = self.raw_data["URSBESLDAT"][1:11]
        status_item = [x["item"] for
                       x in self.iucn
                       if x["sv"].lower() == raw_status.lower()]
        qualifier = self.make_qualifier_startdate(raw_timestamp)
        self.add_statement("iucn", status_item, quals=[qualifier])

    def set_is(self):
        """Set the P31 property - nature reserve or national park."""
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
        """Set the Naturvårdsverket ID number."""
        nid = self.raw_data["NVRID"]
        self.add_statement("nature_id", nid)

    def set_forvaltare(self):
        """Set the operator (förvaltare) of the area."""
        forvaltare_raw = self.raw_data["FORVALTARE"]
        #  TODO: wtf is an enskild markägare?????????
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
        """Get WD item associated with certain value of unique ID."""
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
        """Overwrite plain add_statement with default sources."""
        if self.raw_data["SKYDDSTYP"] == "Nationalpark":
            source = self.sources["np"]
        elif self.raw_data["SKYDDSTYP"] == "Naturreservat":
            source = self.sources["nr"]
        return super().add_statement(prop_name, value, quals, source)

    def __init__(self, raw_data, repository, data_files, existing):
        """
        Initialize the NatureArea object.

        :param raw_data: Row from csv file.
        :param repository: Wikidata site instance.
        :param data_files: Dict of various mapping files.
        :param existing: WD items that already have an unique id
        """
        WikidataItem.__init__(self, raw_data, repository, data_files, existing)
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
