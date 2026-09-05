import lxml.etree as ET
import re





def treat_foreign(text_string):
	language_dict = {"LAT": "lat",
					 "HEB": "heb",
					 "PRV": "pro",
					 "PRT": "por",
					 "LAM": "languages_from_america",
					 "ITL": "ita",
					 "GRK": "gre",
					 "GER": "ger",
					 "GAL": "glg",
					 "FRN": "fre",
					 "ENG": "eng",
					 "CAT": "cat",
					 "BAS": "eus",
					 "ARA": "arc",
					 "ARG": "arg",
					 "ARB": "ara"}
	for orig, iso in language_dict.items():
		span_regexp = re.compile(r"\{" + orig + r"\. ([^{}]+)}")
		text_string = re.sub(span_regexp, rf"<foreign xml:lang='{iso}'>\1</foreign>", text_string)
	return text_string

def treat_folio(text_string):
	# Gérer éventuellement les breaks
	folio_regexp = re.compile(r"\[fol\. (\d+[rv]?)\]")
	text_string = re.sub(folio_regexp, r'<pb n="\1"/>', text_string)
	return text_string


def treat_columns(text_string):
	# Règle à mettre en dernier, car galère de parser
	text_string = re.sub(r"{CB1\.([^{}]+)}", r'<cb type="single_column"/>\1', text_string)
	text_string = re.sub(r"{CB2\.([^{}]+)}", r'<cb type="double_column"/>\1', text_string)
	return text_string

def treat_rubrics(text_string):
	rubrics_regexp = re.compile(r"\{RUB\.([^\{\}]+)\}")
	text_string = re.sub(rubrics_regexp, r"<hi rend='rubric'>\1</hi>", text_string)
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


def treat_scribal_additions(text_string):
	emendation_regexp = re.compile(r"\[\^([^\d][^\[\]]+)\]")
	text_string = re.sub(emendation_regexp, r'<add hand="#self">\1</add>', text_string)
	return text_string



def treat_other_scribe_additions(text_string):
	emendation_regexp = re.compile(r"\[\^(\d)#([^\[\]]+)\]")
	text_string = re.sub(emendation_regexp, r'<add hand="#\1">\2</add>', text_string)
	if re.search(emendation_regexp, text_string):
		treat_other_scribe_additions(text_string)
	return text_string

def treat_initial(text_string):
	# Il est possible que l'annotation inverse la hauteur et la lettre, vérifier dans la source
	initial_regexp_miniature = re.compile(r"{IN(\d+)\.\s{MIN\.}} ([A-Z])")
	text_string = re.sub(initial_regexp_miniature, r"<hi rend='initiale miniature' n='\1'>\2</hi>", text_string)



	initial_regexp = re.compile(r"{IN(\d+)\.} ([A-Z])")
	text_string = re.sub(initial_regexp, r"<hi rend='initiale' n='\1'>\2</hi>", text_string)
	return text_string

def treat_notes(text_string):
	text_string = re.sub(r"\{RMK: ([^{}]+)\}", r"<note>\1</note>", text_string)
	return text_string


def treat_symbols(text_string):
	# Les symboles doivent être traités a posteriori, si c'est intéressant.
	sig_regexp = re.compile(r"{SYMB[.:] ([^{}]+)}")
	text_string = re.sub(sig_regexp, r'<g ref="#?">\1</g>', text_string)
	return text_string

def treat_graphics(text_string):
	text_string = re.sub(r"{=?MIN=?\.}", "<graphic type='miniature'/>", text_string)
	text_string = re.sub(r"{=?DIAG=?\.}", "<graphic type='diagramme'/>", text_string)
	ill_regexp = re.compile(r"\{\=?ILL\=?\.?\}")
	text_string = re.sub(ill_regexp, "<graphic type='illustration'/>", text_string)
	return text_string

def treat_signature_catchwords(text_string):
	sig_regexp = re.compile(r"\{SG\. ([^{}]+)\}")
	text_string = re.sub(sig_regexp, r"<fw rend='sig'>\1</fw>", text_string)

	sig_regexp = re.compile(r"\{CW\. ([^{}]+)\}")
	text_string = re.sub(sig_regexp, r"<fw rend='catchword'>\1</fw>", text_string)

	return text_string

