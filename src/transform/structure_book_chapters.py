import glob
import json
import re
import sys

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


def structure_book(xml_tree):
	preexisting_structure = xml_tree.xpath("descendant::tei:div[@type='livre']", namespaces=namespaces)
	if len(preexisting_structure) != 0:
		first_rubric = preexisting_structure[0].xpath("following::tei:figure[tei:ab/tei:hi[@rend='rubrique']]", namespaces=namespaces)[0]


	# Vérifier que le premier texte de la pied_mouch n'est pas ignoré.
	following_siblings = first_rubric.xpath("following-sibling::*",
												namespaces=namespaces)
	localisation_dict = {first_rubric: []}

	# for node in following_siblings:
	current_node = first_rubric
	for index, node in enumerate(following_siblings):
		if node.xpath("self::tei:figure[descendant::tei:hi[@rend='rubrique']]", namespaces=namespaces):
			localisation_dict[node] = []
			current_node = node
		else:
			localisation_dict[current_node].append(node)
	parent_element = first_rubric.xpath("parent::tei:div", namespaces=namespaces)[0]
	print(parent_element)
	for heading, following_nodes in localisation_dict.items():
		div = ET.Element("div")
		div.set("type", "livre")
		parent_element.append(div)
		heading.tag = ET.QName(heading).localname
		head = ET.Element("head")
		head.append(heading)
		par = ET.Element("p")
		par.extend(following_nodes)
		div.append(head)
		div.append(par)
		div.tag = ET.QName(div).localname
	return xml_tree


def structure_chapters(path):
	xml_tree = ET.parse(path)
	xml_tree = structure_book(xml_tree)
	# Problème de namespace
	books = xml_tree.xpath("descendant::div[@type='livre'] | descendant::tei:div[@type='livre']", namespaces=namespaces)
	for idx, book in enumerate(books):
		print(f"Treating book {idx + 1}")
		try:
			first_rubric = book.xpath("descendant::tei:hi[@rend='rubrique'][not(ancestor::figure)]", namespaces=namespaces)[0]
		except IndexError:
			print("Error")
			# Create a default div if no rubric is found
			parent_element = book.xpath("tei:div", namespaces=namespaces)[0]
			subdiv = ET.Element("div")
			parent_element.append(subdiv)
			subdiv.set("type", "chapitre")
			p = ET.Element("p")
			subdiv.append(p)

			# Add all content to the default paragraph
			for node in book.iterchildren():
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
		# Vérifier que le premier texte de la rubrique n'est pas ignoré.
		following_siblings = first_rubric.xpath("following-sibling::*", namespaces=namespaces)
		localisation_dict = {first_rubric: []}

		# for node in following_siblings:
		current_node = first_rubric
		for index, node in enumerate(following_siblings):
			if node.tag == "{http://www.tei-c.org/ns/1.0}hi" and node.attrib['rend'] == 'rubrique':
				regexp = re.compile(r"[ICXV]+")
				tail = node.xpath("following::tei:lb", namespaces=namespaces)[0].tail
				if tail is None or re.search(regexp, tail) is None:
					print("IGNORED")
					print(tail)
					localisation_dict[current_node].append(node)
					continue
				else:
					print("OK")
					print(tail)
					pass
				if node.xpath("contains(preceding-sibling::tei:hi[@rend='rubrique'][1], '+') or contains(preceding-sibling::tei:hi[@rend='rubrique'][1], '⇒')", namespaces=namespaces):
					localisation_dict[current_node].append(node)
				else:
					localisation_dict[node] = []
					current_node = node
			else:
				localisation_dict[current_node].append(node)
		# with open("/home/mgl/Documents/nodes.json", "w") as output_json:
		# 	json.dump(localisation_dict, output_json)

		parent_element = book
		for idx, (rubric, following_nodes) in enumerate(localisation_dict.items()):
			rubric.tag = ET.QName(rubric).localname
			subdiv = ET.Element("div")
			parent_element.append(subdiv)
			subdiv.set("type", "chapitre")
			subdiv.set("n", str(idx + 1))
			head = ET.SubElement(subdiv, "head")
			head.append(rubric)
			p = ET.Element("p")
			subdiv.append(p)
			p.extend(following_nodes)

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
	serialize(path=path, xml_tree=xml_tree)


def serialize(path, xml_tree):
	basename = path.split("/")[-1]
	out_path = f"/home/mgl/Bureau/Travail/projets/Biblissima-Text/data/Biblissima-Textes/structured/{basename}"
	print(f"Writing to {out_path}")
	with open(out_path, "w") as output_xml:
		output_xml.write(ET.tostring(xml_tree, pretty_print=True, encoding="utf8").decode("utf8"))




if __name__ == '__main__':
	path = sys.argv[1]
	structure_chapters(path)