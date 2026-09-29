"""
run_evals.py — runs the agent on every task in tasks.json,
checks each answer, and prints a score.

Run from the agent_harness folder:  python -m evals.run_evals
"""

import json
import time

from agent.llm import LLMClient
from agent.loop import run_agent


def grade(answer, expected):
    """Pass if the expected text appears in the answer (ignoring case and commas)."""
    cleaned = answer.lower().replace(",", "")
    return expected.lower() in cleaned


def main():
    with open("evals/tasks2.json") as f:
        tasks = json.load(f)

    llm = LLMClient()
    run_stamp = str(int(time.time()))  # makes session ids unique for every eval run
    results = []

    for task in tasks:
        print(f"Running {task['id']}...")
        try:
            result = run_agent(
                task=task["prompt"],
                llm=llm,
                session_id=f"eval-{task['id']}-{run_stamp}",  # fresh conversation each time
                run_id=f"eval-{task['id']}",
            )
        except Exception as e:
            # one broken task should not stop the whole eval
            result = {"answer": f"CRASH: {e}", "steps": 0, "tokens": 0, "status": "crash"}

        result["id"] = task["id"]
        result["passed"] = grade(result["answer"], task["expected"])
        results.append(result)

        time.sleep(2)  # be gentle with Groq's rate limits

    # ---- report ----
    print("\n=== RESULTS ===")
    for r in results:
        mark = "PASS" if r["passed"] else "FAIL"
        print(f"{mark}  {r['id']:<10} steps={r['steps']}  tokens={r['tokens']}  status={r['status']}")

    passed = sum(r["passed"] for r in results)
    total_tokens = sum(r["tokens"] for r in results)
    print(f"\nScore: {passed}/{len(results)} passed, {total_tokens} tokens total")

    # save so you can compare against later runs
    with open("evals/results.json", "w") as f:
        json.dump(results, f, indent=2)


if __name__ == "__main__":
    for i in range(10):
        main()