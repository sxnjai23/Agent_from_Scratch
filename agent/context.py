"""
session.py,summarize.py  — save and load a conversation's messages to/from disk,
so an agent can pick up where it left off across separate runs and  condenses old messages into a short summary so a long
conversation doesn't grow forever.

"""

import json
import os


SUMMARIZE_AFTER = 12  # if there are more messages than this, summarize the old ones
KEEP_RECENT = 6  # always keep this many of the most recent messages in full


SESSIONS_DIR = "sessions"


def load_session(session_id: str) -> list[dict] | None:
    """Return the saved messages list for this session, or None if it doesn't exist yet."""
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def save_session(session_id: str, messages: list[dict]):
    """Write the messages list to disk, overwriting any previous save."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    path = os.path.join(SESSIONS_DIR, f"{session_id}.json")
    with open(path, "w") as f:
        json.dump(messages, f, indent=2)



def maybe_summarize(messages: list[dict], llm) -> list[dict]:
    """If the conversation is long, replace the old part with one summary message."""
    if len(messages) <= SUMMARIZE_AFTER:
        return messages  # still short enough, nothing to do

    system_msg = messages[0]                 # keep the system prompt as-is
    old_messages = messages[1:-KEEP_RECENT]   # the middle chunk to compress
    recent_messages = messages[-KEEP_RECENT:] # keep these untouched

    summary_prompt = [
        {"role": "system", "content": "Summarize this conversation in 3-5 sentences. "
                                       "Keep any concrete facts, numbers, or decisions."},
        {"role": "user", "content": str(old_messages)},
    ]
    response = llm.call(summary_prompt)  # a plain call, no tools needed for this one

    summary_msg = {"role": "system", "content": f"Earlier conversation summary: {response.content}"}

    return [system_msg, summary_msg] + recent_messages