"""
smoke_test.py — runs the agent on a few tasks, one at a time,
so we can see with our own eyes whether everything works together.
"""

from agent.llm import LLMClient
from agent.loop import run_agent

llm = LLMClient()

tasks = [
    "What is 15 times 7?",                        # should use the math tool
    "What's the weather in Chennai?",              # should use the weather tool
    "Use code to find the 20th Fibonacci number",   # should use the sandbox
]

for i, task in enumerate(tasks):
    print(f"\n=== TEST {i}: {task} ===")
    answer = run_agent(task=task, llm=llm, session_id=f"smoke-{i}", run_id=f"smoke-{i}")
    print("Answer:", answer)