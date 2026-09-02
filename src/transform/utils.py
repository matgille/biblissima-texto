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