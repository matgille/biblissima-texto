import src.transform.metadata as metadata
import src.transform.utils as utils
import src.transform.txt_to_xml as conversion
import tqdm
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
	for idx, file in tqdm.tqdm(enumerate(files)):
		file_as_list = utils.read_to_lines(file)
		md = metadata.retrieve_metadata(file_as_list, name_parser)
		if md is None:
			continue
		# Le texte commence à la 7e ligne
		orig_text = "\n".join(file_as_list[7:])
		xml_text = conversion.convert(orig_text)
		conversion.convert_to_xml(xml_text, orig_text, md["file_id_hsms"])


if __name__ == '__main__':
	all_files = glob.glob(f"{sys.argv[1]}/*.txt")
	if len(sys.argv) == 3:
		all_files = [item for item in all_files if sys.argv[2] in item]
		print(all_files)
	main(all_files)