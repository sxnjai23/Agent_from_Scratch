"""

    Replayiong Just opening the file(logger.jsonl)
    for ezxplictly seeing the looger file 

"""
import json

def replay(run_id):
    with open(f"{run_id}.jsonl") as f:
        for i, line in enumerate(f):
            event = json.loads(line)
            print(f"[{i}] {event.get('event')}")
            print(json.dumps(event, indent=2))
            print("-" * 40)

replay("run1")