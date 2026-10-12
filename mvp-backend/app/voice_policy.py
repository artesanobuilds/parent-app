"""Trusted presentation policy applied by the answering graph, never client input.

Voice changes phrasing only. Parent-approved kid boundaries, tool permissions,
moderation, and escalation rules remain authoritative.
"""

KID_VOICE_POLICY = (
    "\n\n## Voice mode\n"
    "Your reply will be spoken aloud. Keep sentences short (≤15 words). "
    "Prefer one or two short sentences, then give the child room to answer. "
    "No markdown formatting, no asterisks, no parentheticals, and no spoken URLs. "
    "Use commas and periods for rhythm. Ask at most one question at a time. "
    "If an allowed tool is needed, briefly say what you are checking before using it. "
    "This presentation guidance does not change the grown-up's boundaries, "
    "your permitted tools, or any safety and escalation rules."
)

PARENT_VOICE_POLICY = (
    "\n\n## Voice mode\n"
    "You are being spoken aloud to the parent. Reply in short, natural spoken "
    "sentences, with one question at a time. No markdown headings, bullet lists, "
    "asterisks, or bold. Keep content recommendations as [Title](mvp://library/{id}): "
    "the adapter speaks the label and displays its card. "
    "If you need to use a tool, first say a short sentence such as "
    "'Let me look that up.' Never claim a task succeeded until its tool confirms it. "
    "These presentation rules do not change your coaching boundaries or tool permissions."
)


def is_voice_surface(surface: str) -> bool:
    if surface not in {"text", "voice"}:
        raise ValueError(f"Unknown agent surface: {surface}")
    return surface == "voice"
