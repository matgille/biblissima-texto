import copy

import lxml.etree as ET
import re





def treat_folio(text_string):
	# Gérer éventuellement les breaks
	folio_regexp = re.compile(r"\[fol\. (\d+[rv]?)\]")
	text_string = re.sub(folio_regexp, r'<pb n="\1"/>', text_string)
	return text_string


def treat_particular_abbreviations(test_string):
	text_string = re.sub(r"⦃⦃([^⦃⦄]+)⦃([^⦃⦄]+)⦄⦄⦄", r'<hi rend="superscript">\1<ex>\2</ex></hi>', test_string)
	return text_string

def treat_abbreviations(text_string):
	# Je ne sais pas quoi faire avec les caractères en superscript.
	superscript_regexp = re.compile(r"⦃⦃((?:(?!⦄⦄)[\s\S])+)⦄⦄")
	text_string = re.sub(superscript_regexp, r'<hi rend="superscript">\1</hi>', text_string)
	text_string = re.sub(r"⦃([^⦃/=⦄]+)⦄", r'<ex>\1</ex>', text_string)
	return text_string






def treat_illegible_char(text_string):
	text_string = re.sub(r'(?<!\s)\[\?\?\]', r'<gap reason="illegible" extent="subword"/>', text_string)
	return text_string

def treat_illegible_word(text_string):
	text_string = re.sub(r'\s\[\?\?\]', r' <gap reason="illegible" extent="word"/>', text_string)
	return text_string


def treat_complex_illegibility(text_string, debug=False):
	pattern = re.compile(r"\[(\?{2,3}\s?){2,}\]")
	search = re.finditer(pattern, text_string)
	if search:
		# On va travailler en inversé, car on modifie la chaîne de caractères,
		# et on modifie donc les index
		# ON aurait aussi pu fonctionner par cas, sans règles, mais moins propre
		all_replaces = []
		for item in reversed(list(search)):
			replaced = ""
			match = item.group(0)
			orig_match = copy.copy(match)
			match = re.sub(r"[\[\]]", "", match)
			splits = match.split()
			for idx, split in enumerate(splits):
				if split == "??":
					if idx == 0:
						replaced += '<gap reason="illegible" extent="subword"/> '
					elif idx == len(splits) - 1:
						replaced += ' <gap reason="illegible" extent="subword"/>'
				elif split == "???":
					if idx == 0:
						replaced += '<gap reason="illegible" extent="words"/> '
					elif idx == len(splits) - 1:
						replaced += ' <gap reason="illegible" extent="words"/> '
					else:
						replaced += ' <gap reason="illegible" extent="words"/> '
			# On met le tout dans un set et on fait les remplacements
			# sur le set.
			all_replaces.append((orig_match, replaced))
		for orig, reg in list(set(all_replaces)):
			text_string = text_string.replace(orig, reg)
			text_string = re.sub(r"\s{2}", " ", text_string)
	return text_string

def treat_illegible_words(text_string, debug=False):
	orig = copy.copy(text_string)
	text_string = re.sub(r'(\s?)\[\?\?\?\]', r'\1<gap reason="illegible" extent="words"/>', text_string)
	if debug:
		print(f"Orig: {orig}")
		print(f"Result: {text_string}")
	return text_string

def treat_combining_characters(text_string):
	text_string = text_string.replace("n(~)", "[n](ñ)")
	text_string = text_string.replace("n[~]", "[ñ](n)")
	return text_string

def treat_calderon(text_string):
	text_string = text_string.replace("¶", '<g ref="#calderon1"/>')
	text_string = text_string.replace("%2", '<g ref="#calderon2"/>')
	text_string = text_string.replace("%3", '<g ref="#calderon3"/>')
	return text_string


def treat_linebreaks(text_string):
	hyphen_regexp = re.compile(r"\-\n")
	text_string = re.sub(hyphen_regexp, '<lb break="no"/>', text_string)
	no_hyphen_regexp = re.compile(r"\n")
	text_string = re.sub(no_hyphen_regexp, '\n<lb break="yes"/>', text_string)
	return text_string

