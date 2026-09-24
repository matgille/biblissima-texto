import glob
import json

import lxml.etree as ET

namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
ET.register_namespace("tei", "http://www.tei-c.org/ns/1.0")

def unwrap(node):
	"""Remplace `node` par son contenu dans le parent."""
	parent = node.getparent()
	# le texte avant le 1er enfant de node est collé à ce qui précède
	prev = node.getprevious()
	if prev is not None:
		prev.tail = (prev.tail or "") + (node.text or "")
	else:
		parent.text = (parent.text or "") + (node.text or "")

	# déplacer les enfants de node juste avant node (= à sa place)
	for child in list(node):
		node.addprevious(child)

	# le tail de node est collé à ce qui précède maintenant
	prev = node.getprevious()
	if prev is not None:
		prev.tail = (prev.tail or "") + (node.tail or "")
	else:
		parent.text = (parent.text or "") + (node.tail or "")

	parent.remove(node)


def structure(path):
	xml_tree = ET.parse(path)
	body = xml_tree.xpath("descendant::tei:body", namespaces=namespaces)[0]
	try:
		first_rubric = body.xpath("descendant::tei:hi[@rend='rubrique']", namespaces=namespaces)[0]
	except IndexError:
		# Create a default div if no rubric is found
		parent_element = body.xpath("tei:div", namespaces=namespaces)[0]
		subdiv = ET.Element("div")
		parent_element.append(subdiv)
		subdiv.set("type", "chapitre")
		p = ET.Element("p")
		subdiv.append(p)

		# Add all content to the default paragraph
		for node in body.iterchildren():
			if node.tag == "{http://www.tei-c.org/ns/1.0}div":
				continue  # Skip existing divs
			try:
				node.tag = ET.QName(node).localname
			except (ValueError, AttributeError):
				pass
			p.append(node)

		basename = path.split("/")[-1]
		out_path = f"/home/mgl/Bureau/Travail/projets/Biblissima-Text/data/Biblissima-Textes/structured/{basename}"
		with open(out_path, "w") as output_xml:
			output_xml.write(ET.tostring(xml_tree, pretty_print=True, encoding="utf8").decode("utf8"))
		return

	# Le tail de la rubrique n'est pas pris en compte
	first_rubric_tail = first_rubric.tail
	# Vérifier que le premier texte de la rubrique n'est pas ignoré.
	following_siblings = first_rubric.xpath("following-sibling::*[not(ancestor::tei:hi[@rend='rubrique'])]", namespaces=namespaces)
	localisation_dict = {first_rubric: []}

	# for node in following_siblings:
	current_node = first_rubric
	for index, node in enumerate(following_siblings):
		if node.tag == "{http://www.tei-c.org/ns/1.0}hi" and node.attrib['rend'] == 'rubrique':
			if node.xpath("contains(preceding-sibling::tei:hi[@rend='rubrique'][1], '+') or contains(preceding-sibling::tei:hi[@rend='rubrique'][1], '⇒')", namespaces=namespaces):
				localisation_dict[current_node].append(node)
			else:
				localisation_dict[node] = []
				current_node = node
		else:
			localisation_dict[current_node].append(node)
	print(len(localisation_dict))
	# with open("/home/mgl/Documents/nodes.json", "w") as output_json:
	# 	json.dump(localisation_dict, output_json)

	parent_element = body.xpath("tei:div", namespaces=namespaces)[0]
	for rubric, following_nodes in localisation_dict.items():
		rubric.tag = ET.QName(rubric).localname
		subdiv = ET.Element("div")
		parent_element.append(subdiv)
		subdiv.set("type", "chapitre")
		head = ET.SubElement(subdiv, "head")
		head.append(rubric)
		p = ET.Element("p")
		head.addnext(p)

		# Gestion des noeuds non textuels
		for idx, node in enumerate(following_nodes):
			try:
				node.tag = ET.QName(node).localname
			except (ValueError, AttributeError):
				pass
			try:
				p.append(node)
			except TypeError as e:
				print(e)
				print(f"Erreur sur |{node}|, vérifiez que le noeud textuel a été correctement placé")
				print(idx)
				print(following_nodes)
				if node is None:
					continue
				else:
					if isinstance(node, str):
						p.text = node
						continue
				try:
					following_nodes[idx - 1].tail = following_nodes[idx - 1].tail + node
				except (TypeError, AttributeError) as e:
					print(e)
					print(f"Tail |{following_nodes[idx - 1]}| non injecté")
					print(following_nodes[idx - 1].tail)
					print(ET.tostring(following_nodes[idx - 1]))
					continue

	# On va replacer les tei:hi
	target_rubrics = parent_element.xpath("descendant::p/descendant::hi[@rend='rubrique']", namespaces=namespaces)
	for rubrique in target_rubrics:
		preceding_rubric = rubrique.xpath("ancestor::div[@type='chapitre']/head/hi", namespaces=namespaces)[0]
		lb = ET.Element("lb")
		lb.set("break", "yes")
		preceding_rubric.set("type", "merged")
		preceding_rubric.append(lb)
		preceding_rubric.append(rubrique)
		unwrap(rubrique)

	basename = path.split("/")[-1]
	out_path = f"/home/mgl/Bureau/Travail/projets/Biblissima-Text/data/Biblissima-Textes/structured/{basename}"
	print(f"Writing to {out_path}")
	with open(out_path, "w") as output_xml:
		output_xml.write(ET.tostring(xml_tree, pretty_print=True, encoding="utf8").decode("utf8"))




if __name__ == '__main__':
	path = "test_data/TEI/*.xml"
	for file in glob.glob(path):
		print(file)
		structure(file)