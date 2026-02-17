## Onboarding Trait Spec

Purpose: guide the onboarding agent to collect the minimum useful parent/child context for personalized, attachment-aware coaching that aligns with Dr. Becky Kennedy’s focus on connection/repair and core developmental psychology.

### Parent traits to collect (with rationale)
- Household structure (single, partnered, co-parenting, divorced/separated, widowed): shapes load, support, scheduling, and how to frame co-parenting/transition plans.
- Employment/availability (stay-at-home, part-time, full-time, shift work, travel) + work hours/energy pattern: affects time/energy and realistic routines.
- Support system (family, friends, childcare, community/faith, none) + boundaries: buffers stress; guides suggestions for respite and delegation.
- Cultural/primary language considerations: informs values, communication norms, and resources that feel congruent.
- Parenting style tendencies (authoritative/connection-seeking vs. power/withdrawal patterns): signals which strategies will land; grounded in Baumrind + Becky Kennedy’s “connection before correction.”
- Current stressors and regulation strategies (what works/backfires): parent regulation predicts child co-regulation; informs doable micro-interventions.
- Default stress response and “dreaded moments”: targets prevention and scripts at the hardest times of day.
- Mental/physical health flags (self-reported, non-clinical): affects capacity; prompts gentle pacing and referrals if needed.
- Goals and pain points (e.g., mornings, sibling conflict, screen use, sleep): anchors advice to what matters now.
- Coparent dynamics/boundaries (if applicable): informs consistent scripts and handoffs.
- Preferred guidance style (concise scripts vs. explanations; bullet vs. narrative): improves adherence and fit.

### Child traits to collect (per child, with rationale)
- Age and grade/developmental band: calibrates expectations and skills (e.g., toddler emotion labeling vs. tween independence).
- Temperament/traits (e.g., sensitivity, activity level, adaptability, intensity; intro-/extraversion): from Thomas & Chess/Kagan; tailors environment and scripts.
- Interests/motivators: fuels engagement, rewards, and connection rituals.
- Strengths (incl. academic) and current challenges (behavioral, social, academic): focuses interventions and celebrates wins.
- Emotion regulation skills, triggers, and escalation pattern; calming strategies: informs co-regulation scripts and prevention.
- Social profile (peer fit, friendships, conflict style, bullying risk) and sibling conflict patterns/repair helpers: guides coaching on belonging, safety, and family dynamics.
- Learning profile (prefers visual/auditory/kinesthetic; executive function notes): shapes scaffolds, routines, and instruction.
- Neurodiversity/special needs/health (diagnosed or suspected): ensures accommodations and pacing; avoids generic advice.
- Recent changes/losses: ties behavior to context, surfaces transition supports.
- School context/teacher notes; academic strengths: aligns strategies with classroom reality and pressures.
- Sensory notes (seek/avoid for noise, touch, movement): reduces overload and mismatches.
- Sleep and routines: foundational for behavior/emotion regulation.
- Motivators/rewards that work; safety flags (non-clinical): aligns reinforcement and risk awareness.

### Why these (sources & framing)
- Attachment/co-regulation emphasis from Dr. Becky Kennedy’s “connection before correction” and rupture-repair.
- Temperament research (Thomas & Chess; Kagan) for fit between child traits and environment.
- Parenting style impacts (Baumrind) to align strategies with authoritative, connection-forward approaches.
- Executive function and learning supports from developmental/education research to match scaffolds to child profile.
- Family context (structure, support, work patterns) is a strong moderator of what is feasible and sustainable.

### How the agent should use this
- Ask concise, empathetic questions; reflect back specifics.
- When enough detail is gathered to update a profile, call `FoundMoreAboutParent` or `FoundMoreAboutChild(child_name)` with structured fields (even partials).
- Default to “small next step” recommendations matched to the collected traits; avoid medical advice and invite professional support when needed.

