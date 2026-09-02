import re
import src.transform.utils as utils
from transformers import pipeline
import numpy as np

def retrieve_names(string: str, parser, is_author=False) -> list[dict]:
	"""
	Fonction pour traiter les noms, distinguer les noms et prénoms
	:param string: la chaîne à traiter
	:return: une liste de dictionnaires
	"""

	result = []
	if is_author:
		# Le cas des noms d'auteur
		if "," in string:
			names, function = string.split(",", 1)
		else:
			names, function = string, ""
		# On cherche à identifier des titres royaux
		kings_regexp = re.compile(r'\s[IVX]+[\s,:;]|\s[IVX]+$')
		if re.search(kings_regexp, names):
			return [
				{"surname": names.strip(),
				 "forename": "",
				 "confidence": 1,
				 "function": function.strip()}
			]
		else:
			names = [names]
	else:
		names = string.split(",")
	for name in names:
		if len(name.split()) == 1:
			forename, surname = "", name
			confidence = 0.5
		elif len(name.split()) == 2 and is_author is False:
			forename, surname = name.split()
			confidence = 1
		else:
			parsed = parser(name.lower())
			if len(parsed) == 2 and is_author is False:
				corresponding_entity_fname = next(item for item in parsed if item['entity_group'] == 'FNAME')
				start_fname, end_fname = corresponding_entity_fname['start'], corresponding_entity_fname['end']
				forename = name[start_fname:end_fname]
				corresponding_entity_lname = next(item for item in parsed if item['entity_group'] == 'LNAME')
				start_lname, end_lname = corresponding_entity_lname['start'], corresponding_entity_lname['end']
				surname = name[start_lname:end_lname]
				confidence = 0.9
			else:
				all_labels = [item['entity_group'] for item in parsed]
				# On regarde l'alternance de labels
				n_changes = sum(
					a != b
					for a, b in zip(all_labels, all_labels[1:])
				)
				if n_changes == 1:
					last_fname_span = [item for item in parsed if item['entity_group'] == 'FNAME'][-1]['end']
					forename = name[:last_fname_span]
					surname = name[last_fname_span:]
					confidence = 0.8
				else:
					confidence = 0
					forename = name
					surname = ""
		if is_author is False:
			result.append({
							"forename": forename.strip(),
							"surname": surname.strip(),
							"confidence": confidence
						})
		else:
			result.append({
							"forename": forename.strip(),
							"surname": surname.strip(),
							"function": function.strip(),
							"confidence": confidence
						})



	return result


def retrieve_metadata(file) -> dict:
	"""
	Wrapper pour la récupération de metadonnées
	:param file: le chemin vers le fichier
	:return: un dictionnaire contenant les metadonnées
	"""
	df_oeuvres = utils.import_table_as_dataframe(path="databases/tabla-obras.csv", sep="\t")
	df_codex = utils.import_table_as_dataframe(path="databases/tabla-codices.csv", sep="\t")
	as_list = utils.read_to_lines(file)
	HSMS_ident = as_list[0].replace("{RMK: ", "").replace(".}", "")

	oeuvre_filtree = df_oeuvres[df_oeuvres["HSMS ID"] == HSMS_ident]
	codex_filtre = df_codex[df_codex["HSMS ID"] == HSMS_ident]

	##### Identifiants
	oeuvre_id = oeuvre_filtree["Obra ID"].values[0]
	file_id_hsms = codex_filtre["Abreviatura HSMS"].values[0]
	beta_copid = oeuvre_filtree["BETA copid"].values[0]
	beta_manid = oeuvre_filtree["BETA manid"].values[0]
	beta_cnum = oeuvre_filtree["BETA cnum"].values[0]
	cote = codex_filtre["Signatura"].values[0]
	##### Identifiants

	#### Informations bibliographiques
	bibliotheque_conservation = codex_filtre["Biblioteca"].values[0]
	lien_philobiblon = codex_filtre["PhiloBiblonlink"].values[0]
	digitalisation = codex_filtre["facsímildigital"].values[0]

	#### Informations bibliographiques


	auteur = oeuvre_filtree["Autor"].values[0]
	transcripteur = codex_filtre["transcriptor"].values[0]
	traducteur = oeuvre_filtree["Traductor"].values[0]

	name_parser = pipeline("ner", model="ele-sage/distilbert-base-uncased-name-splitter",
						   aggregation_strategy="simple")
	auteur_parse = retrieve_names(auteur, parser=name_parser, is_author=True)
	transcripteur_parse = retrieve_names(transcripteur, parser=name_parser, is_author=False)
	if isinstance(traducteur, str):
		traducteur_parse = retrieve_names(traducteur, parser=name_parser, is_author=True)
	else:
		traducteur_parse = None

	titre = oeuvre_filtree["Título"].values[0]
	emplacement_oeuvre = oeuvre_filtree["folio"].values[0]
	folio_codex = codex_filtre["número folios"].values[0]
	format = codex_filtre["formato"].values[0]

	debut_production_oeuvre = oeuvre_filtree["OPDT-inicio"].values[0]
	fin_production_oeuvre = oeuvre_filtree["OPDT-fin"].values[0]
	debut_production_codex = codex_filtre["SPDT-inicio"].values[0]
	fin_production_codex = codex_filtre["SPDT-fin"].values[0]
	lieu_production = codex_filtre["Lugar específico de producción"].values[0]
	producteur = codex_filtre["productor específico"].values[0]


	langues = oeuvre_filtree["lengua 1"].values[0], oeuvre_filtree["lengua 2"].values[0]
	type_textuel = oeuvre_filtree["tipo textual"].values[0]
	matiere_1 = oeuvre_filtree["materia 1"].values[0]
	matiere_2 = oeuvre_filtree["materia 2"].values[0]
	matiere_3 = oeuvre_filtree["materia 3"].values[0]
	matiere_4 = oeuvre_filtree["materia 4"].values[0]
	notes_oeuvre_editeur = oeuvre_filtree["notas"].values[0]
	notes_codex_editeur = codex_filtre["notas"].values[0]
	version_OSTA = codex_filtre["versión"].values[0]


if __name__ == '__main__':
	pass