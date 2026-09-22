import copy
import unidecode
import lxml.etree as ET
import re

import pandas as pd

import src.transform.utils as utils




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
	factgrid_endpoint = "https://database.factgrid.de/"


	# On commence par le titre
	titleStmt = model_as_tree.xpath("//titleStmt")[0]
	title = titleStmt.xpath("title")[0]
	title.text = f"{metadata['titre']}: version XML-TEI"
	transcription = titleStmt.xpath("respStmt")[0]
	for idx, transcriptor in enumerate(metadata["transcripteur_parse"]):
		if idx == 0:
			name = transcription.xpath("name")[0]
			name.getparent().remove(name)
		name = ET.Element("name")
		surname = ET.SubElement(name, "surname")
		surname.text = transcriptor["surname"]
		forename = ET.SubElement(name, "forename")
		forename.text = transcriptor["forename"]
		transcription.append(name)

	## L'oeuvre
	sourceDesc = model_as_tree.xpath("//sourceDesc", namespaces=tei_ns)[0]
	oeuvre = sourceDesc.xpath("bibl[@type='work']", namespaces=tei_ns)[0]
	if metadata["factgrid_work_id"]:
		factgrid_idno_work = oeuvre.xpath("idno[@type='factgrid-id']")[0]
		factgrid_idno_work.text = metadata["factgrid_work_id"]
		factgrid_idno_work.set("corresp", f"{factgrid_endpoint}entity/{metadata['factgrid_work_id']}")

	if metadata["BNFid"]:
		factgrid_idno_work = oeuvre.xpath("idno[@type='BNF-id']")[0]
		factgrid_idno_work.text = metadata["BNFid"]
		factgrid_idno_work.set("corresp", f"https://data.bnf.fr/fr/ark:/12148/cb{metadata['BNFid']}")


	if metadata["BNEid"]:
		factgrid_idno_work = oeuvre.xpath("idno[@type='BNE-id']")[0]
		factgrid_idno_work.text = metadata["BNEid"]
		factgrid_idno_work.set("corresp", f"https://datos.bne.es/obra/{metadata['BNEid']}.html")


	if metadata["VIAFid"]:
		factgrid_idno_work = oeuvre.xpath("idno[@type='VIAF-id']")[0]
		factgrid_idno_work.text = metadata["VIAFid"]
		factgrid_idno_work.set("corresp", f"https://viaf.org/en/viaf/{metadata['VIAFid']}")

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
		oeuvre.insert(1, auteur)

	# le titre
	title_oeuvre = oeuvre.xpath("title")[0]
	title_oeuvre.text = metadata['titre']

	# Date de l'oeuvre
	date_work = oeuvre.xpath("date")[0]
	date_debut = metadata['debut_production_oeuvre']
	date_fin = metadata['fin_production_oeuvre']
	parent = date_work.getparent()
	index = parent.index(date_work)
	parent.remove(date_work)
	parent.insert(index, utils.process_date(date_work, date_debut, date_fin))


	# Identifiants
	## HSMS-WORK
	hsms_work_oeuvre = oeuvre.xpath("idno[@type='HSMS-WORK']")[0]
	hsms_work_oeuvre.text = metadata['oeuvre_id']

	## BETA texid
	try:
		idno_texid_oeuvre = oeuvre.xpath("idno[@type='beta-texid']")[0]
		idno_texid_oeuvre.text = metadata['beta_texid']
	except KeyError:
		idno_texid_oeuvre.text = "TODO"

		## biblissima ID
		try:
			hsms_work = oeuvre.xpath("idno[@type='factgrid_mss_id']")[0]
			hsms_work.text = metadata['factgrid_mss_id']
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

	# On gère les informations en fonction du support de l'écriture
	format = metadata['format']
	msDesc = sourceDesc.xpath("msDesc")[0]

	# Le nom du manuscrit
	msName = msDesc.xpath("descendant::msName")[0]
	msName.text = metadata['msName']
	TEI = model_as_tree.getroot()

	# History
	origDate = sourceDesc.xpath("descendant::origDate")[0]
	date_debut = metadata['debut_production_codex']
	date_fin = metadata['fin_production_codex']
	# Ajouter la gestion de l'approximation (ca.)
	if format == "manuscrito":
		# On supprime le biblStruct destiné à la description de l'édition
		print_nodes = sourceDesc.xpath("biblStruct[@ana = '#frbr.manifestation']")[0]
		print_nodes.getparent().remove(print_nodes)
		print_comments = sourceDesc.xpath("descendant::comment()[contains(., 'Édition')]")
		[item.getparent().remove(item) for item in print_comments]

		# On corrige l'analyse du msDesc
		msDesc.set("ana", "#frbr.manifestation_singleton")

		origDate.set("corresp", f"#{metadata['oeuvre_id']}")
		parent = origDate.getparent()
		index = parent.index(origDate)
		parent.remove(origDate)
		parent.insert(index, utils.process_date(origDate, date_debut, date_fin))
	else:
		msDesc.set("ana", "#frbr.item")
		biblStruct = sourceDesc.xpath("biblStruct[@ana = '#frbr.manifestation']")[0]
		publisher = biblStruct.xpath("monogr/imprint/publisher")[0]
		publisher.text = metadata["producteur"]
		pubPlace = biblStruct.xpath("monogr/imprint/pubPlace")[0]
		pubPlace.text = metadata["lieu_production"]
		publicationDate = biblStruct.xpath("monogr/imprint/date")[0]
		parent = publicationDate.getparent()
		index = parent.index(publicationDate)
		parent.remove(publicationDate)
		parent.insert(index, utils.process_date(publicationDate, date_debut, date_fin))
		history = msDesc.xpath("descendant::history")[0]
		history.getparent().remove(history)
		# Ajouter la date ici
	# On gère les informations en fonction du support de l'écriture

	# Gestion de la traduction
	translation_bibl = sourceDesc.xpath("bibl[@type='translation']")[0]
	if metadata['traducteur_parse']:
		# Identifiants
		hsms_work_traduction = translation_bibl.xpath("idno[@type='HSMS-WORK']")[0]
		hsms_work_traduction.text = metadata['oeuvre_id']
		hsms_work_oeuvre.text =  ""
		if metadata["factgrid_work_id"]:
			factgrid_work_id_traduction = translation_bibl.xpath("idno[@type='factgrid-id']")[0]
			factgrid_work_id_traduction.text = metadata["factgrid_work_id"]
			factgrid_work_id_traduction.set("corresp", factgrid_endpoint + metadata["factgrid_work_id"])
			# On supprime l'identifiant au niveau du work.
			factgrid_idno_work.text = ""
			factgrid_idno_work.attrib.pop('corresp')

		# Date
		date_traduction = translation_bibl.xpath("date")[0]
		date_work = oeuvre.xpath("date")[0]
		date_traduction.text = date_work.text
		date_work.text = ""
		for name, value in date_work.attrib.items():
			date_traduction.set(name, value)
			date_work.attrib.pop(name)

		idno_texid_traduction = translation_bibl.xpath("idno[@type='beta-texid']")[0]
		idno_texid_traduction.text = metadata['beta_texid']
		idno_texid_oeuvre.text = ""

		hsms_work_translate = translation_bibl.xpath("idno[@type='HSMS-WORK']")[0]
		hsms_work_translate.text = metadata['oeuvre_id']
		# On annule l'injection précédente.
		hsms_work_oeuvre.text = ""
		title_translation = translation_bibl.xpath("title")[0]
		title_translation.text = metadata["titre"]
		# On annule l'injection précédente.
		title_oeuvre.text = ""
		TEI.set("type", "traduction")
		author = translation_bibl.xpath("author")[0]
		author.getparent().remove(author)
		for idx, translator in enumerate(metadata["traducteur_parse"]):
			auteur = ET.SubElement(oeuvre, "author")
			surname = ET.SubElement(auteur, "surname")
			surname.text = translator["surname"]
			forename = ET.SubElement(auteur, "forename")
			forename.text = translator["forename"]
			if translator['function'] != '':
				role = ET.SubElement(auteur, "roleName")
				role.text = translator['function']
			if idx != len(metadata["traducteur_parse"]) - 1:
				name.tail = " et "
			translation_bibl.insert(1, auteur)
	else:
		TEI.set("type", "oeuvre_originale")
		translation_bibl.getparent().remove(translation_bibl)
		translation_comments = sourceDesc.xpath("descendant::comment()[contains(., 'Traductions')]")
		[item.getparent().remove(item) for item in translation_comments]

	# Identifiants du manuscrit
	msDesc = sourceDesc.xpath("msDesc")[0]
	identifier = msDesc.xpath("msIdentifier")[0]
	if metadata['digitalisation']:
		identifier.set("facs", metadata['digitalisation'])
	lieu_conservation = metadata['bibliotheque_conservation'].split(":")[0].strip()
	try:
		bibliotheque = metadata['bibliotheque_conservation'].split(":")[1].strip()
	except IndexError:
		bibliotheque = "UNK"
	settlement = identifier.xpath("settlement")[0]
	settlement.text = lieu_conservation
	institution = identifier.xpath("repository")[0]
	institution.text = bibliotheque
	institution.set("corresp", metadata['factgrid_institution_id'])

	hsms_id = identifier.xpath("idno[@type='HSMS-ID']")[0]
	hsms_id.text = metadata['HSMS_ident']
	# BNE: adapter.
	id_bne = identifier.xpath("idno[@type='BNE']")[0]
	id_bne.getparent().remove(id_bne)
	beta_copid = identifier.xpath("idno[@type='beta-copid']")[0]
	beta_manid = identifier.xpath("idno[@type='beta-manid']")[0]
	factgrid_id = identifier.xpath("idno[@type='factgrid-id']")[0]
	if metadata["beta_manid"]:
		beta_manid.text = str(int(metadata['beta_manid']))
		beta_manid.set("corresp", metadata['lien_philobiblon'])
		beta_copid.getparent().remove(beta_copid)
		factgrid_id.set("corresp", metadata['factgrid_mss_id'])
		factgrid_id.text = metadata['factgrid_mss_id'].split("/")[-1]
	if metadata["beta_copid"]:
		try:
			beta_copid.text = str(int(metadata['beta_copid']))
		except ValueError:
			beta_copid.text = metadata['beta_copid']
		beta_copid.set("corresp", metadata['lien_philobiblon'])
		beta_manid.getparent().remove(beta_manid)
		factgrid_id.set("corresp", metadata['factgrid_mss_id'])
		factgrid_id.text = metadata['factgrid_mss_id'].split("/")[-1]
	cote = identifier.xpath("idno[@type='cote']")[0]
	cote.text = metadata["cote"]


	# Profile desc
	profileDesc = model_as_tree.xpath("descendant::profileDesc")[0]
	# La langue utilisée.
	langues = metadata["langues"]
	langUsage = profileDesc.xpath("descendant::langUsage")[0]
	child = langUsage.xpath("language")[0]
	langUsage.remove(child)
	for lang in langues:
		language = ET.SubElement(langUsage, "language")
		language.text = lang
		language.set("ident", lang)

	# Catégorie formelle; matière textuelle
	catRef = profileDesc.xpath("descendant::catRef")[0]
	# On commence par la forme
	forme = metadata['type_textuel']
	if forme == "prosa":
		forme = "#prose"
	else:
		forme = "#vers"

	matieres = [metadata[f"matiere_{str(n)}"] for n in range(1, 5)]
	# On va enlever
	matieres = " ".join([f"#{unidecode.unidecode(item)}" for item in matieres if item])
	catRef.set("target", f"{forme} {matieres}")



	# msContent
	msContent = msDesc.xpath("msContents")[0]
	msItem = msContent.xpath("msItem")
	for item in msItem:
		item.set("{http://www.w3.org/XML/1998/namespace}id", metadata['oeuvre_id'])
		locus = item.xpath("locus")[0]
		locus.text = metadata['emplacement_oeuvre']
		incipit = item.xpath("incipit")[0]
		incipit.text = metadata['incipit_unit']
		colophon = item.xpath("colophon")[0]
		colophon.text = metadata['colophon']
		explicit = item.xpath("explicit")[0]
		explicit.text = metadata['explicit_unit']
		if not pd.isna(metadata['beta_cnum']) and metadata['beta_cnum']:
			beta_cnum = item.xpath("idno[@type='beta-cnum']")[0]
			comment = beta_cnum.xpath("comment()")[0]
			beta_cnum.remove(comment)
			beta_cnum.text = str(int(metadata['beta_cnum']))
			cnum_factgrid = item.xpath("idno[@type='factgrid-cnum']")[0]
			comment = cnum_factgrid.xpath("comment()")[0]
			cnum_factgrid.remove(comment)
			cnum_factgrid.text = metadata['factgrid_cnum']
			cnum_factgrid.set("corresp", f"{factgrid_endpoint}entity/{metadata['factgrid_cnum']}")



	# On injecte le texte pré-structuré dans le body
	text = model_as_tree.xpath("//body", namespaces=tei_ns)[0]
	p = text.xpath("p", namespaces=tei_ns)[0]
	p.getparent().remove(p)
	text.append(structured_text)
	root = model_as_tree.getroot()
	root.tag = ET.QName(root).localname
	return model_as_tree

