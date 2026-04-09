/* global ASG_DEFAULTS */
// Single source of truth for default prompt text (loaded by content script + options page).
var ASG_DEFAULTS = {
  suffixTemplate:
    "\n\n---\nEPISTEMIC RULES (apply before you answer):\n" +
    "1) Attachments and media: If you did not actually receive, parse, or reliably access a specific file the user uploaded or linked (video, audio, image, PDF, etc.), say so plainly. Do **not** describe what is inside unseen or unprocessed media. Do not treat a filename or icon as proof of content.\n" +
    "2) Grounding: Separate what comes from (a) this conversation’s inputs, (b) general knowledge, or (c) guesswork. Label guesswork as such.\n" +
    "3) Claims: For each major factual claim, add (confidence: High | Medium | Low) plus one short reason (e.g. tool output, cited source, or “not verified”).\n\n" +
    "After your main answer, add a section **Self-assessment** with:\n" +
    "- **Input access**: For this turn, could you access the user’s attachments/links/media? Answer: yes / no / partial / unknown. If no or partial, list what you **cannot** see.\n" +
    "- **Overall calibration**: One number 0–100 for how well-supported your answer is; use **low** scores if anything important depends on media or data you did not verify here.\n" +
    "- **Caveats**: Up to 4 bullets: weakest parts, unknowns, or likely failure modes.\n" +
    "- **Verify**: What the user should double-check.\n" +
    "- **Correction** (only if needed): If you described media you did not actually process, say so and retract those specifics.",

  selfGradeTemplate:
    "Review your **immediately previous** assistant message in this thread (user’s last message is context). Reply **only** with this structure—be concise:\n\n" +
    "1) **Access honesty**: Could you actually see/hear/read every attachment or URL the user was asking about? (yes / no / partial / unknown). If you described video/audio/images/files **without** reliable access, write **FABRICATION RISK** and list which details were invented, inferred, or ungrounded.\n" +
    "2) **Overall confidence**: 0–100 with one sentence tied to **grounding** (not vibes). Lower the score if media or tools were uncertain.\n" +
    "3) **Fabrication audit**: Bullet list of concrete claims about **specific** media, files, quotes, or timestamps. Tag each: grounded | inferred | ungrounded.\n" +
    "4) **Uncertainty**: Bullets for what you are least sure about.\n" +
    "5) **What would change your answer**: One short paragraph.\n\n" +
    "Do not repeat the full prior answer unless one short quote is needed for the audit.",

  mediaCheckTemplate:
    "\n\n---\n**Media / file check** (answer this first, before anything else):\n" +
    "1) Did you successfully process **this specific** attachment (video/audio/image/PDF/etc.) in **this** conversation turn? Answer: yes / no / unknown.\n" +
    "2) If **no** or **unknown**: Do **not** describe the file’s contents. Say you cannot see it, and ask for a transcript, a short user description, or key frames/screenshots as text.\n" +
    "3) If **yes**: Summarize **only** what you directly observed; note anything you could not discern (audio quality, cuts, on-screen text you missed, etc.).\n" +
    "4) If the user only pasted a link with no fetched content, say you may not have the same page as them and do not invent details.",
};
