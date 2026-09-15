import json
import re
import time
from SPARQLWrapper import SPARQLWrapper, JSON
import sys
import requests
from lxml import html


def search_factgrid(identifier, type_identifier):
    time.sleep(1)
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
    with open("/home/mgl/Documents/test.json", "w")  as output_json:
        json.dump(data, output_json)
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
    return texid, codex_title, unit_incipit
