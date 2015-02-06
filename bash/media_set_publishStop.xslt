<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns="urn:vpro:media:update:2009"
                >
  <xsl:param name="publishStop" />
  <xsl:output method="xml"/>
  <xsl:template match="/*">
    <xsl:element name="{name()}" namespace="urn:vpro:media:update:2009">
      <xsl:for-each select="@*">
        <xsl:attribute name="{name()}">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:attribute name="publishStop"><xsl:value-of select="$publishStop" /></xsl:attribute>
      <xsl:copy-of select="*" />
    </xsl:element>
  </xsl:template>
</xsl:stylesheet>
