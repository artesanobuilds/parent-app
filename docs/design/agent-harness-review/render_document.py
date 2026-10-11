"""Build the technical design PDF from README.md.

Dependencies: reportlab, pymupdf. Requires rsvg-convert on PATH.
Figures are placed as vector PDF pages, preserving selectable, sharp labels.
"""
from pathlib import Path
from html import escape
import re
import subprocess
import tempfile
import pymupdf as fitz
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    Preformatted, Flowable,
)

ROOT=Path(__file__).parent
SOURCE=(ROOT/'README.md').read_text()
OUTPUT=ROOT/'MVP-Agent-Harness-Technical-Design.pdf'
INK=colors.HexColor('#182D3A')
MUTED=colors.HexColor('#526675')
TEAL=colors.HexColor('#167A73')
BG=colors.HexColor('#EAF3F0')
PAGE_W,PAGE_H=A4
MARGIN=43
WIDTH=PAGE_W-2*MARGIN
FIGURES=[]
TMP=Path(tempfile.mkdtemp(prefix='harness-pdf-'))

styles={
 'title':ParagraphStyle('Title',fontName='Helvetica-Bold',fontSize=28,leading=32,textColor=INK,spaceAfter=12),
 'h1':ParagraphStyle('Heading1',fontName='Helvetica-Bold',fontSize=22,leading=26,textColor=INK,spaceAfter=12,keepWithNext=True),
 'h2':ParagraphStyle('Heading2',fontName='Helvetica-Bold',fontSize=11.5,leading=14,textColor=TEAL,spaceBefore=10,spaceAfter=5,keepWithNext=True),
 'body':ParagraphStyle('Body',fontName='Helvetica',fontSize=9.5,leading=13.2,textColor=INK,spaceAfter=8),
 'cell':ParagraphStyle('Cell',fontName='Helvetica',fontSize=8.6,leading=11.5,textColor=INK),
 'th':ParagraphStyle('TableHeader',fontName='Helvetica-Bold',fontSize=8.6,leading=11.5,textColor=colors.white),
 'code':ParagraphStyle('Code',fontName='Courier',fontSize=7.7,leading=10.5,textColor=INK,backColor=colors.HexColor('#F0F4F6'),borderPadding=8,spaceBefore=4,spaceAfter=11),
 'bullet':ParagraphStyle('Bullet',fontName='Helvetica',fontSize=9.5,leading=13.2,textColor=INK,leftIndent=15,firstLineIndent=-13,spaceAfter=7),
 'meta':ParagraphStyle('Meta',fontName='Helvetica',fontSize=8.5,leading=12,textColor=MUTED,spaceAfter=10),
}
refs=dict(re.findall(r'^\[([^\]]+)\]:\s*(\S+)\s*$',SOURCE,re.M))

def inline(t):
    t=escape(t)
    # Bind code spans before links so brackets in snippets stay literal.
    t=re.sub(r'`([^`]+)`',r'<font name="Courier" size="9">\1</font>',t)
    t=re.sub(r'\*\*([^*]+)\*\*',r'<b>\1</b>',t)
    t=re.sub(r'\[([^\]]+)\]\((https?[^\s)]+)\)',r'<link href="\2" color="#167A73">\1</link>',t)
    t=re.sub(r'\[([^\]]+)\]\[([^\]]+)\]',lambda m:f'<link href="{refs[m[2]]}" color="#167A73">{m[1]}</link>' if m[2] in refs else m[0],t)
    t=re.sub(r'\[([ER]\d+)\]',lambda m:f'<link href="{refs[m[1]]}" color="#167A73">[{m[1]}]</link>' if m[1] in refs else m[0],t)
    return t

