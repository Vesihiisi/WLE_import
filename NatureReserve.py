from WikidataItem import WikidataItem
import importer_utils as utils


class NatureReserve(WikidataItem):

    def set_labels(self):
        swedish_name = self.raw_data["NAMN"]
        if "reservat" in swedish_name:
            languages = ["sv"]
        else:
            languages = [
                "sv", "en", "da", "fi", "fr", "pt",
                "pl", "nb", "nn", "nl", "de", "es"
            ]
        for language in languages:
            self.add_label(language, swedish_name)

    def set_descriptions(self):
        county_without_lan = self.raw_data["LAN"].split(" ")[:-1]
        county_name = " ".join(county_without_lan)
        if utils.get_last_char(county_name) == "s":
            county_name = county_name[:-1]

        nr_dictionary = {"en": "nature reserve in {}, Sweden",
                         "fi": "luonnonpuisto {} Ruotsissa",
                         "da": "naturreservat i {}, Sverige",
                         "pl": "rezerwat przyrody w regionie {}, Szwecja",
                         "nb": "naturreservat i {}, Sverige",
                         "nn": "naturreservat i {}, Sverige",
                         "nl": "natuurreservaat in {}, Zweden",
                         "de": "Naturschutzgebiet in {}, Schweden",
                         "fr": "réserve naturelle en {}, Suède",
                         "ru": "заповедник в лене {} в Швеции",
                         "pt": "reserva natural na {}, Suécia",
                         "es": "reserva natural en {}, Suecia",
                         "sv": "naturreservat i {}"}
        fi_locations = {
            "Blekinge": "Blekingen läänissä",
            "Dalarna": "Taalainmaan läänissä",
            "Gotland": "Gotlannin läänissä",
            "Gävleborg": "Gävleborgin läänissä",
            "Halland": "Hallandin läänissä",
            "Jämtland": "Jämtlandin läänissä",
            "Jönköping": "Jönköpingin läänissä",
            "Kalmar": "Kalmarin läänissä",
            "Kronoberg": "Kronobergin läänissä",
            "Norrbotten": "Norrbottenin läänissä",
            "Skåne": "Skånen läänissä",
            "Stockholm": "Tukholman läänissä",
            "Södermanland": "Södermanlandin läänissä",
            "Uppsala": "Uppsalan läänissä",
            "Västra Götaland": "Länsi-Götanmaan läänissä",
            "Värmland": "Värmlannin läänissä",
            "Västerbotten": "Västerbottenin läänissä",
            "Västernorrland": "Västernorrlandin läänissä",
            "Västmanland": "Västmanlandin läänissä",
            "Örebro": "Örebron läänissä",
            "Östergötland": "Itä-Götanmaan läänissä"
        }
        ru_locations = {
            "Blekinge": "Блекинге",
            "Dalarna": "Даларна",
            "Gotland": "Готланд",
            "Gävleborg": "Евлеборг",
            "Halland": "Халланд",
            "Jämtland": "Емтланд",
            "Jönköping": "Йёнчёпинг",
            "Kalmar": "Кальмар",
            "Kronoberg": "Крунуберг",
            "Norrbotten": "Норрботтен",
            "Skåne": "Сконе",
            "Stockholm": "Стокгольм",
            "Södermanland": "Сёдерманланд",
            "Uppsala": "Уппсала",
            "Värmland": "Вермланд",
            "Västerbotten": "Вестерботтен",
            "Västernorrland": "Вестерноррланд",
            "Västmanland": "Вестманланд",
            "Västra Götaland": "Вестра-Гёталанд",
            "Örebro": "Эребру",
            "Östergötland": "Эстергётланд",
        }
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
        sweden = self.items["sweden"]
        self.add_statement(
            "country", sweden)

    def set_is(self):
        nature_reserve = self.items["nature_reserve"]
        self.add_statement("is", nature_reserve)

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

    def set_nid(self):
        nid = self.raw_data["NVRID"]
        self.add_statement("nature_id", nid)

    def set_iucn_status(self):
        """
        Set the IUCN category of the area.
        """
        raw_status = self.raw_data["IUCNKAT"]
        raw_timestamp = self.raw_data["URSBESLDAT"][1:11]
        status_item = [x["item"] for
                       x in self.iucn
                       if x["sv"].lower() == raw_status.lower()]
        protection_date = utils.date_to_dict(raw_timestamp, "%Y-%m-%d")
        qualifier = {"start_time": {"time_value": protection_date}}
        self.add_statement("iucn", status_item, qualifier)

    def set_forvaltare(self):
        """
        Set the operator (förvaltare) of the reserve.
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
