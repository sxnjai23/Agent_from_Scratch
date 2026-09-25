"""
sandbox.py — runs untrusted Python code (code the LLM wrote) safely,
inside a disposable Docker container instead of on our real machine.

Think of it like this: we never let the model's code touch our actual
computer. We hand it a throwaway "box" to run in, watch it from outside,
and if it misbehaves or takes too long, we just destroy the box.
"""

import docker

# one shared connection to Docker, reused across every call
client = docker.from_env()


def run_python_code(code: str, timeout_seconds: int = 5) -> str:
    """
    Run a string of Python code inside an isolated container.

    Returns whatever the code printed, or a clear error message if it
    crashed, timed out, or misbehaved. Never raises — safe to call
    directly from execute() in tools.py.
    """

    # Step 1: start a fresh, disposable container.
    # "python:3.11-slim" is a small pre-made Linux + Python environment.
    # detach=True means: start it running in the background, don't wait here.
    container = client.containers.run(
        "python:3.11-slim",
        ["python", "-c", code],
        detach=True,
        mem_limit="128m",        # hard cap on memory — can't eat all our RAM
        network_disabled=True,   # no internet access from inside the box
    )

    try:
        # Step 2: watch from the outside, with a time limit.
        # We are NOT inside the container — we're just waiting for it
        # to report back that it finished. If it takes too long, we
        # give up waiting and forcibly stop it ourselves.
        try:
            result = container.wait(timeout=timeout_seconds)
        except Exception:
            container.kill()
            return f"Error: code took longer than {timeout_seconds} seconds and was stopped."

        # Step 3: read back whatever the code printed while it ran.
        # This comes back as raw bytes, so we decode it into readable text.
        output = container.logs().decode("utf-8").strip()

        # Step 4: check whether the code actually succeeded.
        # A nonzero status code means the code crashed on its own
        # (e.g. a NameError or ZeroDivisionError), even though the
        # container itself ran fine.
        status_code = result["StatusCode"]
        if status_code != 0:
            return f"Error: the code crashed (exit code {status_code}). Output was:\n{output}"

        return output

    finally:
        # Step 5: always clean up, no matter what happened above —
        # success, timeout, or crash. force=True handles the case
        # where the container might still be shutting down.
        container.remove(force=True)


if __name__ == "__main__":
    # quick manual tests — run this file directly to check the sandbox works
    print("Normal code:")
    print(run_python_code("print(1 + 1)"))

    print("\nCode that crashes:")
    print(run_python_code("1 / 0"))

    print("\nCode that hangs (should time out):")
    print(run_python_code("while True: pass", timeout_seconds=3))