def tronquer(root, borne1, borne2):
	# positions en ordre document
	pos = {el: i for i, el in enumerate(root.iter())}
	if pos[borne1] > pos[borne2]:
		borne1, borne2 = borne2, borne1

	# éléments à préserver quoi qu'il arrive :
	proteges = set(borne1.iter())      # borne1 + toute sa descendance
	proteges |= set(borne2.iter())     # borne2 + toute sa descendance
	p = borne1.getparent()
	while p is not None:               # ancêtres de borne1
		proteges.add(p)                # (couvre aussi les ancêtres communs)
		p = p.getparent()

	for el in list(root.iter()):
		if el in proteges:
			continue
		if pos[el] < pos[borne1] or pos[el] > pos[borne2]:
			parent = el.getparent()
			if parent is not None:
				parent.remove(el)
	return root


def keep_only_given_work(tree, ident):
	body = tree.xpath("//body/div/p")[0]
	all_notes = body.xpath("descendant::RMK[contains(., 'HSMS-')]")
	if len(all_notes) == 1 or len(all_notes) == 0:
		return tree
	target_note = next((idx, note) for idx, note in enumerate(all_notes) if ident in note.text)
	print(all_notes)

	# Si on est le dernier noeud
	if target_note[0] + 1 == len(all_notes):
		rmk_subelement = ET.Element("RMK-END")
		body.append(rmk_subelement)
		replaced_body =  tronquer(body, borne1=target_note[1], borne2=rmk_subelement)
		rmk_subelement = replaced_body.xpath("descendant::RMK-END")[0]
		rmk_subelement.getparent().remove(rmk_subelement)
	else:
		replaced_body =  tronquer(body, borne1=target_note[1], borne2=all_notes[target_note[0] + 1])
	body.getparent().replace(body, replaced_body)
	return tree

