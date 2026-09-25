"""
Tracing.py -> used to trace the agent and log the messages in a file. 
It creates a new file for each run and logs the messages in JSONL format.

"""


import json


class Tracer():
    def __init__(self, run_id):
        self.file = open(f"{run_id}.jsonl", "a")

    def log(self, data: dict):
        self.file.write(json.dumps(data, default=str) + "\n")
        self.file.flush()  # write immediately, don't wait for buffer to fill

    def close(self):
        self.file.close()