class VectorFigure(Flowable):
    def __init__(self,path):
        super().__init__()
        self.path=path.with_suffix('.svg')
        data=self.path.read_text()
        w,h=map(float,re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"',data).groups())
        self.width=WIDTH
        self.height=WIDTH*h/w
        if self.height>548:
            self.width*=548/self.height
            self.height=548
        self.hAlign='CENTER'
    def draw(self):
        x,y=self.canv.absolutePosition(0,0)
        FIGURES.append((self.canv.getPageNumber()-1,x,PAGE_H-y-self.height,self.width,self.height,self.path))

class ReviewDoc(SimpleDocTemplate):
    def afterFlowable(self,f):
        if isinstance(f,Paragraph) and f.style.name in ('Title','Heading1'):
            title=f.getPlainText()
            key='section-'+str(self.page)+'-'+str(abs(hash(title)))
            self.canv.bookmarkPage(key)
            self.canv.addOutlineEntry(title,key,0,False)

def chrome(c,doc):
    c.saveState()
    c.setFillColor(TEAL); c.setFont('Helvetica-Bold',8)
    c.drawString(MARGIN,PAGE_H-26,'ARTESANO BUILDS  /  MVP ENGINEERING')
    c.setFillColor(MUTED);c.setFont('Helvetica',8)
    c.drawRightString(PAGE_W-MARGIN,PAGE_H-26,'DESIGN PROPOSAL  ·  10 OCT 2026')
    c.setStrokeColor(colors.HexColor('#DCE4E7'));c.setLineWidth(.5)
    c.line(MARGIN,34,PAGE_W-MARGIN,34)
    c.drawString(MARGIN,21,'Agent harness architecture  /  Existing contracts preserved')
    c.drawRightString(PAGE_W-MARGIN,21,str(doc.page))
    c.restoreState()

story=[]
lines=SOURCE.splitlines();i=0
while i<len(lines):
    line=lines[i].strip()
    if not line or re.match(r'^\[[^\]]+\]:',line):i+=1;continue
    if line=='<!-- pagebreak -->':story.append(PageBreak());i+=1;continue
    if line.startswith('```'):
        code=[];i+=1
        while i<len(lines) and not lines[i].startswith('```'):
            code.append(lines[i]);i+=1
        story.append(Preformatted('\n'.join(code),styles['code']));i+=1;continue
    if line.startswith('!['):
        path=re.search(r'\]\(([^)]+)\)',line)[1]
        story.extend([VectorFigure(ROOT/path),Spacer(1,13)]);i+=1;continue
    if line.startswith('|'):
        rows=[]
        while i<len(lines) and lines[i].strip().startswith('|'):
            row=[c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.match(r'^[: -]+$',c) for c in row):rows.append(row)
            i+=1
        n=len(rows[0])
        if n==3: widths=[WIDTH*.23,WIDTH*.39,WIDTH*.38]
        elif rows[0][0]=='Ref':widths=[WIDTH*.1,WIDTH*.9]
        else:widths=[WIDTH*.32,WIDTH*.68]
        cells=[[Paragraph(inline(c),styles['th' if r==0 else 'cell']) for c in row] for r,row in enumerate(rows)]
        t=Table(cells,colWidths=widths,repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,0),INK),('VALIGN',(0,0),(-1,-1),'TOP'),
            ('LEFTPADDING',(0,0),(-1,-1),9),('RIGHTPADDING',(0,0),(-1,-1),9),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.HexColor('#F1F5F6'),colors.white]),
            ('LINEBELOW',(0,0),(-1,0),.7,TEAL),
        ]));story.extend([t,Spacer(1,11)]);continue
    if line.startswith('# '):story.append(Paragraph(inline(line[2:]),styles['title']));i+=1;continue
    if line.startswith('## '):story.append(Paragraph(inline(line[3:]),styles['h1']));i+=1;continue
    if line.startswith('### '):story.append(Paragraph(inline(line[4:]),styles['h2']));i+=1;continue
    style='bullet' if re.match(r'^\d+\. ',line) else 'body'
    if line.startswith('**Architecture review'):style='meta'
    parts=[line];i+=1
    while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||!\[|```|<!--|\d+\. |\[[^\]]+\]:)',lines[i]):
        parts.append(lines[i].strip());i+=1
    story.append(Paragraph(inline(' '.join(parts)),styles[style]))

doc=ReviewDoc(str(TMP/'base.pdf'),pagesize=A4,rightMargin=MARGIN,leftMargin=MARGIN,topMargin=48,bottomMargin=45,title='MVP Agent Harness Technical Design',author='Artesano Builds',subject='Architecture review and proposed REST-compatible harness refactor')
doc.build(story,onFirstPage=chrome,onLaterPages=chrome)
pdf=fitz.open(TMP/'base.pdf')
for page,x,y,w,h,src in FIGURES:
    vector=TMP/(src.stem+'.pdf')
    subprocess.run(['rsvg-convert','-f','pdf','-o',str(vector),str(src)],check=True)
    with fitz.open(vector) as figure:
        pdf[page].show_pdf_page(fitz.Rect(x,y,x+w,y+h),figure,0)
pdf.save(OUTPUT,garbage=4,deflate=True)
print(f'{OUTPUT}: {len(pdf)} pages, {OUTPUT.stat().st_size:,} bytes')
for n,p in enumerate(pdf):
    print(f'Page {n+1}: {len(p.get_text().split())} words')
