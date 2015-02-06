<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:update="urn:vpro:media:update:2009"
                >
  <xsl:output method="text"/>
  <xsl:template match="/">
    <xsl:for-each select="///update:scheduleEvent">
      <xsl:value-of select="@channel" />
      <xsl:text> </xsl:text>
      <xsl:value-of select="update:start" />
      <xsl:text> </xsl:text>
      <xsl:value-of select="../../@mid" />
      <xsl:text>&#xa;</xsl:text>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
