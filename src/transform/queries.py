import json
import re
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import sys
import requests
from lxml import html


def retrieve_msContents(identifier):
    """
    On part du point d'entrée CNUM pour récupérer l'incipit et l'explicit du fragment.
    :param identifier:
    :return:
    """
    time.sleep(1)
    SPARQL_ENDPOINT = "https://database.factgrid.de/sparql"

    if isinstance(identifier, float):
        identifier = str(round(identifier))

    query = f"""
SELECT ?cnum ?cnumLabel ?segmentationLabel ?incipit ?explicit ?unit_incipit ?unit_explicit ?title WHERE {{
  ?cnum wdt:P476 "BETA cnum {identifier}" .
  OPTIONAL {{
    ?cnum p:P543 ?stmt .
    ?stmt ps:P543 ?segmentation .
    OPTIONAL {{ ?stmt pq:P70  ?incipit . }}
    OPTIONAL {{ ?stmt pq:P602 ?explicit . }}
    
  }}
  OPTIONAL {{
            ?cnum wdt:P590 ?work .          # 1er saut : cnum -> œuvre (texid)
            OPTIONAL {{ ?work wdt:P11 ?title . }}   # 2e saut : titre de l'œuvre
            ?work ps:P543 ?segmentation .
                OPTIONAL {{ ?work pq:P70  ?unit_incipit . }}
                OPTIONAL {{ ?work pq:P602 ?unit_explicit . }}
          }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en,de,fr". }}
}}
"""
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query},
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "Biblissima-texte/1.0 (contact matthias.gille-levenson@ens-lyon.fr)",
        },
        timeout=10,
    )

    data = r.json()
    try:
        unit_incipit = data['results']['bindings'][0]['unit_incipit']['value']
    except (KeyError, IndexError):
        unit_incipit = None
    try:
        unit_explicit = data['results']['bindings'][0]['unit_explicit']['value']
    except (KeyError, IndexError):
        unit_explicit = None
    try:
        unit_title = data['results']['bindings'][0]['title']['value']
    except (KeyError, IndexError):
        unit_title = None
    try:
        factgrid_cnum_id = data['results']['bindings'][0]['cnum']['value'].split("/")[-1]
    except (KeyError, IndexError):
        factgrid_cnum_id = None
    try:
        incipit = data['results']['bindings'][0]['incipit']['value']
    except (IndexError, KeyError):
        incipit = "Unknown"
    try:
        explicit = data['results']['bindings'][-1]['explicit']['value']
    except KeyError:
        try:
            explicit = data['results']['bindings'][-1]['incipit']['value']
        except KeyError:
            explicit = "Unknown"
    except IndexError:
        explicit = "Unknown"

    # Des fois on n'a que l'incipit.
    if incipit == explicit and len(data['results']['bindings']) == 1:
        explicit = "Unknown"

    return incipit, explicit, factgrid_cnum_id, unit_title, unit_incipit, unit_explicit


def search_factgrid_beta_id(identifier, type_identifier):
    SPARQL_ENDPOINT = "https://database.factgrid.de/sparql"

    if isinstance(identifier, float):
        identifier = str(round(identifier))
    philo_id = f"BETA {type_identifier} {identifier}"  # ex. "BETA manid 1788"
    print(philo_id)

    query = f"""
SELECT ?ms ?msLabel ?philoId ?typeLabel
       ?institution ?institutionId ?institutionLabel ?institutionPhiloId
       ?date ?langueLabel ?supportLabel ?folios ?numerisation
WHERE {{
  ?ms wdt:P476 "{philo_id}" .
  BIND("{philo_id}" AS ?philoId)
  OPTIONAL {{ ?ms wdt:P2 ?type . }}
  OPTIONAL {{ ?ms wdt:P329 ?institution . }}
  OPTIONAL {{ ?institution wdt:P476 ?institutionPhiloId . }}
  OPTIONAL {{ ?ms wdt:P95  ?origine . }}
  OPTIONAL {{ ?ms wdt:P106 ?date . }}
  OPTIONAL {{ ?ms wdt:P18  ?langue . }}
  OPTIONAL {{ ?ms wdt:P480 ?support . }}
  OPTIONAL {{ ?ms wdt:P107 ?folios . }}
  OPTIONAL {{ ?ms wdt:P138 ?numerisation . }}
  BIND(REPLACE(STR(?institution), "https://database.factgrid.de/entity/", "") AS ?institutionId)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en,de,fr". }}
}}
"""
    r = requests.get(
        SPARQL_ENDPOINT,
        params={"query": query},
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "Biblissima-texte/1.0 (contact matthias.gille-levenson@ens-lyon.fr)",
        },
        timeout=10,
    )

    data = r.json()
    cols = data["head"]["vars"]
    reordered = [
        {c: b.get(c, {}).get("value") for c in cols}
        for b in data["results"]["bindings"]
    ]
    libraries_id = {}
    # On a plusieurs résultats car on a trois identifiants de bibliothèque différents: BETA, BITECA, BITAGAP
    if reordered:
        for item in reordered:
            ms = item['ms']
            institution = item['institution']
            current_philoidtype = item['institutionPhiloId'].split()[0]
            libraries_id[current_philoidtype] = item['institutionPhiloId'].split()[-1]
        return libraries_id, ms, institution
    else:
        return None

def search_philobiblon(url, cnum):
    """
    Cette fonction cherche dans l'ancienne version de philobiblon (on ne peut pas requêter la nouvelle avec GET) le titre du témoin dans le mss.
    :param url:
    :param cnum:
    :return:
    """
    print(f"Searching for {url} and cnum {cnum}")
    response = requests.get(url)
    response.raise_for_status()
    tree = html.fromstring(response.content)
    # Trouver le <td> contenant "BETA cnum 208"
    td_cnum = tree.xpath(
        f"//td[contains(normalize-space(.), 'BETA cnum {cnum}')]"
    )
    if not td_cnum:
        print(f"BETA cnum {cnum} introuvable")
        return "Unknown", "Unknown"
    td_cnum = td_cnum[0]
    # Premier <td> suivant contenant "texid"
    td_texid = td_cnum.xpath(
        "following::td[contains(normalize-space(.), 'texid')][1]"
    )

    if not td_texid:
        return "Unknown", "Unknown"

    if td_cnum:
        td_title = td_cnum.xpath(
            "following::td[contains(normalize-space(.), 'Title(s) in witness')][1]/following::td"
        )
        try:
            title = td_title[0].text_content().strip()
        except IndexError:
            title = None
    else:
        print("No title found")
        title = None

    regexp = re.compile("texid (\d+)")
    td_texid = td_texid[0].text_content().strip()
    texid = re.search(regexp, td_texid).group(1)
    return texid, title
