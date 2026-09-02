import src.transform.metadata as metadata
import src.transform.utils as utils
import src.transform.txt_to_xml as convert

from transformers import pipeline
import glob
import sys


def main(files:str) -> None:
	"""
	Fonction principale de transformation de textes XML-TEI
	:param files: la liste de fichiers à traiter.
	:return: None
	"""

	name_parser = pipeline("ner", model="ele-sage/distilbert-base-uncased-name-splitter",
						   aggregation_strategy="simple")
	for idx, file in enumerate(files):
		file_as_list = utils.read_to_lines(file)
		with open(f"test_data/output/orig_{idx}.txt", "w") as output_file:
			output_file.write("\n".join(file_as_list))
		md = metadata.retrieve_metadata(file_as_list, name_parser)
		if md is None:
			continue
		# Le texte commence à la 7e ligne
		xml_text = convert.convert(file_as_list[7:], idx)


if __name__ == '__main__':
	files_dir = glob.glob(f"{sys.argv[1]}/*.txt")
	main(files_dir)