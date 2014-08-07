#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import poms
from xml.dom import minidom
import time
import unittest
import xml.etree.ElementTree as ET



class POMSRSTest(unittest.TestCase):
    def setUp(self):
        poms.opts()
        global xmlns, pref
        xmlns = "urn:vpro:media:update:2009"
        pref = "{" + xmlns + "}"
        ET.register_namespace("u", xmlns)

    def to_et(self, minidomxml):
        """poms library uses standard minidom, this converts to ElementTree, because that provides xpath"""
        return ET.fromstring(minidomxml.toxml())



    def test_post(self):
        print "posting xml"
        mid = poms.post_str("""
        <program xmlns:media="urn:vpro:media:2009" xmlns:shared="urn:vpro:shared:2009" xmlns="urn:vpro:media:update:2009" type="CLIP" avType="VIDEO" embeddable="true">
           <broadcaster>VPRO</broadcaster>
           <title type="MAIN">Holland Doc</title>
           <title type="SUB">Zwart ijs</title>
           <title type="ORIGINAL">Holland Doc: Zwart IJs</title>
           <description type="MAIN">Main title</description>
           <description type="SHORT">Short title</description>
           <description type="EPISODE"> Documentaire over de band tussen het schaatsen op natuurijs en orthodox-christelijk Nederland. Zwart IJs volgt een aantal schaatsers in een jaar dat er bijna een Elfstedentocht kwam, op zondag.</description>
           <tag>schaatsen</tag>
        </program>
        """);

        xml = self.to_et(poms.get(mid))

        self.assertEqual(xml.findall(pref + "title[@type='MAIN']")[0].text, "Holland Doc")

        return mid

    def test_get(self):
        print "getting xml"
        xml = self.to_et(poms.get("POMS_VPRO_1250889"))
        self.assertEqual(xml.findall(pref + "title[@type='MAIN']")[0].text, "Holland Doc")



if __name__ == "__main__":
    unittest.main()
