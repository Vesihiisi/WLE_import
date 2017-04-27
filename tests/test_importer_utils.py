#!/usr/bin/python
# -*- coding: utf-8  -*-
import unittest
import WLE_import.importer_utils as utils


class TestStringMethods(unittest.TestCase):

    def test_extract_municipality_name_simple(self):
        text = "Naturreservat i Huddinge kommun"
        output = "Huddinge"
        self.assertEqual(utils.extract_municipality_name(text), output)

    def test_extract_municipality_name_falun(self):
        text = "Naturreservat i Falu kommun"
        output = "Falun"
        self.assertEqual(utils.extract_municipality_name(text), output)

    def test_extract_municipality_name_s_remove(self):
        text = "Naturreservat i Göteborgs kommun"
        output = "Göteborg"
        self.assertEqual(utils.extract_municipality_name(text), output)

    def test_extract_municipality_name_s_keep(self):
        text = "Naturreservat i Robertsfors kommun"
        output = "Robertsfors"
        self.assertEqual(utils.extract_municipality_name(text), output)

    def test_extract_municipality_name_gotland(self):
        text = "Naturreservat i Gotlands län"
        output = "Gotland"
        self.assertEqual(utils.extract_municipality_name(text), output)

    def test_extract_municipality_name_complex(self):
        text = "Planeradfe naturreservat i Huddinge kommun"
        output = "Huddinge"
        self.assertEqual(utils.extract_municipality_name(text), output)


if __name__ == '__main__':
    unittest.main()
