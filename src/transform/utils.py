import glob
import pandas as pd
import lxml.etree as ET


def remove_unnecesary_lb_nodes(xml_tree):
	query = "//lb[following-sibling::node()[1][self::CW or self::CB1 or self::CB2 or self::CB3 or self::CB4 or self::CB5 or self::CB6 or self::CB7 or self::CB8 or self::pb or self::HD or self::fw or (self::text() and normalize-space() = '')]]"
	lb_nodes = xml_tree.xpath(query, namespaces={"tei": "http://www.tei-c.org/ns/1.0"})
	for lb in lb_nodes:
		print("Removing node.")
		lb.getparent().remove(lb)
	if len(xml_tree.xpath(query, namespaces={"tei": "http://www.tei-c.org/ns/1.0"})) != 0:
		xml_tree = remove_unnecesary_lb_nodes(xml_tree)
	return xml_tree


def read_to_lines(path: str) -> list:
	"""
	Lit un fichier et le place dans une liste
	:param path: chemin du fichier
	:return: la liste voulue
	"""
	with open(path, "r") as input_file:
		return [line.replace("\n", "") for line in input_file.readlines()]


def import_table_as_dataframe(path: str, sep:str) -> pd.DataFrame:
	"""
	Import d'une table csv en objet DataFrame
	:param path: chemin vers le fichier
	:param sep: le délimiteur
	:return: le dataframe
	"""
	return pd.read_csv(path, delimiter=sep)


def process_date(node, date_debut, date_fin):
	if "ca." in date_debut or (date_fin and "ca." in date_fin and date_debut != date_fin):
		node.set("cert", "medium")
		node.text = f"{date_debut} - {date_fin}"
		node.set("notBefore-iso", date_debut.replace("ca.", "").strip())
		node.set("notAfter-iso", date_fin.replace("ca.", "").strip())
	# Il manque le cas où les date sont égale avec ca.
	elif date_debut == date_fin and "a quo" and "ad quem" not in date_debut:
		node.text = date_debut
		node.set("when", date_debut)
	elif "a quo" in date_debut:
		node.set("notBefore-iso", date_debut.replace("a quo", "").strip())
		node.text = date_debut
		if "ad quem" in date_fin:
			node.set("notAfter-iso", date_fin.replace("ad quem", "").strip())
			node.text = node.text + f"- {date_fin}"
	elif date_fin and "ad quem"  in date_fin:
		node.set("notAfter-iso", date_fin.replace("ad quem", "").strip())
		node.text = date_fin
		if "a quo" in date_debut:
			node.set("notBefore-iso", date_fin.replace("ad quem", "").strip())
			node.text = f"{date_debut} -" + node.text
	else:
		node.text = ""
		if date_debut:
			node.set("notBefore-iso", date_debut)
			node.text = f"{date_debut}"
		if date_fin:
			node.set("notAfter-iso", date_fin)
			node.text = f"{node.text} - {date_fin}"
	return node


def write_tree(tree, path):
	with open(path, "w") as output_file:
		output_file.write(ET.tostring(tree, pretty_print=True).decode())