#! /usr/bin/env py.test
# -*- coding: utf-8 -*-
# Copyright (c) 2007-2009 PediaPress GmbH
# See README.txt for additional licensing information.

import sys

from mwlib.advtree import buildAdvancedTree
from mwlib import parser

#from mwlib.treecleaner_new import TreeCleaner
import os
if os.environ.get('TREENEW'):
    print 'using new treecleaner'
    from mwlib.treecleaner_new import TreeCleaner
    new_treecleaner = True
else:
    from mwlib.treecleaner import TreeCleaner
    new_treecleaner = False
    

from mwlib.advtree import (Article, ArticleLink, Blockquote, BreakingReturn, CategoryLink, Cell, Center, Chapter,
                     Cite, Code, DefinitionList, Div, Emphasized, Gallery, HorizontalRule, ImageLink, InterwikiLink, Item,
                     ItemList, LangLink, Link, Math, NamedURL, NamespaceLink, Paragraph, PreFormatted,
                     Reference, ReferenceList, Row, Section, Source, SpecialLink, Span, Strong, Table, Text, Underline,
                     URL)

from mwlib.xfail import xfail

def _treesanity(r):
    "check that parents match their children"
    for c in r.allchildren():
        if c.parent:
            assert c in c.parent.children
            assert len([x for x in c.parent.children if x is c]) == 1
        for cc in c:
            assert cc.parent
            assert cc.parent is c
            

def getTreeFromMarkup(raw):
    from mwlib.dummydb import DummyDB
    from mwlib.uparser import parseString
    return parseString(title="Test", raw=raw, wikidb=DummyDB())
    
def cleanMarkup(raw):
    print "Parsing %r" % (raw,)
    
    tree  = getTreeFromMarkup(raw)

    print "before treecleaner: >>>"
    showTree(tree)
    print "<<<"
    
    print '='*20
    buildAdvancedTree(tree)
    tc = TreeCleaner(tree, save_reports=True)
    if new_treecleaner:
        tc.clean(tree)
    else:
        tc.cleanAll(skipMethods=[])
    reports = tc.getReports()
    print "after treecleaner: >>>"
    showTree(tree)
    print "<<<"
    return (tree, reports)

def cleanMarkupSingle(raw, cleanerMethod):
    tree  = getTreeFromMarkup(raw)
    buildAdvancedTree(tree)
    tc = TreeCleaner(tree, save_reports=True)
    tc.clean([cleanerMethod])
    reports = tc.getReports()
    return (tree, reports)
    

def showTree(tree):
    parser.show(sys.stdout, tree, 0)
    

def test_fixLists1():
    raw = r"""
para

* list item 1
* list item 2
** list item 2.1
* list item 3

* list 2 item 1
* list 2 item 2

para

* list 3
"""
    tree, reports = cleanMarkup(raw)
    lists = tree.getChildNodesByClass(ItemList)
    for li in lists:
        print li, li.getParents()
        assert all([p.__class__ != Paragraph for p in li.getParents()])
    _treesanity(tree)
    assert False

def test_fixLists2():
    raw = r"""
* list item 1
* list item 2
some text in the same paragraph

another paragraph
    """    
    # cleaner should do nothing
    tree, reports = cleanMarkup(raw)
    lists = tree.getChildNodesByClass(ItemList)
    li = lists[0]
    assert li.parent.__class__ == Paragraph
    txt = ''.join([x.asText() for x in li.siblings])
    assert u'some text in the same paragraph' in txt
    assert u'another' not in txt

def test_fixLists3():
    raw = r"""
* ul1
* ul2
# ol1
# ol2
"""
    tree, reports = cleanMarkup(raw)
    assert len(tree.children) == 2 # 2 itemlists as only children of article
    assert all( [ c.__class__ == ItemList for c in tree.children])
    

def test_childlessNodes():
    raw = r"""
blub
    
<source></source>

*

<div></div>

<u></u>
    """
    tree, reports = cleanMarkup(raw)
    from pprint import pprint
    pprint(reports)         
    assert len(tree.children) == 1 #assert only the 'blub' paragraph is left and the rest removed
    assert tree.children[0].__class__ == Paragraph  


