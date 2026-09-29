"""
main.py — command-line entry point for the agent.

Usage:
    python main.py                          interactive chat
    python main.py "What is 15 times 7?"    run one task and exit
    python main.py --new "..."              start a fresh session
    python main.py --model llama-3.3-70b-versatile "..."
"""

import argparse
import os
import time

from agent.llm import LLMClient
from agent.loop import run_agent

if os.name == "nt":
    os.system("")  # let Windows terminals understand color codes


class C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"


LINE = f"{C.DIM}{'-' * 40}{C.RESET}"

BANNER = f"""{C.CYAN}{C.BOLD}
 ██████╗ ██╗██╗   ██╗     █████╗  ██████╗ ███████╗███╗   ██╗████████╗
 ██╔══██╗██║╚██╗ ██╔╝    ██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
 ██║  ██║██║ ╚████╔╝     ███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
 ██║  ██║██║  ╚██╔╝      ██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
 ██████╔╝██║   ██║       ██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
 ╚═════╝ ╚═╝   ╚═╝       ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
{C.RESET}{C.DIM}                agent + harness — type 'exit' to quit{C.RESET}
"""


def build_parser():
    parser = argparse.ArgumentParser(
        prog="agent",
        description="A small AI agent with tools: math, weather, and sandboxed Python.",
    )
    parser.add_argument(
        "task", nargs="?", default=None,
        help="the task to run. Omit this to start an interactive chat.",
    )
    parser.add_argument("--model", default="openai/gpt-oss-20b", help="Groq model to use")
    parser.add_argument("--session", default="default", help="session id (conversation to resume)")
    parser.add_argument("--new", action="store_true", help="start a fresh session instead of resuming")
    parser.add_argument("--max-steps", type=int, default=10, help="max tool-call steps per task")
    parser.add_argument("--max-tokens", type=int, default=4000, help="token budget per task")
    return parser


def run_one(task, llm, args):
    """Run a single task through the agent and return the result dict."""
    return run_agent(
        task=task,
        llm=llm,
        session_id=args.session,
        max_steps=args.max_steps
    )


def one_shot(task, llm, args):
    """Run one task, print just the answer, and exit."""
    result = run_one(task, llm, args)
    print(f"{C.MAGENTA}{result['answer']}{C.RESET}")
    return result


def interactive(llm, args):
    """A small colored chat loop, with a separator after every message."""
    print(BANNER)
    print(f"{C.CYAN}{C.BOLD}Agent + Harness{C.RESET} {C.DIM}— type 'exit' to quit{C.RESET}\n")

    while True:
        try:
            task = input(f"{C.CYAN}You ›{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print(f"\n{C.DIM}Varatuma Byee....{C.RESET}")
            break

        if not task:
            continue
        if task.lower() in ("exit", "quit"):
            print(f"{C.DIM}Varatuma Byee....{C.RESET}")
            break

        print(LINE)

        result = run_one(task, llm, args)
        status_color = C.GREEN if result["status"] == "done" else C.YELLOW

        print(f"{C.MAGENTA}Agent ›{C.RESET} {result['answer']}")
        print(f"{C.DIM}[{status_color}{result['status']}{C.DIM} · "
              f"{result['steps']} steps · {result['tokens']} tokens]{C.RESET}")
        print(LINE)


def main():
    args = build_parser().parse_args()

    if args.new:
        args.session = f"{args.session}-{time.strftime('%Y%m%d%H%M%S')}"

    llm = LLMClient()

    if args.task:
        one_shot(args.task, llm, args)
    else:
        interactive(llm, args)


if __name__ == "__main__":
    main()