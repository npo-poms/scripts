<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:update="urn:vpro:media:update:2009"
                >
  <xsl:param name="publishStop" />
  <xsl:param name="id" />
  <xsl:param name="programUrl" />
  <xsl:output method="xml"/>
  <xsl:template match="/">
    <xsl:for-each select="//update:location[@urn=concat('urn:vpro:media:location:', $id) or update:programUrl = $programUrl]">
      <update:location>
        <xsl:for-each select="@*">
          <xsl:if test="name() != urn"> <!-- you cannot update existing locations, but it will match on programUrl like this -->
            <xsl:attribute name="{name()}"><xsl:value-of select="."/></xsl:attribute>
          </xsl:if>
        </xsl:for-each>
        <xsl:attribute name="publishStop"><xsl:value-of select="$publishStop" /></xsl:attribute>
        <xsl:copy-of select="*" />
      </update:location>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
