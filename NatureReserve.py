from WikidataItem import WikidataItem
import importer_utils as utils


class NatureReserve(WikidataItem):

    def set_labels(self):
        swedish_name = self.raw_data["NAMN"]
        self.add_label("sv", swedish_name)

    def set_descriptions(self):
        swedish_description = "naturreservat"
        self.add_label("sv", swedish_description)

    def set_country(self):
        sweden = self.items["sweden"]
        self.add_statement(
            "country", sweden)

    def set_is(self):
        nature_reserve = self.items["nature_reserve"]
        self.add_statement("is", nature_reserve)

    def set_municipalities(self):
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

    def set_nid(self):
        nid = self.raw_data["NVRID"]
        self.add_statement("nature_id", nid)

    def set_iucn_status(self):
        raw_status = self.raw_data["IUCNKAT"]
        raw_timestamp = self.raw_data["URSBESLDAT"][1:11]
        status_item = [x["item"] for
                       x in self.iucn
                       if x["sv"].lower() == raw_status.lower()]
        protection_date = utils.date_to_dict(raw_timestamp, "%Y-%m-%d")
        qualifier = {"start_time": {"time_value": protection_date}}
        self.add_statement("iucn", status_item, qualifier)

    def set_forvaltare(self):
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

    def __init__(self, raw_data, repository):
        WikidataItem.__init__(self, raw_data, repository)
        self.set_labels()
        self.set_descriptions()
        self.set_is()
        self.set_country()
        # self.set_municipalities()
        self.set_forvaltare()
        self.set_nid()
        self.set_iucn_status()