def test_removeLangLinks():
    raw = r"""
bla
[[de:Blub]]
[[en:Blub]]
[[es:Blub]]
blub
"""
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    langlinks = tree.find(LangLink)
    assert not langlinks, 'expected no LangLink instances'
    
def test_removeCriticalTables():
    raw = r'''
{| class="navbox"
|-
| bla
| blub
|}

blub
'''    
    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(Table)) == 0


def test_fixTableColspans():
    raw = r'''
{|
|-
| colspan="5" | bla
|-
| bla
| blub
|}
    '''
    tree, reports = cleanMarkup(raw)
    t = tree.getChildNodesByClass(Table)[0]
    cell = t.children[0].children[0]
    assert cell.colspan == 2

def test_removeBrokenChildren():
    raw = r'''
<ref>
 preformatted text
</ref>

<ref>
<p>bla</p>
<div>
 some preformatted text in a div
</div>
blub
</ref>
'''
    
    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(PreFormatted)) == 0


def test_fixNesting2():
    raw = r'''
<div><div>
* bla
* blub
</div></div>
    '''
    tree, reports = cleanMarkup(raw)
    list_node = tree.getChildNodesByClass(ItemList)[0]
    assert not any([p.__class__ == Div for p in list_node.getParents()])

# the two tests below only make sense if paragraph nesting is forbidden - this is not the case anymore
# but maybe they are interesting in the future - therefore I did not delete them

## def test_fixNesting3():
##     raw = r'''
## <strike>
## para 1

## para 2
## </strike>
##     '''

##     tree, reports = cleanMarkup(raw)
##     paras = tree.getChildNodesByClass(Paragraph)
##     for para in paras:
##         assert not para.getChildNodesByClass(Paragraph)

# def test_fixNesting4():
#     raw = """
# <strike>

# <div>
#  indented para 1

# regular para

#  indented para 2

# </div>

# </strike>
# """

#     tree = getTreeFromMarkup(raw)    
#     tree, reports = cleanMarkup(raw)
#     paras = tree.getChildNodesByClass(Paragraph)
#     for para in paras:
#         assert not para.getChildNodesByClass(Paragraph)
        

def test_fixNesting5():
    raw = """
<strike>
<div>

<div>

<div>
para 1
</div>

para 2
</div>

<div>
para 2
</div>

</div>
</strike>
    """

    tree, reports = cleanMarkup(raw)
    paras = tree.getChildNodesByClass(Paragraph)

    for para in paras:
        assert not para.getChildNodesByClass(Paragraph) 

def test_fixNesting6():
    raw =u"""''„Drei Affen, zehn Minuten.“'' <ref>Dilbert writes a poem and presents it to Dogbert:<poem style>
''DOGBERT: I once read that given infinite time, a thousand monkeys with typewriters would eventually write the complete works of Shakespeare.''
''DILBERT: But what about my poem?''
''DOGBERT: Three monkeys, ten minutes.“''</poem></ref>

<references/>
    """

    tree, reports = cleanMarkup(raw)
    showTree(tree)
    from pprint import pprint
    pprint(reports)

    assert len(tree.getChildNodesByClass(Reference)) == 1

def test_fixNesting7():
    raw='''
<div>
<p>

<div>

;bla
:blub
;bla2
:blub

</div>

</p>
</div>
    '''
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    dl = tree.getChildNodesByClass(DefinitionList)[0]
    assert not dl.getParentNodesByClass(Paragraph)


@xfail
def test_splitBigTableCells():
    '''
    Splitting big table cells can not properly be tested here.
    Testing needs to be done in the writers, since this test is writer
    specific and the output has to be verfied
    '''
    assert False
    

@xfail
def test_fixParagraphs():
    raw = r'''  ''' #FIXME: which markup results in paragraphs which are not properly nested with preceeding sections?
    tree, reports = cleanMarkup(raw)
    assert False


def test_cleanSectionCaptions():
    raw = r'''
==<center>centered heading</center>==
bla
    '''

    tree, reports = cleanMarkup(raw)
    section_node = tree.getChildNodesByClass(Section)[0]
    assert all([p.__class__ != Center for p in section_node.children[0].getAllChildren()])

def test_cleanSectionCaptions2():
    raw = """=== ===
    bla
    """

    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(Section)) == 0

    