def revert_parenthesis(text_string):
	text_string = text_string.replace("≺", "(").replace("≻", ")")
	return text_string


def convert_ampersands(text):
	return text.replace("&", "&amp;")

def modify_delimiter(text):
	return text.replace("<", "⦃").replace(">", "⦄")


def iterxml(text, id=""):
	output = []
	stack = []
	pos = 0
	# TODO: Vérifier que les ajouts scribaux du type [^7] fonctionnent
	for match in re.finditer(r'(\(\^\d#)|(\[\^\d#)|(\[\^)|(\[\*)|(\(\^)|(\[)|(\()|\{([=]?[A-Za-z0-9_]+[=]?)[:.]?\s?|[}\])]', text):
		# Texte avant le token
		content = text[pos:match.start()]
		if content:
			# print(f"Found opening tag: {content}")
			output.append(content)

		token = match.group(0)

		if token in ['}', ']', ')']:
			if not stack:
				raise ValueError(f"Fermeture '}}' sans balise ouverte. Text {id} État de fin du texte: \n{' '.join(output[-100:])}")

			tag = stack.pop()

			output.append(f"</{tag}>")

		else:
			scribal_other_hand_deletion = match.group(1)
			other_hand_insertion = match.group(2)
			scribal_insertion = match.group(3)
			editorial_guess = match.group(4)
			scribal_deletion = match.group(5)
			editorial_insertion = match.group(6)
			editorial_deletion = match.group(7)
			editorial_tag = match.group(8)
			if editorial_tag:
				raw_tag = editorial_tag
				# On enlève le '=' pour obtenir un nom XML classique
				tag = raw_tag.replace('=', '_equal_')
				if re.search(r"^IN", tag):
					value = re.search(r"\d+", tag)
					tag = "hi"
					output.append(f'<hi rend="initiale" n="{value.group(0)}">')
				else:
					output.append(f"<{tag}>")
				stack.append(tag)
			elif other_hand_insertion:
				# On enlève le '=' pour obtenir un nom XML classique
				tag = "SCRIBAL_INSERTION_OTHER_HAND"
				output.append(f"<{tag}>")
				stack.append(tag)
			elif editorial_guess:
				# On enlève le '=' pour obtenir un nom XML classique
				tag = "EDITORIAL_GUESS"
				output.append(f"<{tag}>")
				stack.append(tag)

			elif scribal_deletion:
				# On enlève le '=' pour obtenir un nom XML classique
				tag = "SCRIBAL_DELETION"
				output.append(f"<{tag}>")
				stack.append(tag)
			elif scribal_other_hand_deletion:
				# On enlève le '=' pour obtenir un nom XML classique
				tag = "SCRIBAL_DELETION_OTHER_HAND"
				output.append(f"<{tag}>")
				stack.append(tag)
			elif scribal_insertion:
				tag = "SCRIBAL_INSERTION"

				output.append(f"<{tag}>")
				stack.append(tag)
			elif editorial_deletion:
				tag = "EDITORIAL_DELETION"
				output.append(f"<{tag}>")
				stack.append(tag)
			elif editorial_insertion:
				tag = "EDITORIAL_INSERTION"

				output.append(f"<{tag}>")
				stack.append(tag)

		pos = match.end()

	# Texte restant
	if pos < len(text):
		output.append(text[pos:])

	if stack:
		raise ValueError(f"Balises non fermées : {stack}. "
						 f"\n Text {id} État de fin du texte: \n{' '.join(output[-20:])}")

	return ''.join(output)

def identify_shifted_word_before_pb(text_string):
	"""
	Permet d'identifier les mots coupés qui sont reconstruits en fin de page (la fin du mot est en page suivante)
	:param text_string:
	:return:
	"""
	regexp = re.compile(r'-(\S+)</CB(\d+)>')
	text_string = re.sub(regexp, r'-<SHIFTED/>\1</CB\2>', text_string)
	return text_string

