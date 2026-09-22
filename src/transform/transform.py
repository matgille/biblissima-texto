import re
import time

import src.transform.queries as queries
import src.transform.metadata as metadata
import src.transform.utils as utils
import src.transform.txt_to_xml as conversion
import tqdm
from transformers import pipeline
import glob
import sys
import lxml.etree as ET
import pandas as pd


def create_multiple_msItem(codex_ident, xml_tree):
	"""
	Récupère toutes les métadonnées pour les oeuvres à plusieurs unités (lettres, poésie, glose)
	:return:
	"""

	df_oeuvres = utils.import_table_as_dataframe(path="databases/tabla-obras.csv", sep="\t")
	df_codices = utils.import_table_as_dataframe(path="databases/tabla-codices.csv", sep="\t")

	oeuvre_filtree_codex = df_oeuvres[df_oeuvres["HSMS ID"] == codex_ident]
	codex_filtre = df_codices[df_codices["HSMS ID"] == codex_ident]

	factgrid_endpoint = "https://database.factgrid.de/"
	msContents = ET.Element("msContents")
	origin = ET.Element("origin")

	for idx, work in oeuvre_filtree_codex.iterrows():

		work_id = work["Obra ID"]
		# Informations historiques

		origDate = ET.Element("origDate")
		origDate.set("corresp", f"#{work_id}")
		date_debut = codex_filtre["SPDT-inicio"].values[0]
		date_fin = codex_filtre["SPDT-fin"].values[0]
		origDate = utils.process_date(origDate, date_debut, date_fin)
		origin.append(origDate)

		# Information de texte
		beta_cnum_val = work["BETA cnum"]
		disable_queries = False
		if not pd.isna(beta_cnum_val):
			if disable_queries is True:
				incipit_unit, explicit_unit, factgrid_cnum_val, unit_title = "Unknown", "Unknown", "Unknown", "Unknown"
			else:
				(

					factgrid_cnum_val,
					factgrid_word_id,
					unit_title,
					incipit_unit,
					explicit_unit,
					colophon
				) = queries.retrieve_msContents(
					identifier=beta_cnum_val)
		else:
			incipit_unit, explicit_unit, factgrid_cnum_val = "Unknown", "Unknown", "Unknown"

		item = ET.SubElement(msContents, "msItem")
		item.set("{http://www.w3.org/XML/1998/namespace}id", work_id)
		locus = ET.SubElement(item, "locus")
		locus.text = work["folio"]
		colophon_element = ET.SubElement(item, "colophon")
		colophon_element.text = colophon
		incipit = ET.SubElement(item, "incipit")
		incipit.text = incipit_unit
		explicit = ET.SubElement(item, "explicit")
		explicit.text = explicit_unit
		if not pd.isna(beta_cnum_val) and beta_cnum_val:
			title = ET.SubElement(item, "title")
			title.text = unit_title
			beta_cnum = ET.SubElement(item, "idno")
			beta_cnum.set("type", "beta-cnum")
			beta_cnum.text = str(int(beta_cnum_val))
			cnum_factgrid = ET.SubElement(item, "idno")
			beta_cnum.set("type", "beta-cnum")
			cnum_factgrid.text = factgrid_cnum_val
			cnum_factgrid.set("type", "factgrid-cnum")
			cnum_factgrid.set("corresp", f"{factgrid_endpoint}entity/{factgrid_cnum_val}")
		# Si on n'a pas de beta cnum, on peut récupérer le titre de l'unité grâce aux notes dans le texte
		else:
			print(work_id)
			regexp = re.compile(rf"<RMK>{work_id}: ([^<]+)</RMK>")
			titre = re.search(regexp, xml_tree).group(1)
			title = ET.SubElement(item, "title")
			title.text = titre
	return msContents, origin

