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
				if "IN" in tag:
					value = re.search(r"\d+", tag)
					tag = "hi"
					output.append(f'<hi rend="initiale" n="{value.group(0)}">')
				else:
					output.append(f"<{tag}>")
				stack.append(tag)
			elif other_hand_insertion:
				# On enlève le '=' pour obtenir un nom XML classique
				tag = "OTHER_HAND_INSERTION"
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

	# text = revert_parenthesis(text)
	return text

def convert_cb(xml_tree):
	cb1 = xml_tree.xpath("//CB1|//CB2|//CB3|//CB4")
	mapping = {"CB1": "single", "CB2": "double", "CB3": "triple", "CB4": "quadruple"}
	for cbreak in cb1:
		childs = cbreak.xpath("child::*")
		cb = ET.Element("cb")
		cb.set("type", mapping[cbreak.tag])
		cbreak.addprevious(cb)
		# On insère après le noeud, il faut donc faire l'insertion sur la liste inversée
		[cb.addnext(child) for child in reversed(childs)]
		cbreak.getparent().remove(cbreak)
	return xml_tree

def convert_rubric(xml_tree):
	rubrics = xml_tree.xpath("//RUB")
	for rubric in rubrics:
		rubric.tag = "hi"
		rubric.set("rend", "rubric")
	return xml_tree

def convert_substitutions(xml_tree):
	subst_del = xml_tree.xpath("//SCRIBAL_DELETION[following-sibling::node()[1][self::SCRIBAL_INSERTION]]")
	for deletion in subst_del:
		subst = ET.Element("subst")
		deletion.addprevious(subst)
		deletion.tag = "del"
		addition = deletion.xpath("following-sibling::node()[1][self::SCRIBAL_INSERTION]")[0]
		addition.tag = "add"
		subst.append(addition)
		subst.append(deletion)

	return xml_tree

	for substitution in subst:
		subst_element = ET.Element("subst")
		deletion = substitution.xpath("EDITORIAL_DELETION")[0]
		insertion = substitution.xpath("EDITORIAL_INSERTION")[0]

	return xml_tree

def convert_editorial_deletions(xml_tree):
	ed_del = xml_tree.xpath("//EDITORIAL_DELETION")
	for deletion in ed_del:
		choice = ET.Element("choice")
		corr = ET.SubElement(choice, "corr")
		deletion.tag = "sic"
		deletion.addprevious(choice)
		choice.append(deletion)
	return xml_tree

def convert_elements(xml_tree):
	xml_tree = convert_cb(xml_tree=xml_tree)
	xml_tree = convert_rubric(xml_tree)
	xml_tree = convert_substitutions(xml_tree)
	# xml_tree = convert_editorial_deletions(xml_tree)
	return xml_tree

def convert_to_xml(text, orig_text, idx):
	TEI_NS = "http://www.tei-c.org/ns/1.0"
	NSMAP = {None: TEI_NS}
	parent_div = ET.Element(f"div")
	try:
		childDiv = ET.fromstring(f"<p>{text}</p>")
		parent_div.append(childDiv)
	except ET.XMLSyntaxError as e:
		print(f"Erreur de syntaxe: {e}. Check text_{idx}")
		with open(f"test_data/output/text_{idx}.txt", "w") as output_file:
			output_file.write(text)
		with open(f"test_data/output/orig_text_{idx}.txt", "w") as output_file:
			output_file.write(orig_text)
		exit()
	with open(f"test_data/xml/text_{idx}.xml", "w") as output_xml:
		output_xml.write(ET.tostring(parent_div, pretty_print=False).decode())

