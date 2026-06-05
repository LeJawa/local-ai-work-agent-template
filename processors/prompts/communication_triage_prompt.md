/no_think

Classify each message into exactly one category.

Return ONLY valid JSON using this exact shape:

{{JSON_FORMAT}}

Category definitions:

needs_reply:
- Use this when someone asks a direct question or appears to expect a response from Luis.
- Examples: client questions, scheduling questions, requests for clarification, replies needed from a real person.

needs_action:
- Use this when something needs to be done, but the main task is not simply replying.
- Examples: pay invoice, submit form, review security alert, confirm appointment, resend document, check bug report.
- Include a short todo_title that could later be sent to Microsoft To Do.

waiting_on:
- Use this when Luis appears to be waiting for someone else to respond, send something, approve something, or complete something.
- Only use this if the message clearly indicates Luis is waiting on another person.

follow_up:
- Use this when the message does not need immediate action today, but should be checked again later.
- Examples: proposal sent and awaiting response, event reminder to revisit, conversation that may need a later check-in.

fyi:
- Use this for informational messages only.
- Examples: newsletters, receipts, routine updates, completed backups, marketing announcements, confirmations with no action.

undesired:
- Use this for undesired emails only, like phishing or scam emails.

Rules:
- Return only JSON.
- Do not explain.
- Do not reason step by step.
- Use the source from the Source field.
- Use the sender from the From field.
- Use the subject from the Subject field.
- Keep each summary short, 1-2 sentences max.
- Put each message in only one category.
- Include every message in the batch exactly once.
- Do not treat marketing events or newsletters as real calendar commitments.
- Appointment confirmations only need action if the message asks Luis to confirm, reply, review, or do something.
- Questions from real people usually belong in needs_reply.
- Billing, forms, security alerts, and appointment confirmations usually belong in needs_action if they require action.
- If someone else says they will review, send, approve, or get back to Luis, use waiting_on.
- If Luis should check back later but does not need to act today, use follow_up.

Messages:

{{MESSAGES}}
