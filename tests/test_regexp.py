import re
import src.transform.txt_to_xml as transform
import lxml.etree as ET

def test_abbreviations():
	assert transform.convert("<<p<er>o>>") == '<hi rend="superscript">p<ex>er</ex>o</hi>'
	assert transform.convert("ferr<<a>>ndo") == 'ferr<hi rend="superscript">a</hi>ndo'
	assert transform.treat_particular_abbreviations(transform.modify_delimiter("v<<q<ue>>>")) == 'v<hi rend="superscript">q<ex>ue</ex></hi>'
	assert transform.convert("v<<q<ue>>>") == 'v<hi rend="superscript">q<ex>ue</ex></hi>'

def test_folio():
	assert transform.convert("[fol. 1v]") == '<pb n="1v"/>'

def test_scribal_additions():
	example = """[^2#pu<e>s [^2#e<n>] enero y hebrero
no<n> haze nj<n>g<<u>>nd frio]"""
	target = """<dummy><add
            hand="#2">pu<ex>e</ex>s <add hand="#2">e<ex>n</ex></add> enero
            y hebrero <lb break="yes"/>no<ex>n</ex> haze nj<ex>n</ex>g<hi
                rend="superscript">u</hi>nd frio</add></dummy>"""
	parser = ET.XMLParser(remove_blank_text=True)
	dummy_produced = ET.fromstring(f"<dummy>{transform.convert(example)}</dummy>", parser=parser)
	dummy_gt = ET.fromstring(target, parser=parser)
	expected = ET.tostring(dummy_produced, pretty_print=True).decode()
	produced = ET.tostring(dummy_gt, pretty_print=True).decode()
	expected_stripped = re.sub(r"\s+", " ", expected)
	produced_stripped = re.sub(r"\s+", " ", produced)
	assert expected_stripped == produced_stripped, \
		(f"\nOrig:\n{ET.tostring(dummy_gt, pretty_print=True).decode()}\n"
		 f"Produit:\n{ET.tostring(dummy_produced, pretty_print=True).decode()}\n")


def test_editorial_additions():
	assert transform.convert("de[ ]ma") == "de<choice><corr> </corr><sic/></choice>ma"
	assert transform.convert("delos dichos nauios: entre lo[s] q") == 'delos dichos nauios: entre lo<choice><corr>s</corr><sic/></choice> q'

def test_correction():
	assert transform.convert("azey(r)[t]e, vinagre miel,"), 'azey<choice><sic>r</sic><corr>t</corr>e, vinagre miel,'

def test_unclear():
	assert transform.convert("Mute[*e]çuma con dadiuas los auia aduzido a su ami-\n") == 'Mute<unclear reason="illegible">e</unclear>çuma con dadiuas los auia aduzido a su ami<lb break="no"/>'

def test_mixed_text():
	example = """porque el Nicolao muy largamente las pone.\n[^2#[??]]"""
	target = """<dummy>porque el Nicolao muy largamente las pone. <lb break="yes"/><add hand="#2"><gap reason="illegible"
                extent="subword"/></add></dummy>"""
	parser = ET.XMLParser(remove_blank_text=True)
	dummy_produced = ET.fromstring(f"<dummy>{transform.convert(example)}</dummy>", parser=parser)
	dummy_gt = ET.fromstring(target, parser=parser)
	expected = ET.tostring(dummy_produced, pretty_print=True).decode()
	produced = ET.tostring(dummy_gt, pretty_print=True).decode()
	expected_stripped = re.sub(r"\s+", " ", expected)
	produced_stripped = re.sub(r"\s+", " ", produced)
	assert expected_stripped == produced_stripped, \
										(f"\nOrig:\n{ET.tostring(dummy_gt, pretty_print=True).decode()}\n"
										f"Produit:\n{ET.tostring(dummy_produced, pretty_print=True).decode()}\n")



def test_cb():
	text = """{CB1.
{RUB. Muy alto muy poderoso y excelentissimo principe
muy catholico & inuictissimo emperador rey y señor.}
{IN8.} ENla relacio<n> que embie a vuestra majestad
con Juan de ribera delas cosas que enestas partes me auian sucedi-
do despues dela segunda que dellas a vuestra alteza embie / dixe co-
mo por apaziguar y reduzir al real seruicio de vuestra majestad las}"""
	parser = ET.XMLParser(remove_blank_text=True)
	dummy_produced = ET.fromstring(f"<dummy>{transform.convert(text)}</dummy>", parser=parser)
	dummy_gt = ET.fromstring(f'''<dummy><cb type="single_column"/>
        <lb break="yes"/><hi rend="rubric"> Muy alto muy poderoso y
            excelentissimo principe <lb break="yes"/>muy catholico &amp;
            inuictissimo emperador rey y señor.</hi>
        <lb break="yes"/><hi rend="initiale" n="8">E</hi>Nla relacio<ex>n</ex>
        que embie a vuestra majestad <lb break="yes"/>con Juan de ribera delas
        cosas que enestas partes me auian sucedi<lb break="no"/>do despues dela
        segunda que dellas a vuestra alteza embie / dixe co<lb break="no"/>mo
        por apaziguar y reduzir al real seruicio de vuestra majestad las</dummy>''', parser=parser)
	expected = ET.tostring(dummy_produced, pretty_print=True).decode()
	produced = ET.tostring(dummy_gt, pretty_print=True).decode()
	expected_stripped = re.sub(r"\s+", " ", expected)
	produced_stripped = re.sub(r"\s+", " ", produced)
	assert expected_stripped == produced_stripped, \
										(f"\nOrig:\n{ET.tostring(dummy_gt, pretty_print=True).decode()}\n"
										f"Produit:\n{ET.tostring(dummy_produced, pretty_print=True).decode()}\n")
