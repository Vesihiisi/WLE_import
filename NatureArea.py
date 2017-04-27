from WikidataItem import WikidataItem
import importer_utils as utils


class NatureArea(WikidataItem):

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
        """Add descriptions in various languages."""
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
        self.add_statement("country", sweden)

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

    def set_iucn_status(self):
        """Set the IUCN category of the area."""
        #  To do: add no_value
        raw_status = self.raw_data["IUCNKAT"]
        raw_timestamp = self.raw_data["URSBESLDAT"][1:11]
        status_item = [x["item"] for
                       x in self.iucn
                       if x["sv"].lower() == raw_status.lower()]
        protection_date = utils.date_to_dict(raw_timestamp, "%Y-%m-%d")
        qualifier = {"start_time": {"time_value": protection_date}}
        self.add_statement("iucn", status_item, qualifier)

    def set_forvaltare(self):
        """Set the operator (förvaltare) of the reserve."""
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
        area_total = self.raw_data["AREA_HA"]
        area_water = self.raw_data["VATTEN_HA"]
        area_land = self.raw_data["LAND_HA"]
        area_woods = self.raw_data["SKOG_HA"]
        print(utils.hectares_to_km(area_total))
        print(area_woods)

    def __init__(self, raw_data, repository, data_files):
        WikidataItem.__init__(self, raw_data, repository, data_files)
        self.set_labels()
        self.set_descriptions()
        self.set_is()
        self.set_country()
        self.set_municipalities()
        self.set_forvaltare()
        self.set_natur_id()
        self.set_iucn_status()
        self.set_area()
