// Scripted, synthetic parent reflection. No model, storage, clinical measure or score.
export const scenarios = {
  morning: {
    title: 'At the doorway',
    observation: 'My child cried when I said it was time to put shoes on.',
    context: 'School morning; an unfinished cardboard project nearby.',
    parentInterpretation: 'I first read this as refusing to cooperate.',
    parentCapacity: 'I was rushed and running on little sleep.',
    possibilities: ['Leaving an unfinished project might feel hard.', 'Shoes, timing, or something else may matter. We do not know yet.'],
    childPerspective: null,
    before: 'How can I make my child stop resisting every morning?',
    after: 'What might I be missing, and what can I change without giving up the need to leave?',
    adjustment: 'Try one slower instruction. Ask whether they want company or a little space while keeping the departure boundary.',
    words: 'Leaving is hard today. We still need to go. Would you like me beside you or a little space?',
  },
  joy: {
    title: 'A cardboard world',
    observation: 'My child spent a long time building a cardboard world and wanted to show me.',
    context: 'An ordinary afternoon, with no problem to solve.',
    parentInterpretation: 'I focused on praising how impressive it looked.',
    parentCapacity: 'I had a few minutes, but was tempted to improve the design.',
    possibilities: ['They may want shared attention more than an evaluation.', 'They might enjoy explaining, making, or something we have not noticed.'],
    childPerspective: null,
    before: 'What talent does this show, and how can I develop it?',
    after: 'What do they enjoy here, and how can I join without taking over?',
    adjustment: 'Let them lead for a few minutes. Ask about the part they want to show rather than judging the result.',
    words: 'Show me the part you want me to notice. Would you like me to watch, help, or just listen?',
  },
  repair: {
    title: 'After I raised my voice',
    observation: 'I raised my voice. My child went quiet and left the room.',
    context: 'A hard evening after a long day.',
    parentInterpretation: 'I hoped the quiet meant we were okay again.',
    parentCapacity: 'I felt guilty and wanted immediate reassurance.',
    possibilities: ['Quiet does not tell us whether repair happened.', 'They may want space. Their feelings are unknown.'],
    childPerspective: null,
    before: 'How do I get them to forgive me so we can move on?',
    after: 'How can I take responsibility and give them room to respond?',
    adjustment: 'When safe and calm, acknowledge your own action without asking the child to reassure you. Let them respond or take space.',
    words: 'I raised my voice. That was my responsibility. You do not need to make me feel better. I can listen when you want.',
  },
};
export function initial(key='morning') {
  if (!scenarios[key]) throw Error('Unknown synthetic scenario');
  return {key,episode:{id:`synthetic-${key}`,childId:'synthetic-child-1',source:'Synthetic parent report',...structuredClone(scenarios[key])},reviewed:false,capacity:null,action:null,outcome:null,childContribution:null,safetyHold:false};
}
export function review(state) { return {...state, reviewed:true}; }
export function capacity(state,value) {
  if (!['some','none','skip'].includes(value)) throw Error('Invalid capacity response');
  return {...state,capacity:value,action:null,outcome:null};
}
export function adjust(state) {
  if(!state.reviewed) throw Error('Review first');
  if(state.safetyHold) throw Error('Ordinary coaching paused');
  if(!state.capacity) throw Error('Choose or skip capacity question');
  if(state.freeTextEdited) return {...state,action:{kind:'reflection-only',text:'No current response plan. This scripted demo cannot interpret a corrected event. Revisit context or choose another fictional scenario.',words:'No script generated for corrected text.'}};
  const action=state.capacity==='none'
    ? {kind:'support',text:'No new exercise. Keep the next step small; seek practical adult support if available. Lack of time or support is not a parenting failure.',words:'No script required. You can come back later.'}
    : {kind:'parent-adjustment',text:state.episode.adjustment,words:state.episode.words};
  return {...state,action};
}
export function checkIn(state,{parentAction,childResponse='unknown'}) {
  if(!state.action) throw Error('No adjustment selected');
  if(!['tried','not-tried','changed-plan'].includes(parentAction)) throw Error('Unknown parent action');
  if(!['unknown','still-upset','different','declined'].includes(childResponse)) throw Error('Unknown response');
  return {...state,outcome:{parentAction,childResponse,source:'Synthetic parent self-report',conclusion:'This does not establish causality, connection, repair, or the child’s feelings.'}};
}
export function correct(state,text) {
  if(!text.trim()) throw Error('Empty correction');
  return {...state,episode:{...state.episode,observation:text.trim(),context:'Context needs review after correction.',parentInterpretation:'No current interpretation for this corrected event.',parentCapacity:'Capacity needs a fresh review.',possibilities:['We do not know what fits this corrected event.'],adjustment:null,words:null},reviewed:false,capacity:null,action:null,outcome:null,childContribution:null,freeTextEdited:true};
}
export function childContribution(state,{text=null,declined=false}={}) {
  if(declined) return {...state,childContribution:{status:'declined',text:null,interpretation:'No conclusion about trust, attachment or cooperation.'}};
  if(!text?.trim()) throw Error('A quote or a skip is required');
  return {...state,childContribution:{status:'parent-reported',text:text.trim(),source:'Parent reports child words • synthetic',verifiedWithChild:false}};
}
export function holdForSafety(state) {
  return {...state,safetyHold:true,action:null,outcome:null};
}
export function reflection(state) {
  return [
    {dimension:'What I noticed',status:state.reviewed?'Parent reviewed':'Needs review',text:state.episode.observation,source:state.episode.source},
    {dimension:'My first interpretation',status:'Parent self-report',text:state.episode.parentInterpretation,source:'Synthetic parent report; not objective truth'},
    {dimension:'What else could fit',status:'Possibilities, not findings',text:state.episode.possibilities.join(' '),source:'Scripted alternatives; not measured child needs'},
    {dimension:'Their perspective',status:state.childContribution?.status||'Unknown',text:state.childContribution?.text||'We have not heard their perspective. Skipping does not imply anything about the relationship.',source:state.childContribution?.source||'No direct child evidence'},
    {dimension:'My room to respond',status:state.capacity==='none'?'No capacity today':'Private parent context',text:state.episode.parentCapacity,source:'Parent self-report; excluded from brief'},
    {dimension:'What I chose',status:state.action?'Optional next step':'Not chosen',text:state.action?.text||'No action required.',source:'Parent-selected response, not an alliance rating'},
  ];
}
export function portableBrief(state,include=false) {
  return {schemaVersion:2,synthetic:true,purpose:'Help a parent consider a small response adjustment',notes:include&&state.reviewed&&!state.safetyHold&&!state.freeTextEdited?[{observation:state.episode.observation,context:state.episode.context,source:state.episode.source}]:[],excluded:['Private parent capacity, guilt and stress notes','Child-needs hypotheses and relational labels','Raw conversation and child quotes','Health, family conflict, names and location'],limits:'No alliance score or clinical measure. Manual preview only; no connector.'};
}
