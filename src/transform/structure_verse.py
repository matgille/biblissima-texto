import glob
import json
import sys

import lxml.etree as ET

def replace_element(parent, old_element, new_element):
	"""
	Remplace un élément enfant par un nouvel élément dans un parent donné.

	Args:
		parent: L'élément parent contenant l'élément à remplacer
		old_element: L'élément à remplacer
		new_element: Le nouvel élément à insérer
	"""
	# Trouver l'index de l'ancien élément
	index = parent.index(old_element)

	# Supprimer l'ancien élément
	parent.remove(old_element)

	# Insérer le nouvel élément à la même position
	parent.insert(index, new_element)

namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
ET.register_namespace("tei", "http://www.tei-c.org/ns/1.0")


def structure_stroph(lineGroup):
	try:
		first_node_in_stroph = lineGroup.xpath("descendant::lb", namespaces=namespaces)[0]
	except IndexError:
		first_node_in_stroph = lineGroup.xpath("descendant::hi[@rend='initiale']", namespaces=namespaces)[0]


	# Vérifier que le premier texte de la pied_mouch n'est pas ignoré.
	following_siblings = first_node_in_stroph.xpath("following-sibling::*",
												namespaces=namespaces)
	localisation_dict = {first_node_in_stroph: []}

	# for node in following_siblings:
	current_node = first_node_in_stroph
	for index, node in enumerate(following_siblings):
		if node.tag == "{http://www.tei-c.org/ns/1.0}lb":
			localisation_dict[node] = []
			current_node = node
		else:
			localisation_dict[current_node].append(node)
	print(len(localisation_dict))

	for lb, following_nodes in localisation_dict.items():
		lb.tag = ET.QName(lb).localname
		verse = ET.Element("l")
		verse.append(lb)
		[verse.append(item) for item in following_nodes]
		lineGroup.append(verse)
	return lineGroup

def structure(path):
	xml_tree = ET.parse(path)
	body = xml_tree.xpath("descendant::tei:body", namespaces=namespaces)[0]
	first_pied_mouch = body.xpath("descendant::tei:lb", namespaces=namespaces)[0]


	# Le tail de la pied_mouch n'est pas pris en compte
	# Vérifier que le premier texte de la pied_mouch n'est pas ignoré.
	following_siblings = first_pied_mouch.xpath("following-sibling::*", namespaces=namespaces)
	localisation_dict = {first_pied_mouch: []}

	# for node in following_siblings:
	current_node = first_pied_mouch
	for index, node in enumerate(following_siblings):
		if (node.xpath("self::tei:lb", namespaces=namespaces) and node.xpath("following-sibling::node()[1][self::tei:hi[@rend='initiale']]", namespaces=namespaces)) or (node.xpath("self::tei:lb", namespaces=namespaces) and node.xpath("following-sibling::node()[1][self::tei:g[@ref='#calderon1']]", namespaces=namespaces)):
			localisation_dict[node] = []
			current_node = node
		else:
			localisation_dict[current_node].append(node)
	print(len(localisation_dict))

	parent_element = body.xpath("tei:div", namespaces=namespaces)[0]
	for idx, (linebreak, following_nodes) in enumerate(localisation_dict.items()):
		print(idx)
		linebreak.tag = ET.QName(linebreak).localname
		strophe = ET.Element("lg")
		strophe.append(linebreak)
		[strophe.append(item) for  item in following_nodes]
		parent_element.append(strophe)

	all_lg = body.xpath("//lg", namespaces=namespaces)
	for lg in all_lg:
		replace_element(lg.getparent(), lg, structure_stroph(lg))

	basename = path.split("/")[-1]
	out_path = f"/home/mgl/Bureau/Travail/projets/Biblissima-Text/data/Biblissima-Textes/structured/{basename}"
	print(f"Writing to {out_path}")
	with open(out_path, "w") as output_xml:
		output_xml.write(ET.tostring(xml_tree, pretty_print=True, encoding="utf8").decode("utf8"))




if __name__ == '__main__':
	path = sys.argv[1]
	structure(path)