# TODO: manuscrits composites avec ordre altéré (0089: fin du Libro de Alexandre après intercalation d'un autre item)
def work_loop(files):
	name_parser = pipeline("ner", model="ele-sage/distilbert-base-uncased-name-splitter",
						   aggregation_strategy="simple")
	df_oeuvres = utils.import_table_as_dataframe(path="databases/tabla-obras.csv", sep="\t")
	n = 0
	splits_exceptions = ["HSMS-0037", "HSMS-0190", "HSMS-0248"]
	skip_metadata_retrieval = False
	previous_work = None
	for idx, work in df_oeuvres.iterrows():
		# if work['HSMS ID'] != "HSMS-0337":
		# 	continue
		# On vérifie que le manuscrit contient plusieurs oeuvres
		n += 1
		print(n)
		# if idx < 50:
		# 	continue
		if n < 1960:
			continue
		print(f"Current hsms id: {work['HSMS ID']}. Previous work: {previous_work}")
		if skip_metadata_retrieval is True and previous_work == work['HSMS ID']:
			print("Passing")
			continue
		else:
			skip_metadata_retrieval = False
		previous_work = work['HSMS ID']
		work_id = work["Obra ID"]
		mss_id = "-".join(work_id.split("-")[:-1])
		contains_multiple_works = len(df_oeuvres[df_oeuvres['HSMS ID'].str.contains(mss_id)]) > 1


		filename = work['Abreviatura HSMS']
		corresponding_file = next(file for file in files if f"TEXT.{filename}.txt" in file)
		file_as_list = utils.read_to_lines(corresponding_file)
		regexp_multiple_works = re.compile(r"HSMS-\d{4}-(\d{4})")
		print(f"Metadata_retrieval {n}")
		orig_text = "\n".join(file_as_list[6:])



		# On splitte après la transformation en xml-tei, c'est beaucoup plus simple.
		xml_text = conversion.convert(orig_text, id=work_id)
		md = metadata.retrieve_metadata(file_as_list, name_parser, work_id=work_id, disable_queries=False)
		print(md["file_id_hsms"])
		print(md["oeuvre_id"])
		matieres = [md[f"matiere_{str(n)}"] for n in range(1, 5)]


		# On vérifie qu'on n'ait pas d'alternance entre oeuvres: soit glose, soit codex destructuré
		regexp = re.compile("<RMK>HSMS-\d{4}-(\d{4})")
		results = re.findall(regexp, xml_text)
		as_int = [int(item) for item in results]
		try:
			ideal_situation = [item for item in range(1, as_int[-1] + 1)]
		except IndexError:
			print(f"Aucun début de text trouvé. Revoir les médatonnées de {md['file_id_hsms']}")
			exit()

		# TODO: ajouter cette information au document XML de sortie
		check_oeuvre_destructure = not (ideal_situation == as_int)
		# Dans le cas où on a un recueil de poésie ou de lettres
		number = int(re.search(regexp_multiple_works, work_id).group(1))
		if number == 1 and contains_multiple_works is True and (check_oeuvre_destructure is True or md['type_textuel'] != "prosa" or "carta" in matieres or md["HSMS_ident"] in splits_exceptions):
			print(f"Oeuvre destructurée ou Recueil de textes poétiques ou lettre identifiée sur {work_id}")
			if number == 1:
				# Dans ces cas là on va avoir plusieurs msItems qu'on va pouvoir renseigner
				updated_msContents, updated_origin = create_multiple_msItem(md["HSMS_ident"], xml_text)
				skip_metadata_retrieval = True
			else:
				continue
			# Sur la poésie, on ne va pas diviser les oeuvres. On ne convertit donc uniquement la première oeuvre.
			conversion.convert_to_xml(xml_text, orig_text, msContents=updated_msContents, origin=updated_origin, md=md,
									  keep_only_work=False, save_as_codex=True)
		else:
			conversion.convert_to_xml(xml_text, orig_text, msContents=None, origin=None, md=md, keep_only_work=True)
			skip_metadata_retrieval = False



def main(files: str) -> None:
	"""
	Fonction principale de transformation de textes XML-TEI
	:param files: la liste de fichiers à traiter.
	:return: None
	"""

	name_parser = pipeline("ner", model="ele-sage/distilbert-base-uncased-name-splitter",
						   aggregation_strategy="simple")
	work_loop(files)
	exit(0)
	for idx, file in tqdm.tqdm(enumerate(files[:51])):
		file_as_list = utils.read_to_lines(file)
		md = metadata.retrieve_metadata(file_as_list, name_parser)
		if md is None:
			continue
		# Le texte commence à la 7e ligne
		orig_text = "\n".join(file_as_list[6:])
		# xml_text = conversion.convert(orig_text, id=md["file_id_hsms"])
		xml_text = conversion.convert(orig_text, id=md["oeuvre_id"])
		print(md["file_id_hsms"])
		conversion.convert_to_xml(xml_text, orig_text, md)


if __name__ == '__main__':
	all_files = glob.glob(f"{sys.argv[1]}/*.txt")
	if len(sys.argv) == 3:
		all_files = [item for item in all_files if sys.argv[2] in item]
		print(all_files)
	main(all_files)
