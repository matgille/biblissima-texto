<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.tei-c.org/ns/1.0"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    exclude-result-prefixes="xs math" version="3.0">
    <xsl:output method="xml"/>
    <xsl:template match="*">
        <xsl:element name="{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="@* | text() | comment() | processing-instruction()">
        <xsl:copy/>
    </xsl:template>
    <!--Permet de copie en appliquant le namespace local de la feuille (défault: tei)-->
    <xsl:template match="/">
        <xsl:element name="TEI">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="RMK">
        <xsl:element name="note">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="HD">
        <xsl:element name="fw">
            <xsl:attribute name="rend">titre-courant</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="CB1">
        <xsl:element name="cb">
            <xsl:attribute name="type">single-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="CB2">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">double-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="CB3">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">triple-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>
    <xsl:template match="CB4">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">quadruple-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>
    <!-- A directement suivi de B -->



    <xsl:template match="EDITORIAL_DELETION">
        <xsl:element name="choice">
            <xsl:element name="sic">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="corr"/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="LAT">
        <xsl:element name="foreign">
            <xsl:attribute name="xml:lang">
                <xsl:text>lat</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="SCRIBAL_INSERTION">
        <xsl:element name="add">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="SCRIBAL_DELETION">
        <xsl:element name="del">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="EDITORIAL_INSERTION">
        <xsl:element name="choice">
            <xsl:element name="corr">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="sic"/>
        </xsl:element>
    </xsl:template>



    <!--Corrections éditoriales-->
    <xsl:template
        match="EDITORIAL_INSERTION[following-sibling::node()[1][self::EDITORIAL_DELETION]]">
        <xsl:element name="choice">
            <xsl:element name="corr">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="sic">
                <xsl:apply-templates
                    select="following-sibling::node()[1]/child::node()"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- B déjà absorbé par le A précédent -->
    <xsl:template
        match="EDITORIAL_DELETION[preceding-sibling::node()[1][self::EDITORIAL_INSERTION]]"/>

    <xsl:template
        match="EDITORIAL_DELETION[following-sibling::node()[1][self::EDITORIAL_INSERTION]]">
        <xsl:element name="choice">
            <xsl:element name="corr">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="sic">
                <xsl:apply-templates
                    select="following-sibling::node()[1]/child::node()"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- B déjà absorbé par le A précédent -->
    <xsl:template
        match="EDITORIAL_INSERTION[preceding-sibling::node()[1][self::EDITORIAL_DELETION]]"/>

    <!--Corrections éditoriales-->


    <xsl:template
        match="SCRIBAL_DELETION[following-sibling::node()[1][self::SCRIBAL_INSERTION]]">
        <xsl:element name="subst">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:element name="del">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="add">
                <xsl:apply-templates
                    select="following-sibling::node()[1]/child::node()"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- B déjà absorbé par le A précédent -->
    <xsl:template
        match="SCRIBAL_INSERTION[preceding-sibling::node()[1][self::SCRIBAL_DELETION]]"/>



    <xsl:template
        match="SCRIBAL_INSERTION[following-sibling::node()[1][self::SCRIBAL_DELETION]]">
        <xsl:element name="subst">
            <xsl:element name="del">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="add">
                <xsl:apply-templates
                    select="following-sibling::node()[1]/child::node()"/>
            </xsl:element>
        </xsl:element>
    </xsl:template>

    <!-- B déjà absorbé par le A précédent -->
    <xsl:template
        match="SCRIBAL_DELETION[preceding-sibling::node()[1][self::SCRIBAL_INSERTION]]"/>

</xsl:stylesheet>