def replace_msContents(tree, node_to_update):
	msContent = tree.xpath("descendant::msContents")[0]
	msContent.getparent().replace(msContent, node_to_update)
	return tree


def replace_origin(tree, node_to_update):
	try:
		origin = tree.xpath("descendant::origin")[0]
	except IndexError:
		return tree
	origin.getparent().replace(origin, node_to_update)
	return tree

def convert_to_xml(text, orig_text, msContents, origin, md, keep_only_work=False, save_as_codex=False):
	work_id = md["oeuvre_id"]
	first_div = ET.Element(f"div")
	try:
		childDiv = ET.fromstring(f"<p>{text}</p>")
		first_div.append(childDiv)
		first_div = treat_initial(first_div)
		# TODO: faire une fonction de réordonnement des lignes rubriquées

		tei_file = inject_metadata(md, first_div)
		if msContents is not None:
			tei_file = replace_msContents(tei_file, msContents)
		if origin is not None:
			tei_file = replace_origin(tei_file, origin)
		if keep_only_work is True:
			tei_file = keep_only_given_work(tei_file, work_id)
	except ET.XMLSyntaxError as e:
		print(f"Erreur de syntaxe: {e}. Check text_{work_id}")
		exit(0)
		with open(f"test_data/output/text_{work_id}.txt", "w") as output_file:
			output_file.write(text)
		with open(f"test_data/output/orig_text_{work_id}.txt", "w") as output_file:
			output_file.write(orig_text)
		exit()
	if save_as_codex is True:
		work_id = "-".join(work_id.split("-")[:-1])
	print(f"Writing test_data/xml/text_{work_id}.xml")
	with open(f"test_data/xml/text_{work_id}.xml", "w") as output_xml:
		output_xml.write(ET.tostring(tei_file, pretty_print=False).decode())

