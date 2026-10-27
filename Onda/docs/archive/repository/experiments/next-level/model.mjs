// Pure local experiment model. No model, network, storage or auth calls.
export const initial = () => ({ stage:0, messages:[], observation:null, experiment:null, outcomes:[], remember:false });
export function observe(state, text) {
  if (!text.trim()) throw new Error('Describe an observation first');
  return {...state, observation:{id:'obs-synthetic-1',childId:'child-synthetic-1',text:text.trim(),source:'Parent report • synthetic session',status:'proposed',context:'School mornings',recordedAt:'2026-10-13',reviewAfter:'2026-11-12',interpretation:'We do not yet know why this happens.'}};
}
export function confirm(state, remember) {
  if(!state.observation) throw new Error('No observation to confirm');
  return {...state,remember,observation:{...state.observation,status:remember?'confirmed':'session-only'}};
}
export function correct(state,text) {
  if(!state.observation || !text.trim()) throw new Error('Correction cannot be empty');
  return {...state,observation:{...state.observation,text:text.trim(),status:'proposed'},remember:false,experiment:null,outcomes:[]};
}
export function startExperiment(state) {
  if(!state.observation || state.observation.status==='proposed') throw new Error('Review the observation before starting');
  return {...state,experiment:{id:'exp-synthetic-1',observationId:state.observation.id,status:'trying',action:'Offer two shoe choices before the doorway; leave a five-minute buffer.',duration:'3 school mornings',measure:'Was leaving easier, unchanged, or harder?',stop:'Stop if either of you becomes more distressed.',evidence:'A low-risk routine adjustment to test, not a diagnosis or proven treatment.'}};
}
export function outcome(state, result) {
  if(!state.experiment) throw new Error('No experiment is active');
  if(!['easier','same','harder','skipped'].includes(result)) throw new Error('Unknown result');
  const outcomes=[...state.outcomes,{result,day:state.outcomes.length+1,source:'Parent report',causalClaim:false}];
  return {...state,outcomes,experiment:{...state.experiment,status:result==='harder'?'paused':'trying'}};
}
export function exportNotes(state) {
  // Export only reviewed observations and opted-in notes; never raw chat.
  return {schemaVersion:1,synthetic:true,observation:state.remember?state.observation:null,experiment:state.remember?state.experiment:null,outcomes:state.remember?state.outcomes:[],limitations:'Parent reports; no diagnosis, developmental score, or causal proof.'};
}
export function providerPlan({eligible=false,identityGranted=false,usageGranted=false}={}) {
  return eligible&&identityGranted&&usageGranted?'chatgpt-plan-responses':'capped-platform-api';
}
export const understanding = () => [
 {id:'strength',kind:'Strength & interest',text:'Enjoys making elaborate cardboard worlds.',source:'Parent report • synthetic',certainty:'One example, not a fixed trait',reviewed:true,sensitive:false},
 {id:'perspective',kind:'Child perspective',text:'“I want time to finish what I am making.”',source:'Parent-reported child words • synthetic',certainty:'Not directly verified with the child',reviewed:true,sensitive:false},
 {id:'context',kind:'Context',text:'Leaving is harder when a project is unfinished.',source:'Parent interpretation • synthetic',certainty:'A possibility to check, not a cause',reviewed:false,sensitive:false},
 {id:'health',kind:'Sensitive note',text:'A parent-reported health concern, intentionally withheld in this demo.',source:'Parent report • synthetic',certainty:'Do not infer a diagnosis',reviewed:true,sensitive:true}
];
export function sharePreview(items,selected) {
  return {schemaVersion:1,synthetic:true,purpose:'Help suggest a playful transition routine',notes:items.filter(n=>selected.includes(n.id)&&n.reviewed&&!n.sensitive).map(({kind,text,source,certainty})=>({kind,text,source,certainty})),excluded:['Names, exact age, school, location','Health and diagnostic information','Raw conversations','Unreviewed interpretations'],permissions:'Manual export only. No connector is active.',recipientInstruction:'Treat as limited parent reports, never as diagnosis or permanent child traits.'};
}
