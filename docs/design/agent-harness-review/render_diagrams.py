"""Render the review's editable SVG architecture figures. No external packages."""
from pathlib import Path
from html import escape

OUT = Path(__file__).parent / 'assets'
OUT.mkdir(exist_ok=True)
INK, MUTED, TEAL, BLUE, GOLD = '#182D3A', '#526675', '#167A73', '#3565A0', '#A26C24'

def text(x, y, value, size=22, color=INK, weight=400):
    return f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}">{escape(value)}</text>'

def rect(x,y,w,h,fill='#FFFFFF',stroke='#D7E1E5',radius=18):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{radius}" fill="{fill}" stroke="{stroke}"/>'

def box(x,y,w,h,title,lines,accent=TEAL,fill='#FFFFFF'):
    s=rect(x,y,w,h,fill)+f'<rect x="{x}" y="{y+20}" width="5" height="{h-40}" rx="2" fill="{accent}"/>'
    s+=text(x+22,y+36,title,24,INK,650)
    for i,line in enumerate(lines): s+=text(x+22,y+68+i*27,line,20,MUTED)
    return s

def arrow(x1,y1,x2,y2,color=TEAL,both=False):
    return f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{color}" stroke-width="2.5" marker-end="url(#arrow)"'+(' marker-start="url(#back)"' if both else '')+'/>'

def start(w,h,title,desc):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-labelledby="title desc">
<title id="title">{escape(title)}</title><desc id="desc">{escape(desc)}</desc>
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10z" fill="{TEAL}"/></marker><marker id="back" viewBox="0 0 10 10" refX="1" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M10 0 L0 5 L10 10z" fill="{TEAL}"/></marker></defs>
<rect width="{w}" height="{h}" fill="#F4F7F8"/><g font-family="Inter, Helvetica Neue, Arial, sans-serif">'''

s=start(1440,1550,'Proposed MVP agent harness','Existing clients and routes retain their contracts. Adapters translate a common execution service into text, voice and job streams. Separate policies share durable domain services and state repositories inside the current backend.')
s+=text(54,54,'MVP  /  BACKEND ARCHITECTURE PROPOSAL',17,TEAL,700)
s+=text(54,104,'One execution service behind the existing API',38,INK,700)
s+=text(54,143,'Keep the product contracts. Consolidate the execution rules.',23,MUTED)
for x,w,t,ls in [(54,420,'iOS app',['Existing requests and SSE parser']), (510,420,'Parent dashboard',['Existing /cos and research clients']), (966,420,'ElevenLabs voice',['Existing OpenAI-compatible stream'])]:
    s+=box(x,178,w,102,t,ls,BLUE)
    s+=arrow(x+w/2,280,x+w/2,318)
s+=rect(54,320,1332,124,'#E9F2FA','#BED3E8')
s+=text(78,356,'EXISTING HTTP CONTRACTS',18,BLUE,700)
s+=text(78,390,'/chat   ·   /cos/chat   ·   /onboarding-chat   ·   /kid-chat',25,INK,600)
s+=text(78,421,'/v1/parent/chat/completions   ·   /v1/chat/completions   ·   /research/runs*   ·   /onboarding/warmup*',20,MUTED)
s+='<path d="M54 478 H1386" stroke="#A3BAC5" stroke-width="2" stroke-dasharray="7 7"/>'
s+=rect(473,461,494,34,'#F4F7F8','#F4F7F8',0)+text(489,486,'IMPLEMENTATION CHANGES BELOW THIS LINE',17,MUTED,650)
for x,w,t,ls in [(54,420,'Text adapter',['Legacy token / tool / error frames']), (510,420,'Voice adapter',['Deltas · article cards · end_call']), (966,420,'Job adapter',['Existing progress / final / polling'])]:
    s+=box(x,518,w,111,t,ls,BLUE)
    s+=arrow(x+w/2,629,x+w/2,674,both=True)
s+=rect(54,680,1332,215,'#E6F3EF','#A9CFC4')
s+=text(80,722,'AgentExecutionService',31,INK,700)
s+=text(80,758,'Trusted identity + run context  →  thread ownership  →  repair  →  execute  →  durable completion',22,INK)
s+=text(80,801,'One place for cancellation, deadlines, retry rules, event filtering and cost attribution',22,TEAL,600)
s+=text(80,841,'Internal events only: TextDelta · ToolStarted · ToolFinished · SafetySignal · Completed · Failed',20,MUTED)
s+=text(80,872,'Model / tool calls: LangGraph + DeepAgents → OpenAI / Tavily, with deadlines and usage accounted centrally.',19,MUTED)
for x,w,t,ls,col in [(54,315,'Parent',['Coach + planning','Keep the flat toolset'],TEAL),(393,315,'Onboarding',['Profile interview','Shared profile schemas'],TEAL),(732,315,'Kid companion',['Separate safety policy','Precheck → stream gate'],GOLD),(1071,315,'Research',['DeepAgents initially','Bounded job execution'],TEAL)]:
    s+=arrow(x+w/2,895,x+w/2,937)
    s+=box(x,943,w,133,t,ls,col)
s+=text(54,1116,'POLICIES STAY DISTINCT     ·     LangGraph stays     ·     Warmup and sync remain explicit workflows',20,MUTED,550)
s+=arrow(384,1140,384,1180)
s+=arrow(1050,1140,1050,1180)
s+=box(54,1186,642,148,'Domain services',['Profiles · planning · research scheduling','Tenant checks + validated commands','Durable write + operation receipt in one transaction'],TEAL)
s+=box(720,1186,666,148,'Execution state and job control',['Checkpoint repository · transcript projections','Run records · leases · cancellation · budget accounting','Keep existing history keys and transcript views'],TEAL)
s+=arrow(384,1334,384,1380)
s+=arrow(1050,1334,1050,1380)
s+=rect(54,1386,1332,91,'#E9EEF2','#CAD6DE')
s+=text(80,1424,'Existing Railway deployment',25,INK,650)
s+=text(80,1455,'DuckDB: domain data + additive run / receipt records       SQLite: existing LangGraph checkpoints',22,MUTED)
s+=text(54,1517,'BLUE  Existing public contract     GREEN  Shared backend implementation     AMBER  Dedicated child safety policy',18,MUTED)
(OUT/'proposed-architecture.svg').write_text(s+'</g></svg>')

s=start(1440,920,'Current MVP harness boundaries','Parent text and voice share the parent graph but duplicate execution loops. Named chat and COS use different thread resolution. Onboarding and kid graphs have separate policies; research has a separate worker. Persistence is split across checkpoints, transcript projections and profile memory.')
s+=text(54,54,'MVP  /  CURRENT DESIGN',17,TEAL,700)
s+=text(54,104,'The graph is shared. The execution rules are scattered.',36,INK,700)
s+=text(54,143,'Each surface owns some combination of repair, stream translation, retries and persistence.',22,MUTED)
rows=[(192,'Parent text','server.generate_stream','Active named conversation','Shared parent graph'),(321,'Planning text','cos._cos_chat_stream','Legacy default conversation','Shared parent graph'),(450,'Parent voice','parent_convai._stream_response','Separate voice thread','Shared parent graph'),(579,'Onboarding and kid','Separate text + voice loops','Profile interview / moderation','Separate graphs'),(708,'Research','ResearchWorker + discovery','Atomic claim / progress rows','DeepAgents')]
for y,t,fn,detail,graph in rows:
    s+=box(54,y,320,103,t,[detail],BLUE)
    s+=arrow(374,y+51,420,y+51)
    s+=box(430,y,578,103,fn,['Per-surface execution and failure handling'],GOLD)
    s+=arrow(1008,y+51,1054,y+51)
    s+=box(1064,y,322,103,graph,['Existing runtime'],TEAL)
s+=text(54,863,'STATE IS SPLIT',17,GOLD,700)
s+=text(234,863,'SQLite checkpoints   ·   DuckDB transcripts and jobs   ·   In-memory profiles with later snapshots',21,MUTED)
(OUT/'current-architecture.svg').write_text(s+'</g></svg>')

s=start(1440,1280,'Proposed turn lifecycle and failure recovery','A mutation and its receipt commit together in DuckDB before its result is checkpointed in SQLite. If execution fails between those operations, the harness reconciles the receipt rather than replaying the mutation. Transcript persistence precedes the unchanged completion marker.')
s+=text(54,54,'MVP  /  PROPOSED EXECUTION LIFECYCLE',17,TEAL,700)
s+=text(54,104,'A durable business effect is not a checkpoint.',38,INK,700)
s+=text(54,146,'The harness must reconcile the gap between two independently committed stores.',23,MUTED)
lanes=[('Client adapter',149),('Execution service',369),('LangGraph',589),('Domain commands',809),('DuckDB',1029),('SQLite',1249)]
for title,x in lanes:
    s+=rect(x-96,185,192,62,'#E9F2FA','#BED3E8',12)+text(x-84,224,title,20,INK,650)
    s+=f'<path d="M{x} 248 V1064" stroke="#CCD8DE" stroke-width="2" stroke-dasharray="5 7"/>'

def seq(a,b,y,label,color=TEAL):
    return text(min(a,b)+10,y-12,label,18,MUTED)+arrow(a,y,b,y,color)

s+=seq(149,369,302,'Authenticated turn')
s+=rect(280,330,396,75,'#E6F3EF','#A9CFC4',12)
s+=text(296,360,'Acquire thread ownership',20,INK,650)
s+=text(296,389,'Reconcile receipts, then repair',19,MUTED)
s+=seq(369,589,451,'Execute with run context')
s+=seq(589,809,514,'Validated tool call')
s+=seq(809,1029,572,'Mutation + receipt')
s+=rect(946,589,260,52,'#E6F3EF','#A9CFC4',10)+text(960,623,'ONE DB TRANSACTION',17,TEAL,700)
s+=seq(1029,809,680,'Committed result')
s+=seq(809,589,732,'Tool result')
s+=seq(589,1249,795,'Checkpoint the graph result')
s+=seq(589,369,855,'Approved text delta')
s+=seq(369,149,910,'Legacy token frame')
s+=seq(369,1029,976,'Persist final transcript and run outcome')
s+=seq(369,149,1043,'Existing [DONE]')
s+=rect(54,1100,1332,132,'#FFF3DF','#E4C895')
s+=text(80,1138,'THE FAILURE WINDOW',18,GOLD,700)
s+=text(80,1174,'If the process stops after the DuckDB commit but before the SQLite checkpoint, recover the receipt.',23,INK,600)
s+=text(80,1208,'Do not repeat the write. Tool loops repeat within the run; successful completion waits for durable finalization.',21,MUTED)
(OUT/'turn-lifecycle.svg').write_text(s+'</g></svg>')
print('Rendered three SVG diagrams to',OUT)
