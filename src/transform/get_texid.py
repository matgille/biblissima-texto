import re

import requests
from lxml import html


def search_texid(url, cnum):
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
        return "Unknown"
    td_cnum = td_cnum[0]
    # Premier <td> suivant contenant "texid"
    td_texid = td_cnum.xpath(
        "following::td[contains(normalize-space(.), 'texid')][1]"
    )

    if not td_texid:
        return "Unknown"

    regexp = re.compile("texid (\d+)")
    td_texid = td_texid[0].text_content().strip()
    texid = re.search(regexp, td_texid).group(1)
    return texid
