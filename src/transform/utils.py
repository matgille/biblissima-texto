import glob
import pandas as pd



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
	if "ca." in date_debut or "ca." in date_fin and date_debut != date_fin:
		node.set("cert", "medium")
		node.text = f"{date_debut} {date_fin}"
		node.set("atLeast", date_debut.replace("ca.", "").strip())
		node.set("atMost", date_fin.replace("ca.", "").strip())
	# Il manque le cas où les date sont égale avec ca.
	elif date_debut == date_fin and "a quo" and "ad quem" not in date_debut:
		node.text = date_debut
		node.set("when", date_debut)
	elif "a quo" in date_debut:
		node.set("atLeast", date_debut.replace("a quo", "").strip())
		node.text = date_debut
		if "ad quem" in date_fin:
			node.set("atMost", date_fin.replace("ad quem", "").strip())
			node.text = node.text + f" {date_fin}"
	elif "ad quem" in date_fin:
		node.set("atMost", date_fin.replace("ad quem", "").strip())
		node.text = date_fin
		if "a quo" in date_debut:
			node.set("atLeast", date_fin.replace("ad quem", "").strip())
			node.text = f"{date_debut} " + node.text
	else:
		node.set("atLeast", date_debut)
		node.set("atMost", date_fin)
		node.text = f"{date_debut} - {date_fin}"
	return node