def treat_editorial_deletion(text_string):
	editorial_del_regexp = re.compile(r"\(([^()]+)\)")
	text_string = re.sub(editorial_del_regexp, r"<choice><sic>\1</sic><corr/></choice>", text_string)
	return text_string

def treat_illegible_char(text_string):
	text_string = re.sub(r'(?<!\s)\[\?\?\]', r'<gap reason="illegible" extent="subword"/>', text_string)
	return text_string

def treat_illegible_word(text_string):
	text_string = re.sub(r'\s\[\?\?\]', r' <gap reason="illegible" extent="word"/>', text_string)
	return text_string


def treat_illegible_words(text_string):
	text_string = re.sub(r'\s\[\?\?\?\]', r' <gap reason="illegible" extent="words"/>', text_string)
	return text_string

def treat_calderon(text_string):
	text_string = text_string.replace("¶", '<g ref="#calderon1"/>')
	text_string = text_string.replace("%2", '<g ref="#calderon2"/>')
	text_string = text_string.replace("%3", '<g ref="#calderon3"/>')
	return text_string

def treat_editorial_guesses(text_string):
	text_string = re.sub(r"\[\*([^\[\]]+)\]", r'<unclear reason="illegible">\1</unclear>', text_string)
	return text_string

def treat_gloss_addendum(text_string):
	text_string = re.sub(r"\{GL\. ([^{}]+)\}", r"<span type='gloss'>\1</span>", text_string)
	text_string = re.sub(r"\{AD\. ([^{}]+)\}", r"<span type='addendum'>\1</span>", text_string)
	return text_string

def treat_editorial_addition(text_string):
	editorial_del_regexp = re.compile(r"\[([^*^][^\[\]]*)\]")
	text_string = re.sub(editorial_del_regexp, r"<choice><corr>\1</corr><sic/></choice>", text_string)
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


def treat_editorial_substitution(text_string):
	text_string = re.sub(r'\(([^()]+)\)\[([^\[\]]+)\]', r'<choice><sic>\1</sic><corr>\2</corr></choice>', text_string)
	return text_string


def convert_running_title(text_string):
	# l'ancienne foliation est toujours indiquée de façon identique.
	text_string = re.sub(r"\{HD\. ([^{}]+)\\\ (\d+)\.?\}", r'<fw type="running_title">\1</fw><fw type="OldFoliation">\2</fw>', text_string)
	text_string = re.sub(r"\{HD\. ([^{}]+)\}", r'<fw type="running_title">\1</fw>', text_string)
	return text_string

def convert_ampersands(text):
	return text.replace("&", "&amp;")

def modify_delimiter(text):
	return text.replace("<", "⦃").replace(">", "⦄")

def convert(orig_text):
	text = modify_delimiter(orig_text)
	text = treat_folio(text)
	text = treat_foreign(text)
	text = treat_particular_abbreviations(text)
	text = treat_symbols(text)
	text = treat_gloss_addendum(text)
	text = treat_abbreviations(text)
	text = treat_rubrics(text)
	text = treat_initial(text)
	text = treat_graphics(text)
	text = treat_signature_catchwords(text)
	text = treat_other_scribe_additions(text)
	text = treat_illegible_char(text)
	text = treat_illegible_word(text)
	text = treat_illegible_words(text)
	text = treat_scribal_additions(text)
	text = treat_calderon(text)
	text = treat_editorial_substitution(text)
	text = treat_editorial_deletion(text)
	text = treat_editorial_addition(text)
	text = treat_linebreaks(text)
	text = convert_ampersands(text)
	text = treat_notes(text)
	text = convert_running_title(text)
	text = treat_editorial_guesses(text)
	text = treat_columns(text)
	text = revert_parenthesis(text)
	return text

def convert_to_xml(text, orig_text, idx):
	TEI_NS = "http://www.tei-c.org/ns/1.0"
	NSMAP = {None: TEI_NS}
	parent_div = ET.Element(f"{{{TEI_NS}}}div", nsmap=NSMAP)
	try:
		childDiv = ET.fromstring(f"<div>{text}</div>")
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

