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
SELECT ?cnum ?cnumLabel ?segmentation ?segmentationLabel ?wseg ?wsegLabel ?classe ?classeLabel
       ?unit_incipit ?unit_explicit ?title ?work_id ?work_incipit ?work_explicit WHERE {{
  ?cnum wdt:P476 "BETA cnum {identifier}" .

  OPTIONAL {{
    ?cnum p:P543 ?stmt .
    ?stmt ps:P543 ?segmentation .
    OPTIONAL {{ ?stmt pq:P70  ?unit_incipit . }}
    OPTIONAL {{ ?stmt pq:P602 ?unit_explicit . }}
    OPTIONAL {{ ?segmentation wdt:P2 ?classe . }}      # classe du segment (rubric/main text/colophon)
  }}

  OPTIONAL {{
    ?cnum wdt:P590 ?work .
    OPTIONAL {{ ?work wdt:P11 ?title . }}
    OPTIONAL {{
      ?work p:P543 ?wstmt .
      ?wstmt ps:P543 ?wseg .                       
      OPTIONAL {{ ?wstmt pq:P70  ?work_incipit . }}
      OPTIONAL {{ ?wstmt pq:P602 ?work_explicit . }}
      OPTIONAL {{ ?wstmt pq:P602 ?work_colophon . }}
    }}
    OPTIONAL {{ ?work wdt:P476 ?work_philo_id . }}
  }}

  BIND(REPLACE(STR(?work), "https://database.factgrid.de/entity/", "") AS ?work_id)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es, en". }}
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
        colophon = next(item['unit_incipit']['value']
                            for item in data['results']['bindings']
                            if item["segmentationLabel"]["value"] == "Colofón")
    except (KeyError, IndexError, StopIteration):
        colophon = None
    try:
        work_id = data['results']['bindings'][0]['work_id']['value']
    except (KeyError, IndexError):
        work_id = None
    try:
        unit_incipit = next(item['unit_incipit']['value']
                            for item in data['results']['bindings']
                            if item["segmentationLabel"]["value"] == "Texto principal")
    except (KeyError, IndexError, StopIteration):
        try:
            unit_incipit = next(item['work_incipit']['value']
                                for item in data['results']['bindings']
                                if item["wsegLabel"]["value"] == "Texto principal")
        except (KeyError, IndexError, StopIteration):
            unit_incipit = None
    try:
        unit_explicit = next(item['unit_explicit']['value']
                            for item in data['results']['bindings']
                            if item["segmentationLabel"]["value"] == "Texto principal")
    except (KeyError, IndexError, StopIteration):
        try:
            unit_explicit = next(item['work_explicit']['value']
                                for item in data['results']['bindings']
                                if item["wsegLabel"]["value"] == "Texto principal")
        except (KeyError, IndexError, StopIteration):
            unit_explicit = None
    try:
        unit_title = data['results']['bindings'][0]['title']['value']
    except (KeyError, IndexError):
        unit_title = None
    try:
        factgrid_cnum_id = data['results']['bindings'][0]['cnum']['value'].split("/")[-1]
    except (KeyError, IndexError):
        factgrid_cnum_id = None

    return factgrid_cnum_id, work_id, unit_title, unit_incipit, unit_explicit, colophon


def search_factgrid_beta_id(identifier, type_identifier):
    SPARQL_ENDPOINT = "https://database.factgrid.de/sparql"

    if isinstance(identifier, float):
        identifier = str(round(identifier))
    philo_id = f"BETA {type_identifier} {identifier}"  # ex. "BETA manid 1788"
    print(philo_id)

    query = f"""
SELECT ?ms ?philoId
       ?institution ?institutionId ?institutionPhiloId
       ?msName
       (GROUP_CONCAT(DISTINCT ?typeLabel; separator=" | ") AS ?types)
WHERE {{
  ?ms wdt:P476 "{philo_id}" .
  BIND("BETA manid 2874" AS ?philoId)
  OPTIONAL {{ ?ms wdt:P2 ?type . }}
  OPTIONAL {{ ?ms wdt:P329 ?institution . }}
  OPTIONAL {{ ?institution wdt:P476 ?institutionPhiloId . }}
  OPTIONAL {{ ?ms rdfs:label ?msName . FILTER(LANG(?msName) = "es") }}
  BIND(REPLACE(STR(?institution), "https://database.factgrid.de/entity/", "") AS ?institutionId)
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "es,en,de,fr". }}
}}
GROUP BY ?ms ?philoId ?institution ?institutionId ?institutionPhiloId ?msName
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
        results = data["results"]["bindings"][0]
    except (IndexError, KeyError):
        results = None
    if results:
        ms = results['ms']["value"]
        institution = results['institution']["value"]
        msName = results['msName']["value"]
        libraries_id = results['institutionPhiloId']["value"]
        return libraries_id, ms, institution, msName
    else:
        return None

def search_philobiblon(url, cnum):
    """
    Cette fonction cherche dans l'ancienne version de philobiblon le titre du témoin dans le mss.
    :param url:
    :param cnum:
    :return:
    """
    # print(f"Searching for {url} and cnum {cnum}")
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

    if td_cnum is not None:
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
