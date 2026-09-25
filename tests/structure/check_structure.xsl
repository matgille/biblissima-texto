<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="3.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0">

    <xsl:output method="text" encoding="UTF-8"/>
    <!--    <xsl:strip-space elements="*"/>-->
    <xsl:param name="output"/>



    <xsl:template match="text()">
        <xsl:if test="normalize-space()">
            <xsl:value-of select="normalize-space(.)"/>
            <!--            <xsl:text> </xsl:text>-->
        </xsl:if>
    </xsl:template>

    <xsl:template match="/">
        <xsl:result-document href="{$output}">
            <xsl:apply-templates select="descendant::tei:text"/>
        </xsl:result-document>
        <xsl:variable name="source" select="base-uri()"/>
        <xsl:variable name="orig_doc"
            select="replace($source, 'corrected', 'TEI')"/>
        <xsl:result-document href="{replace($output, 'reg', 'orig')}">
            <xsl:apply-templates
                select="document($orig_doc)//descendant::tei:text"/>
        </xsl:result-document>
    </xsl:template>

    <!-- Traitement des lb (ajoute un retour à la ligne) -->
    <xsl:template match="tei:lb">
        <xsl:text>&#xA;</xsl:text>
    </xsl:template>

    <!-- Traitement des abréviations (garde orig, supprime reg) -->
    <xsl:template match="tei:ex">
        <xsl:apply-templates/>
    </xsl:template>

    <!-- Suppression des éléments reg dans les abréviations -->
    <xsl:template match="tei:reg"/>

    <!-- Traitement des éléments de texte -->
    <!-- <xsl:template match="tei:l | tei:p | tei:head">
        <xsl:apply-templates/>
        <xsl:text>&#xA;</xsl:text>
    </xsl:template>-->

    <xsl:template match="tei:choice">
        <xsl:apply-templates select="tei:reg | tei:sic"/>
    </xsl:template>

    <!-- Traitement des éléments de structure -->
    <xsl:template match="tei:div | tei:body">
        <xsl:apply-templates/>
        <xsl:text>&#xA;&#xA;</xsl:text>
    </xsl:template>

    <!-- Suppression des éléments non pertinents pour le texte -->
    <xsl:template
        match="tei:teiHeader | tei:sourceDesc | tei:msDesc | tei:profileDesc | tei:encodingDesc"/>

</xsl:stylesheet>
