import src.transform.metadata as metadata
import src.transform.utils as utils
import glob
import sys


def main(files:str) -> None:
	"""
	Fonction principale de transformation de textes XML-TEI
	:param files: la liste de fichiers à traiter.
	:return: None
	"""
	for file in files:
		metadata.retrieve_metadata(file)


if __name__ == '__main__':
	files_dir = glob.glob(f"{sys.argv[1]}/*.txt")
	main(files_dir)