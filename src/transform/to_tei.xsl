<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns="http://www.tei-c.org/ns/1.0"
    xmlns:xs="http://www.w3.org/2001/XMLSchema"
    xmlns:xi="http://www.w3.org/2001/XInclude"
    xmlns:math="http://www.w3.org/2005/xpath-functions/math"
    exclude-result-prefixes="xs math" version="3.0">
    <xsl:output method="xml"/>


    <!--Permet de copie en appliquant le namespace local de la feuille (défault: tei)-->
    <xsl:template match="*">
        <xsl:element name="{local-name()}">
            <xsl:apply-templates select="@* | node()"/>
        </xsl:element>
    </xsl:template>
    <xsl:template match="@* | text() | comment() | processing-instruction()">
        <xsl:copy/>
    </xsl:template>
    <!--Permet de copie en appliquant le namespace local de la feuille (défault: tei)-->

    <xsl:variable name="dir"
        >/home/mgl/Bureau/Travail/projets/Biblissima-Text/Transform/test_data2</xsl:variable>

    <xsl:template match="/">
        <!--On crée un doc principal pour vérifier les validités-->
        <xsl:result-document href="{$dir}/main.xml" indent="true">
            <TEI xmlns="http://www.tei-c.org/ns/1.0" xml:lang="es">
                <teiHeader>
                    <fileDesc>
                        <titleStmt>
                            <title>Title</title>
                        </titleStmt>
                        <publicationStmt>
                            <p>Publication Information</p>
                        </publicationStmt>
                        <sourceDesc>
                            <p>Information about the source</p>
                        </sourceDesc>
                    </fileDesc>
                </teiHeader>
                <xsl:for-each select="collection(concat($dir, '/xml?*.xml'))">
                    <xsl:variable name="outname">
                        <xsl:value-of
                            select="concat($dir, '/TEI/', substring-before(tokenize(base-uri(), '/')[last()], '.'), '.xml')"
                        />
                    </xsl:variable>
                    <xsl:element name="xi:include"
                        namespace="http://www.w3.org/2001/XInclude">
                        <xsl:attribute name="href" select="$outname"/>
                    </xsl:element>
                </xsl:for-each>
            </TEI>

        </xsl:result-document>

        <xsl:for-each select="collection(concat($dir, '/xml?*.xml'))">

            <xsl:variable name="outname">
                <xsl:value-of
                    select="concat($dir, '/TEI/', substring-before(tokenize(base-uri(), '/')[last()], '.'), '.xml')"
                />
            </xsl:variable>
            <xsl:result-document href="{$outname}" indent="true">
                <xsl:element name="TEI" xmlns="http://www.tei-c.org/ns/1.0">
                    <xsl:apply-templates select="TEI"/>
                </xsl:element>
            </xsl:result-document>
        </xsl:for-each>
    </xsl:template>


    <!--Illustrations, miniatures, rubriques-->
    <xsl:template match="MIN | MIN_equal_ | _equal_MIN | _equal_MIN_equal_">
        <xsl:element name="figure">
            <xsl:attribute name="type">
                <xsl:text>miniature</xsl:text>
            </xsl:attribute>
            <xsl:if test="node()">
                <xsl:element name="ab">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:if>
        </xsl:element>
    </xsl:template>

    <xsl:template match="DIAG | DIAG_equal_ | _equal_DIAG | _equal_DIAG_equal_">
        <xsl:element name="figure">
            <xsl:attribute name="type">
                <xsl:text>diagramme</xsl:text>
            </xsl:attribute>
            <xsl:if test="node()">
                <xsl:element name="ab">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:if>
        </xsl:element>
    </xsl:template>

    <xsl:template match="ILL">
        <xsl:element name="figure">
            <xsl:attribute name="type">
                <xsl:text>illumination</xsl:text>
            </xsl:attribute>
            <xsl:if test="node()">
                <xsl:element name="ab">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:if>
        </xsl:element>
    </xsl:template>


    <xsl:template match="SYMB">
        <xsl:choose>
            <!--Cas particulier: {SYMB. {BLNK.}}, dans MAN, manuscrit pas accessible-->
            <xsl:when test="BLNK">
                <xsl:element name="space"/>
            </xsl:when>
            <!--Cas particulier: {SYMB. {BLNK.}}-->


            <!--{SYMB. <word>} Logiquement, un symbole qui contient une expansion devrait être codé ex > g-->
            <xsl:when test="ex">
                <xsl:element name="choice">
                    <xsl:element name="abbr">
                        <xsl:element name="g"/>
                    </xsl:element>
                    <xsl:element name="expan">
                        <xsl:element name="ex">
                            <xsl:apply-templates select="ex/node()"/>
                        </xsl:element>
                    </xsl:element>
                </xsl:element>
            </xsl:when>
            <!--Logiquement, un symbole qui contient une expansion devrait être codé ex > g-->

            <xsl:otherwise>
                <xsl:element name="g">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:template>




    <xsl:template match="BLNK">
        <xsl:element name="space">
            <xsl:if test="node()">
                <xsl:element name="desc">
                    <xsl:apply-templates/>
                </xsl:element>
            </xsl:if>
        </xsl:element>
    </xsl:template>

    <xsl:template match="RUB">
        <xsl:element name="hi">
            <xsl:attribute name="rend">
                <xsl:text>rubrique</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <!--Cas des initiales qui contiennent une miniature-->
    <xsl:template match="hi[@rend['initiale']][figure[@type = 'miniature']]">
        <xsl:element name="hi">
            <xsl:attribute name="rend">
                <xsl:text>initiale</xsl:text>
            </xsl:attribute>
            <xsl:element name="figure">
                <xsl:attribute name="type">
                    <xsl:text>miniature</xsl:text>
                </xsl:attribute>
                <xsl:value-of select="."/>
            </xsl:element>
        </xsl:element>
    </xsl:template>
    <!--Cas des initiales qui contiennent une miniature-->


    <!--Illustrations, miniatures-->


    <!--Signatures, mots d'appel, titres courants-->

    <!--    -->
    <xsl:template
        match="node()[starts-with(local-name(), 'HD')][matches(local-name(), 'HD\d+')]">
        <xsl:element name="fw">
            <xsl:attribute name="rend">titre-courant</xsl:attribute>
            <xsl:attribute name="n">
                <xsl:value-of select="replace(local-name(), 'HD(\d+)', '$1')"/>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="HD[not(matches(., '^.*\\\s*[cvujilx]+$'))]">
        <xsl:element name="fw">
            <xsl:attribute name="rend">titre-courant</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="HD[matches(., '^.*\\\s*[cvujilx]+$')]">
        <xsl:element name="fw">
            <xsl:attribute name="rend">titre-courant</xsl:attribute>
            <xsl:value-of select="replace(., '\\\s*[cvujilx]+', '')"/>
        </xsl:element>
        <xsl:element name="fw">
            <xsl:attribute name="rend">numerotation-ancienne</xsl:attribute>
            <xsl:value-of select="replace(., '^.*\\\s*([cvujilx]+)$', '$1')"/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="SG">
        <xsl:element name="fw">
            <xsl:attribute name="type">
                <xsl:text>signature</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="CW">
        <xsl:element name="fw">
            <xsl:attribute name="type">
                <xsl:text>réclame</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    <!--Signatures, mots d'appel-->

    <xsl:template match="SHIFTED">
        <!-- <xsl:message>
            <xsl:copy-of select="following-sibling::*[following-sibling::lb[1]]"
            />
        </xsl:message>-->
        <!--Continuer ici-->
    </xsl:template>

    <!--Faire quelque chose de deu<ex>e<choice>
                     <sic>r</sic>
                     <corr/>
                  </choice>
               </ex> ou de 
    
    q<ex>u<choice>
                     <sic>i</sic>
                     <corr/>
                  </choice>e</ex>ras
    
    -->

    <xsl:template match="RMK">
        <xsl:element name="note">
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

    <xsl:template match="CB5">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">quintuple-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>


    <xsl:template match="CB6">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">sextuple-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>


    <xsl:template match="CB7">
        <xsl:element name="cb" namespace="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="type">septimuple-column</xsl:attribute>
        </xsl:element>
        <xsl:apply-templates/>
    </xsl:template>

    <!--Gloses et ajouts-->
    <xsl:template match="AD">
        <xsl:element name="seg">
            <xsl:attribute name="type">
                <xsl:text>addendum</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="GL">
        <xsl:element name="seg">
            <xsl:attribute name="type">
                <xsl:text>glose</xsl:text>
            </xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>
    <!--Gloses et ajouts-->




    <!--Langues-->

    <xsl:variable name="lang-map" as="map(xs:string, xs:string)" select="
            map {
                'LAT': 'lat',
                'HEB': 'heb',
                'PRV': 'pro',
                'PRT': 'por',
                'LAM': 'lfa',
                'ITL': 'ita',
                'GRK': 'gre',
                'GER': 'ger',
                'GAL': 'glg',
                'FRN': 'fre',
                'ENG': 'eng',
                'CAT': 'cat',
                'BAS': 'eus',
                'ARM': 'arc',
                'ARG': 'arg',
                'CAL': 'cld',
                'ARB': 'arb'
            }"/>
    <xsl:key name="lang" match="entry" use="@key"/>


    <xsl:template
        match="LAT | ARM | HEB | PRV | PRT | LAM | ITL | GRK | GER | GAL | FRN | ENG | CAT | BAS | ARA | ARG | ARB | CAL">
        <xsl:element name="foreign">
            <xsl:attribute name="xml:lang" select="$lang-map(local-name())"/>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <!--Langues-->




    <xsl:template match="EDITORIAL_GUESS">
        <xsl:element name="supplied">
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>

    <xsl:template match="SCRIBAL_INSERTION">
        <xsl:element name="add">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>


    <xsl:template match="SCRIBAL_INSERTION_OTHER_HAND">
        <xsl:element name="add">
            <xsl:attribute name="hand">#other</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="SCRIBAL_DELETION">
        <xsl:element name="del">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:apply-templates/>
        </xsl:element>
    </xsl:template>



    <xsl:template match="SCRIBAL_DELETION_OTHER_HAND">
        <xsl:element name="del">
            <xsl:attribute name="hand">#other</xsl:attribute>
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


    <xsl:template match="EDITORIAL_DELETION">
        <xsl:element name="choice">
            <xsl:element name="sic">
                <xsl:apply-templates/>
            </xsl:element>
            <xsl:element name="corr"/>
        </xsl:element>
    </xsl:template>



    <!--Gestion des substitutions-->
    <xsl:template match="
            OTHER_HAND_DELETION[
            following-sibling::node()[1][self::SCRIBAL_INSERTION]
            and
            not(preceding-sibling::node()[1][self::SCRIBAL_INSERTION])
            ]
            |
            SCRIBAL_INSERTION[
            following-sibling::node()[1][self::OTHER_HAND_DELETION]
            and
            not(preceding-sibling::node()[1][self::OTHER_HAND_DELETION])
            ]
            " priority="10">
        <xsl:element name="subst">
            <xsl:attribute name="hand">#other</xsl:attribute>
            <xsl:choose>
                <xsl:when test="self::OTHER_HAND_DELETION">
                    <xsl:element name="del">
                        <xsl:apply-templates/>
                    </xsl:element>
                    <xsl:element name="add">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                </xsl:when>

                <xsl:otherwise>
                    <xsl:element name="add">
                        <xsl:apply-templates/>
                    </xsl:element>
                    <xsl:element name="del">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>


    <xsl:template match="
            SCRIBAL_INSERTION[
            preceding-sibling::node()[1][self::OTHER_HAND_DELETION]
            ]
            |
            OTHER_HAND_DELETION[
            preceding-sibling::node()[1][self::SCRIBAL_INSERTION]
            ]
            " priority="5"/>



    <xsl:template match="
            SCRIBAL_DELETION[
            following-sibling::node()[1][self::SCRIBAL_INSERTION]
            and
            not(preceding-sibling::node()[1][self::SCRIBAL_INSERTION])
            ]
            |
            SCRIBAL_INSERTION[
            following-sibling::node()[1][self::SCRIBAL_DELETION]
            and
            not(preceding-sibling::node()[1][self::SCRIBAL_DELETION])
            ]
            " priority="10">
        <xsl:element name="subst">
            <xsl:attribute name="hand">#self</xsl:attribute>
            <xsl:choose>
                <xsl:when test="self::SCRIBAL_DELETION">
                    <xsl:element name="del">
                        <xsl:apply-templates/>
                    </xsl:element>
                    <xsl:element name="add">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                </xsl:when>

                <xsl:otherwise>
                    <xsl:element name="add">
                        <xsl:apply-templates/>
                    </xsl:element>
                    <xsl:element name="del">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>


    <xsl:template match="
            SCRIBAL_INSERTION[
            preceding-sibling::node()[1][self::SCRIBAL_DELETION]
            ]
            |
            SCRIBAL_DELETION[
            preceding-sibling::node()[1][self::SCRIBAL_INSERTION]
            ]
            " priority="5"/>
    <!--Gestion des substitutions-->



    <!--Gestion des corrections éditoriales-->
    <xsl:template match="
            EDITORIAL_DELETION[
            following-sibling::node()[1][self::EDITORIAL_INSERTION]
            and
            not(preceding-sibling::node()[1][self::EDITORIAL_INSERTION])
            ]
            |
            EDITORIAL_INSERTION[
            following-sibling::node()[1][self::EDITORIAL_DELETION]
            and
            not(preceding-sibling::node()[1][self::EDITORIAL_DELETION])
            ]
            " priority="10">
        <xsl:element name="choice">
            <xsl:choose>
                <xsl:when test="self::EDITORIAL_DELETION">
                    <xsl:element name="corr">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                    <xsl:element name="sic">
                        <xsl:choose>
                            <!--Les suppressions éditoriales qui commencent pas $ concernent un type placé à l'envers-->
                            <xsl:when test="contains(., '$')">
                                <xsl:element name="hi">
                                    <xsl:attribute name="rend">
                                        <xsl:text>inverted-char</xsl:text>
                                    </xsl:attribute>
                                    <xsl:value-of select="translate(., '$', '')"
                                    />
                                </xsl:element>
                                <!--Les suppressions éditoriales qui commencent pas $ concernent un type placé à l'envers-->
                            </xsl:when>
                            <xsl:otherwise>
                                <xsl:apply-templates
                                    select="following-sibling::node()[1]/node()"
                                />
                            </xsl:otherwise>
                        </xsl:choose>
                    </xsl:element>
                </xsl:when>

                <xsl:otherwise>
                    <xsl:element name="sic">
                        <xsl:apply-templates
                            select="following-sibling::node()[1]/node()"/>
                    </xsl:element>
                    <xsl:element name="corr">
                        <xsl:apply-templates/>
                    </xsl:element>
                </xsl:otherwise>
            </xsl:choose>
        </xsl:element>
    </xsl:template>


    <xsl:template match="
            EDITORIAL_INSERTION[
            preceding-sibling::node()[1][self::EDITORIAL_DELETION]
            ]
            |
            EDITORIAL_DELETION[
            preceding-sibling::node()[1][self::EDITORIAL_INSERTION]
            ]
            " priority="5"/>

    <!--Gestion des corrections éditoriales-->






</xsl:stylesheet>