def numBR(tree):
    return len(tree.getChildNodesByClass(BreakingReturn))

def test_removebreakingreturnsInside():
    # remove BRs at the inside 'borders' of block nodes
    raw = '''
{|
|-
|<br/>blub<br/>
|text
|-
|<source></source><br/>text
| text
|-
|<br/><source></source><br/><br/>text
| text
|}
'''
    tree, reports = cleanMarkup(raw)
    assert numBR(tree) == 0
    assert len(tree.getChildNodesByClass(Table)) == 1
    assert not tree.getChildNodesByClass(Source)

def test_removebreakingreturnsOutside():
    # remove BRs at the outside 'borders' of block nodes
    raw = '''
<br/>

== section heading ==

<br/>

text

<br/>

<br/>

== section heading 2 ==

<br/><br/>

== section heading 3 ==
<br/>bla</br/>
'''

    tree, reports = cleanMarkup(raw)
    showTree(tree)
    assert numBR(tree) == 0

def test_removebreakingreturnsMultiple():
    # remove BRs at the outside 'borders' of block nodes
    raw = '''
paragraph

<br/>

<br/>

paragraph
'''

    tree, reports = cleanMarkup(raw) 
    assert numBR(tree) == 0

# mwlib.refine creates a whitespace only paragraph containing the first
# br tag. in the old parser this first paragraph also contained the source node.
@xfail
def test_removebreakingreturnsNoremove():
    raw = """
<br/>
<source>
int main()
</source>

<br/>
 <br/> bla <br/> blub

ordinary paragraph. inside <br/> tags should not be removed 
"""

    tree, reports = cleanMarkup(raw) 
    # the only br tags that should remain after cleaning are the ones inside the preformatted node
    assert numBR(tree) == 3

def test_preserveEmptyTextNodes():
    raw="""[[blub]] ''bla''"""
    tree, reports = cleanMarkup(raw) 
    p = [x for x in tree.find(Text) if x.caption==u' ']
    assert len(p)==1, 'expected one space node'

def test_gallery():
    raw ="""<gallery>
Image:There_Screenshot02.jpg|Activities include hoverboarding, with the ability to perform stunts such as dropping down from space
Image:Scenery.jpg|A wide pan over a seaside thatched-roof village
|Members can join and create interest groups
Image:Landmark02.jpg|There contains many landmarks, including a replica of New Orleans
Image:Emotes01.jpg|Avatars can display over 100 emotes
<!-- Deleted image removed: Image:Popoutemotes01.jpg|Avatars can display a wide variety of pop-out emotes -->
Image:Zona.jpg|Zona Island, a place where new members first log in.
Image:Hoverboat01.jpg|A member made vehicle. As an avatar users can paint and build a variety of items.
Image:|Zona Island, a place where new members first log in
<!-- Deleted image removed: Image:OldWaterinHole.jpg|The Old Waterin' Hole: a place where users can sit and chat while in a social club/bar-like environment. -->
</gallery>"""

    tree, reports = cleanMarkup(raw) 
    gallery = tree.find(Gallery)[0]
    assert len(gallery.children) == 6

def test_removeTextlessStyles():

    raw ="'''bold text'''"
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    assert tree.find(Strong)

    raw ="text <em><br/></em> text"
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    assert tree.find(BreakingReturn) and not tree.find(Emphasized)
    

def test_splitTableLists1():
    raw = '''
{|
|-
|
* item 1
* item 2
* item 3
* item 4
* item 5
* item 6

|
* item 7
* item 8
|}
    '''
    tree, reports = cleanMarkup(raw)
    numrows = len(tree.getChildNodesByClass(Row))
    assert numrows == 6, 'ItemList should have been splitted to 6 rows, numrows was: %d' % numrows


def test_splitTableLists2():
    raw = '''
{|
|-
|
* item 1
** item 1.1
** item 1.2
** item 1.3
** item 1.4
** item 1.5
** item 1.6
* item 2
* item 3
* item 4
* item 5
* item 6

|
* item 7
* item 8
|}
    '''
    tree, reports = cleanMarkup(raw)
    numrows = len(tree.getChildNodesByClass(Row))
    assert numrows == 6, 'ItemList should have been splitted to 6 rows, numrows was: %d' % numrows

