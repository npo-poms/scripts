#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import poms
import unittest
import logging

import xml.etree.ElementTree as ET



class POMSRSTest(unittest.TestCase):
    def setUp(self):
        global xmlns, pref
        xmlns = "urn:vpro:media:update:2009"
        pref = "{" + xmlns + "}"
        ET.register_namespace("u", xmlns)

    def to_et(self, minidomxml):
        """poms library uses standard minidom, this converts to ElementTree, because that provides xpath"""
        return ET.fromstring(minidomxml.toxml())



    def test_post(self):
        print("posting xml")
        mid = poms.post_str("""
        <program xmlns:media="urn:vpro:media:2009" xmlns:shared="urn:vpro:shared:2009" xmlns="urn:vpro:media:update:2009" type="CLIP" avType="VIDEO" embeddable="true">
           <broadcaster>VPRO</broadcaster>
           <title type="MAIN">Holland Doc</title>
           <title type="SUB">Sub title</title>
           <title type="ORIGINAL">Original title</title>
           <description type="MAIN">Main title</description>
           <description type="SHORT">Short title</description>
           <description type="EPISODE">Episode title</description>
           <tag>schaatsen</tag>
        </program>
        """)
        print(mid)
        xml = self.to_et(poms.get(mid))

        self.assertEqual(xml.findall(pref + "title[@type='MAIN']")[0].text, "Holland Doc")

        return mid

    def test_get(self):
        print("getting xml")
        xml = self.to_et(poms.get("POMS_NTR_388772"))
        self.assertEqual(xml.findall(pref + "title[@type='MAIN']")[0].text, "Winfried Draait Door")

    def test_parkpost(self):
        xml = """<?xml version="1.0"?>
<NPO_gfxwrp>
  <ProductCode>2P0108MO_BLAUWBLOTEST3</ProductCode>
  <OrderCode>2P140801_EO___BLAUW_BL_MORTEST3</OrderCode>
  <Broadcaster>VPRO</Broadcaster>
  <PromotedProgramProductCode>POMS_VPRO_216214</PromotedProgramProductCode>
  <Referrer/>
  <MXF_Name>91345392</MXF_Name>
  <ProgramTitle>Blauw Bloed Extra: Prinses Irene - 75 jaar</ProgramTitle>
  <EpisodeTitle>Blauw Bloed Extra: Prinses Irene - 75 jaar</EpisodeTitle>
  <PromoType>P</PromoType>
  <TrailerTitle>Blauw Bloed Extra: Prinses Irene - 75 jaar</TrailerTitle>
  <SerieTitle>Blauw Bloed Extra: Prinses Irene - 75 jaar</SerieTitle>
  <FrameCount>750</FrameCount>
  <VideoFormat>HD</VideoFormat>
  <FirstTransmissionDate>2014-08-01T16:59:04+00:00</FirstTransmissionDate>
  <PlacingWindowStart>2014-07-31T06:00:00+02:00</PlacingWindowStart>
  <PlacingWindowEnd>2014-08-01T06:00:00+02:00</PlacingWindowEnd>
  <Files>
    <File Filename="2P0108MO_BLAUWBLO.ismv"/>
    <File Filename="2P0108MO_BLAUWBLO.ismc"/>
    <File Filename="2P0108MO_BLAUWBLO.ism"/>
  </Files>
</NPO_gfxwrp>"""

    def test_xslt(self):
        xsl = poms.get_xslt("location_set_publishStop.xslt")
        locations="""
            <locations xmlns="urn:vpro:media:update:2009">
              <location>
                <programUrl>rtsp:someurl</programUrl>
                <avAttributes>
                   <bitrate>1000000</bitrate>
                   <avFileFormat>M4V</avFileFormat>
                   <videoAttributes width="320" height="180">
                    <aspectRatio>16:9</aspectRatio>
                  </videoAttributes>
                </avAttributes>
               <duration>P0DT0H1M40.000S</duration>
            </location>
            </locations>
        """
        print(poms.xslt(locations, xsl, params = {"programUrl": "rtsp:someurl",
                                            "publishStop": '2012'}))

    def test_get_locations(self):


        print(poms.set_location("WO_VPRO_041686", "http://www.vpro.nl/123.mp4", publishStop = "2012-10-10T20:20:00"))



if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    poms.opts(env = 'dev')
    poms.errors('michiel.meeuwissen@gmail.com')
    del sys.argv[1:]
    suite = unittest.TestSuite()
    suite.addTest(POMSRSTest("test_get_locations"))
    runner = unittest.TextTestRunner()
    runner.run(suite)
    #unittest.main()
