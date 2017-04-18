#!/usr/bin/env python3
import csv

reserves_file = "data/NR_polygon.csv"


class NatureArea(object):

    def process_name(self, raw_name):
        return raw_name

    def process_municipality(self, raw_municipality):
        return raw_municipality

    def process_county(self, raw_county):
        return raw_county

    def process_operator(self, raw_operator):
        return raw_operator

    def __init__(self, raw_data):
        self.name = self.process_name(raw_data["NAMN"])
        self.municipality = self.process_municipality(raw_data["KOMMUN"])
        self.county = self.process_county(raw_data["LAN"])
        self.operator = self.process_operator(raw_data["FORVALTARE"])


def csv_reader(file_obj):
    reader = csv.DictReader(file_obj, delimiter=',')
    for row in reader:
        area = NatureArea(row)
        print(area.name, area.municipality, area.county, area.operator)


if __name__ == "__main__":
    with open(reserves_file, "r") as f_obj:
        csv_reader(f_obj)