def test_removeEmptySection():
    raw = '''
== section 1 ==

== section 2 ==

'''
    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(Section)) == 0, 'section not removed'

def test_noRemoveEmptySection():
    raw = '''
== section 1 ==
[[Image:bla.png]]

== section 2 ==

[[Image:bla.png]]

== section 3 ==

<gallery>
Image:bla.png
</gallery>

== section 4 ==
<div>
[[Image:bla.png]]
</div>
'''

    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(Section)) == 4, 'section falsly removed'

def test_invisibleLinks():
    raw = '''
== invisibleLinks ==
Category links which should be invisible:

[[Category:Polnische Geschichte|some deceiving text]]
[[Category:1848er Revolution]]

and language links:


[[be:Гісторыя Польшчы]]
[[bg:История на Полша]]
[[ca:Història de Polònia]]
'''.decode('utf-8')

    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(LangLink)) == 0, 'removing LangLink failed'
    assert len(tree.getChildNodesByClass(CategoryLink)) == 0, 'removing CategoryLink failed'
    

def test_noPrint():
    raw = '''
== noPrint == 
hi

<span class="noprint">text which is not printed</span>

ho

<div class="noprint">text which is not printed<ref name="bla">some reference which should be kept</ref></div>

blub

<ref class="noprint" name="tricky">Hey, dont display but dont remove</ref>
    '''

    tree, reports = cleanMarkup(raw)
    assert len(tree.getChildNodesByClass(Span)) == 0, 'removing noPrint nodes (span) failed'
    assert len(tree.getChildNodesByClass(Div)) == 0, 'removing noPrint nodes (div) failed'

    refs = tree.getChildNodesByClass(Reference)
    assert len(refs) == 2
    
    assert refs[0].no_display == True, 'this ref should be displayed'
    assert refs[1].no_display == True, 'this ref should be hidden'

def test_listOnlyParagraph():
    raw = '''
bla

* ho, this is a list
* and more

blub
    '''

    tree, reports = cleanMarkup(raw)

    li = tree.getChildNodesByClass(ItemList)[0]
    assert li.parent.__class__ != Paragraph

def test_markInfoboxes(): # FIXME add test
    raw = '''
{| class="infobox"
|-
| bla || blub
|-
| bla || blub
|}

{| class="noInfoboxAtAll"
|-
| bla || blub
|-
| bla || blub
|}

'''
    tree, reports = cleanMarkup(raw)
    tables = tree.getChildNodesByClass(Table)
    assert tables[0].isInfobox == True, 'table not marked as infobox'    
    assert getattr(tables[1], 'isInfobox', False) == False, 'table falsely marked as infobox'
    

def testInvalidFiletypes():
    raw = '''
[[File:bla.ogg]]

[[File:bla.jpg]]
    '''

    tree, reports = cleanMarkup(raw)

    images = tree.getChildNodesByClass(ImageLink)
    assert len(images) == 1
    assert images[0].target.endswith('.jpg')


def test_buildDefinitionLists():
    raw = '''
;dt1
:dd1
;dt2
:dd2
'''
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    dl = tree.getChildNodesByClass(DefinitionList)[0]
    assert dl and len(dl.children)==4


def test_buildDefinitionLists2():
    raw = '''
<ul>
<li>
;dt1
:dd1
;dt2
:dd2
</li>
<li>bla</li>
</ul>
'''
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    dl = tree.getChildNodesByClass(DefinitionList)
    assert not dl

def test_buildDefinitionLists3():
    raw = '''
<div>
hi

;dt1
:dd1
;dt2
:dd2

bla
</div>
'''
    tree, reports = cleanMarkup(raw)
    showTree(tree)
    dl = tree.getChildNodesByClass(DefinitionList)[0]
    assert not dl.getParentNodesByClass(Paragraph), 'DefinitionList should have been pulled out of Paragraph' 
    assert len(tree.getChildNodesByClass(Paragraph)) == 2, 'Paragraphs falsely thrown away'


