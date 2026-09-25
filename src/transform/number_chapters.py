import sys

import lxml.etree as ET


def add_n(file):
	"""
	Adds the n attribute to the <div> elements
	:return:
	"""
	namespaces = {"tei": "http://www.tei-c.org/ns/1.0"}
	as_tree = ET.parse(file)
	root = as_tree.getroot()
	for idx, div in enumerate(root.xpath("//tei:div[@type='chapitre']", namespaces=namespaces)):
		previous_divisions = len(div.xpath("preceding-sibling::tei:div[@type='chapitre']", namespaces=namespaces))
		first_division = root.xpath("//tei:div[@type='chapitre']", namespaces=namespaces)[0]
		if first_division.attrib.get("n"):
			previous_divisions = previous_divisions + int(first_division.attrib.get("n"))
		else:
			previous_divisions = previous_divisions + 1
		div.set("n", str(previous_divisions))

	as_tree.write(file.replace("structured", "numbered"), pretty_print=True, encoding="utf-8")

if __name__ == '__main__':
	file = sys.argv[1]
	add_n(file)