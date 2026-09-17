import re

import src.transform.metadata as metadata
import src.transform.utils as utils
import src.transform.txt_to_xml as conversion
import tqdm
from transformers import pipeline
import glob
import sys


def work_loop(files):
	name_parser = pipeline("ner", model="ele-sage/distilbert-base-uncased-name-splitter",
						   aggregation_strategy="simple")
	df_oeuvres = utils.import_table_as_dataframe(path="databases/tabla-obras.csv", sep="\t")
	n = 0
	splits_exceptions = ["HSMS-0037"]
	for idx, work in df_oeuvres.iterrows():
		filename = work['Abreviatura HSMS']
		work_id = work["Obra ID"]
		corresponding_file = next(file for file in files if filename in file)
		file_as_list = utils.read_to_lines(corresponding_file)
		regexp_multiple_works = re.compile(r"HSMS-\d{4}-(\d{4})")
		md = metadata.retrieve_metadata(file_as_list, name_parser, work_id=work_id, disable_queries=True)
		orig_text = "\n".join(file_as_list[6:])

		# On splitte après la transformation en xml-tei, c'est beaucoup plus simple.
		xml_text = conversion.convert(orig_text, id=work_id)
		print(md["file_id_hsms"])
		print(md["oeuvre_id"])
		matieres = [md[f"matiere_{str(n)}"] for n in range(1, 5)]
		if md['type_textuel'] != "prosa" or "carta" in matieres or md["HSMS_ident"] in splits_exceptions:
			print(f"Poésie ou lettre identifiée sur {work_id}")
			number = int(re.search(regexp_multiple_works, work_id).group(1))
			if number != 1:
				continue
			# Sur la poésie, on ne va pas diviser les oeuvres. On ne convertit donc uniquement la première oeuvre.
			conversion.convert_to_xml(xml_text, orig_text, md, keep_only_work=False, save_as_codex=True)
			print("Cas 2")
		else:
			conversion.convert_to_xml(xml_text, orig_text, md, keep_only_work=True)
		n += 1
		if idx > 50:
			break
	print(n)

def main(files:str) -> None:
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