def test_removeDuplicateLinksInReferences():
    raw = '''
<ref name="SM"><cite id="JMH"><span class="citation "
id="CITEREFJ.C3.B6rg-Michael_Hormann2008">Jörg-Michael Hormann&#32;(2008-05-17)&#32;(in German)&#32;(PDF),&#32;[http://zeppelin-bis-airbus.de/daten/presse/index.php?dir=Aktuelles/Aktuelles%20f%FCr%20die%20Presse%20und%20von%20der%20Presse/Archiv/&file=Starnberger%20Merkur%2017.Mai%202008%20Lokales.pdf ''<nowiki />Anfang vom Ende des ersten "Jumbo"<nowiki />''],&#32;Starnberger Merkur,&#32;pp.&nbsp;9<span class="printonly">,&#32;http://zeppelin-bis-airbus.de/daten/presse/index.php?dir=Aktuelles/Aktuelles%20f%FCr%20die%20Presse%20und%20von%20der%20Presse/Archiv/&file=Starnberger%20Merkur%2017.Mai%202008%20Lokales.pdf</span><span class="reference-accessdate">,&#32;retrieved 2009-05-03</span></span><span
    class="Z3988"
    title="ctx_ver=Z39.88-2004&rft_val_fmt=info%3Aofi%2Ffmt%3Akev%3Amtx%3Abook&rft.genre=book&rft.btitle=Anfang+vom+Ende+des+ersten+%22Jumbo%22&rft.aulast=J%C3%B6rg-Michael+Hormann&rft.au=J%C3%B6rg-Michael+Hormann&rft.date=2008-05-17&rft.pages=pp.%26nbsp%3B9&rft.pub=Starnberger+Merkur&rft_id=http%3A%2F%2Fzeppelin-bis-airbus.de%2Fdaten%2Fpresse%2Findex.php%3Fdir%3DAktuelles%2FAktuelles%2520f%25FCr%2520die%2520Presse%2520und%2520von%2520der%2520Presse%2FArchiv%2F%26file%3DStarnberger%2520Merkur%252017.Mai%25202008%2520Lokales.pdf&rfr_id=info:sid/en.wikipedia.org:Special:ExpandTemplates"><span style="display: none;">&nbsp;</span></span></cite></ref> 
<references/>
'''.decode('utf-8')

    tree, reports = cleanMarkup(raw)
    showTree(tree)
    assert not tree.getChildNodesByClass(URL), 'URL not removed'

def test_filterChildren():
    raw = '''
<gallery>
<p> paragraph inside gallery</p>
</gallery>


<gallery>
Image:dummy.png|image caption
Image:dummy.jpg|blah
<div>remove me!</div>
</gallery>

<ul>

<li>blah</li>

<p>i do not belong here</p>

<li>blub</li>

</ul>
    '''

    tree, reports = cleanMarkup(raw)
    showTree(tree)
    galleries = tree.getChildNodesByClass(Gallery)
    assert len(galleries) == 1 \
           and len(galleries[0].children) == 2 \
           and not galleries[0].getChildNodesByClass(Div) \
           and not galleries[0].getChildNodesByClass(Paragraph), 'gallery not stripped of junk'


    itemlists = tree.getChildNodesByClass(ItemList)
    assert len(itemlists) == 1 \
           and len(itemlists[0].children) == 2 \
           and not itemlists[0].getChildNodesByClass(Paragraph), 'itemlist not stripped of junk'


def test_removeLeadingParas():
    raw= '''
<ul>
<li><p>leading para</p><p>another para</p></li>
<li>hey</li>
</ul>
    '''

    tree, reports = cleanMarkup(raw)
    showTree(tree)
    ul = tree.getChildNodesByClass(ItemList)
    assert len(ul[0].children) == 2 \
           and ul[0].children[0].children[0].__class__ == Text, 'leading para in list not stripped'


def test_fixReferenceNodes():
    raw = '''
<ref>unnamed reference - unchanged by treecleaner</ref>

<ref name="test1">bla, bla</ref>

<ref name="test1"/>

<ref name="test2"/>

<ref name="test2">blub, blub</ref>

    '''

    tree, reports = cleanMarkup(raw)
    refs = tree.getChildNodesByClass(Reference)
    for i in [0,1,3]:
        assert refs[i].children
    for i in [2,4]:
        assert not refs[i].children
    assert refs[1].vlist['name'] == refs[2].vlist['name']
    assert refs[3].vlist['name'] == refs[4].vlist['name']