def convert(orig_text, id="", debug: bool=False):
	text = modify_delimiter(orig_text)
	text = treat_abbreviations(text)
	text = treat_calderon(text)
	text = treat_combining_characters(text)
	text = treat_folio(text)
	text = treat_illegible_char(text)
	text = treat_illegible_word(text)
	text = treat_complex_illegibility(text)
	text = treat_illegible_words(text, debug=debug)
	text = treat_particular_abbreviations(text)
	text = treat_linebreaks(text)
	text = convert_ampersands(text)
	text = iterxml(text, id)
	text = identify_shifted_word_before_pb(text)
	text = revert_parenthesis(text)


	# text = revert_parenthesis(text)
	return text

def convert_rubric(xml_tree):
	rubrics = xml_tree.xpath("//RUB")
	for rubric in rubrics:
		rubric.tag = "hi"
		rubric.set("rend", "rubric")
	return xml_tree

def treat_initial(xml_tree):
	all_initials = xml_tree.xpath("//hi[@rend='initiale']")
	for initiale in all_initials:
		initiale.tail = re.sub("^\s", "", initiale.tail)
		initiale.text = initiale.tail[:1]
		initiale.tail = initiale.tail[1:]
	return xml_tree

def inject_metadata(metadata, structured_text):
	tei_ns = {"tei": "http://www.tei-c.org/ns/1.0"}
	model_as_tree = ET.parse("models/empty_model.xml")


	# On commence par le titre
	titleStmt = model_as_tree.xpath("//titleStmt", namespaces=tei_ns)[0]
	title = titleStmt.xpath("title", namespaces=tei_ns)[0]
	title.text = f"{metadata['titre']}: version XML-TEI"
	transcription = titleStmt.xpath("respStmt", namespaces=tei_ns)[0]
	for idx, transcriptor in enumerate(metadata["transcripteur_parse"]):
		if idx == 0:
			name = transcription.xpath("name", namespaces=tei_ns)[0]
			name.getparent().remove(name)
		name = ET.Element("name")
		surname = ET.SubElement(name, "surname")
		surname.text = transcriptor["surname"]
		forename = ET.SubElement(name, "forename")
		forename.text = transcriptor["forename"]
		transcription.append(name)
		if idx != len(metadata["transcripteur_parse"]) - 1:
			name.tail = " et "

	## L'oeuvre
	sourceDesc = model_as_tree.xpath("//sourceDesc", namespaces=tei_ns)[0]
	oeuvres = sourceDesc.xpath("listBibl[@type='oeuvres']", namespaces=tei_ns)[0]
	oeuvre = oeuvres.xpath("bibl", namespaces=tei_ns)[0]

	## Auteur
	auteur = oeuvre.xpath("author", namespaces=tei_ns)[0]
	auteur.getparent().remove(auteur)
	for idx, author in enumerate(metadata["auteur_parse"]):
		auteur = ET.SubElement(oeuvre, "author")
		surname = ET.SubElement(auteur, "surname")
		surname.text = author["surname"]
		forename = ET.SubElement(auteur, "forename")
		forename.text = author["forename"]
		if author['function'] != '':
			role = ET.SubElement(auteur, "roleName")
			role.text = author['function']
		if idx != len(metadata["transcripteur_parse"]) - 1:
			name.tail = " et "
		oeuvre.insert(1, auteur)

	# le titre
	title = oeuvre.xpath("title")[0]
	title.text = metadata['titre']

	# Date de l'oeuvre
	date = oeuvre.xpath("date")[0]
	date_debut = metadata['debut_production_oeuvre']
	date_fin = metadata['fin_production_oeuvre']
	if date_debut == date_fin and "a quo" not in date_debut:
		date.text = date_debut
		date.set("when", date_debut)
	elif "a quo" in date_debut:
		date.set("atLeast", date_debut.replace("a quo", "").strip())
		date.text = date_debut
		if "ad quem" in date_fin:
			date.set("atMost", date_fin.replace("ad quem", "").strip())
			date.text = date.text + f" {date_fin}"
	elif "ad quem" in date_fin:
		date.set("atMost", date_fin.replace("ad quem", "").strip())
		date.text = date_fin
		if "a quo" in date_debut:
			date.set("atLeast", date_fin.replace("ad quem", "").strip())
			date.text =  f"{date_debut} " + date.text
	else:
		date.set("atMost", date_fin)
		date.set("atLeast", date_debut)

	# Identifiants
	## HSMS-WORK
	hsms_work = oeuvre.xpath("idno[@type='HSMS-WORK']")[0]
	hsms_work.text = metadata['oeuvre_id']

	## BETA texid
	try:
		hsms_work = oeuvre.xpath("idno[@type='philobiblon-texid']")[0]
		hsms_work.text = metadata['beta_texid']
	except KeyError:
		hsms_work.text = "TODO"

		## biblissima ID
		try:
			hsms_work = oeuvre.xpath("idno[@type='biblissima']")[0]
			hsms_work.text = metadata['biblissima']
		except KeyError:
			hsms_work.text = "TODO"

	# XML id original transcription
	bibl_source = sourceDesc.xpath("bibl[@type='source-transcription']")[0]
	bibl_source.set("{http://www.w3.org/XML/1998/namespace}id", metadata["file_id_hsms"])
	title = bibl_source.xpath("title")[0]
	title.text = f"TEXT.{metadata['file_id_hsms']}.txt"
	ptr = bibl_source.xpath("note/ptr")[0]
	target = ptr.xpath("@target")[0]
	ptr.set("target", target.replace("TEXT.X.txt", title.text))
	ptr.tail = f", {metadata['version_OSTA']}."
	if metadata["notes_codex_editeur"]:
		quote = ET.Element("quote")
		ptr.tail = ptr.tail + " Notes (codex): "
		quote.text = f"{metadata['notes_codex_editeur']}."
		ptr.addnext(quote)
	if metadata["notes_oeuvre_editeur"]:
		work_quote = ET.Element("quote")
		work_quote.text = f"{metadata['notes_oeuvre_editeur']}."
		if metadata["notes_codex_editeur"]:
			quote = bibl_source.xpath("note/quote")[0]
			quote.tail = " Notes (oeuvre): "
			quote.addnext(work_quote)
		else:
			ptr.tail = ptr.tail + f"{metadata['notes_oeuvre_editeur']}."
			ptr.addnext(work_quote)

	# Identifiants du manuscrit
	msDesc = sourceDesc.xpath("msDesc")[0]
	identifier = msDesc.xpath("msIdentifier")[0]
	if metadata['digitalisation']:
		identifier.set("facs", metadata['digitalisation'])



	# On injecte le texte pré-structuré dans le body
	text = model_as_tree.xpath("//body", namespaces=tei_ns)[0]
	p = text.xpath("p", namespaces=tei_ns)[0]
	p.getparent().remove(p)
	text.append(structured_text)
	root = model_as_tree.getroot()
	root.tag = ET.QName(root).localname
	print(metadata)
	return model_as_tree





def convert_to_xml(text, orig_text, md):
	idx = md["file_id_hsms"]
	TEI_NS = "http://www.tei-c.org/ns/1.0"
	NSMAP = {None: TEI_NS}
	first_div = ET.Element(f"div")
	try:
		childDiv = ET.fromstring(f"<p>{text}</p>")
		first_div.append(childDiv)
		first_div = treat_initial(first_div)
		tei_file = inject_metadata(md, first_div)
	except ET.XMLSyntaxError as e:
		print(f"Erreur de syntaxe: {e}. Check text_{idx}")
		with open(f"test_data/output/text_{idx}.txt", "w") as output_file:
			output_file.write(text)
		with open(f"test_data/output/orig_text_{idx}.txt", "w") as output_file:
			output_file.write(orig_text)
		exit()
	with open(f"test_data/xml/text_{idx}.xml", "w") as output_xml:
		output_xml.write(ET.tostring(tei_file, pretty_print=False).decode())

