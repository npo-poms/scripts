<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0"
                xmlns:exsl="http://exslt.org/common"
                xmlns:update="urn:vpro:media:update:2009"
                extension-element-prefixes="exsl">
  <xsl:param name="tempDir" />
  <!-- splits a locations call into separate xmls and resets the 'urn' -->
  <xsl:output method="text"/>
  <xsl:template match="/">
    <xsl:for-each select="//update:location">
      <xsl:variable name="file">
        <xsl:value-of select="$tempDir" />/location<xsl:value-of select="position()" /><xsl:text>.xml</xsl:text>
      </xsl:variable>
      <xsl:value-of select="$file" /><xsl:text>
    </xsl:text>
      <exsl:document href="{$file}" method="xml">
        <update:location>
          <xsl:copy-of select="./@publishStart" />
          <update:programUrl><xsl:value-of select="./update:programUrl/text()" /></update:programUrl>
          <xsl:copy-of select="./update:avAttributes" />
        </update:location>
      </exsl:document>
    </xsl:for-each>
  </xsl:template>
</xsl:stylesheet>
