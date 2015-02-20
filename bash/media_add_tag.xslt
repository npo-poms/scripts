<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns="urn:vpro:media:update:2009"
                xmlns:media="urn:vpro:media:update:2009"
                >
  <xsl:param name="tag" />
  <xsl:output method="xml"/>
  <xsl:template match="/*">
    <xsl:element name="{name()}" namespace="urn:vpro:media:update:2009">
      <xsl:for-each select="@*">
        <xsl:attribute name="{name()}">
          <xsl:value-of select="."/>
        </xsl:attribute>
      </xsl:for-each>
      <xsl:apply-templates select="*" />
    </xsl:element>
  </xsl:template>
  <xsl:template match="*">
    <xsl:copy-of select="." />
  </xsl:template>
  <xsl:template match="media:title[not(following-sibling::media:description) and not(following-sibling::media:title)]">
    <xsl:copy-of select="." />
    <xsl:if test="not(../media:tag = $tag)">
      <tag><xsl:value-of select="$tag"/></tag>
    </xsl:if>
  </xsl:template>

  <xsl:template match="media:description[not(following-sibling::media:description)]">
    <xsl:copy-of select="." />
    <xsl:if test="not(../media:tag = $tag)">
      <tag><xsl:value-of select="$tag"/></tag>
    </xsl:if>
  </xsl:template>

</xsl:stylesheet>
