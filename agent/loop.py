"""
    Importing the Main Parts like llm.py and Tools.py
    and traccer for traccing.
"""

from .llm import LLMClient
from .tools import get_all_schemas, execute
from .context import load_session, save_session, maybe_summarize
from harness.tracing import Tracer
import json

"""
    run_agent is used to run the AGENT and act as a agent .
    LOL - No acting this is how a actuall agent WORKS!
    It creates a tracer id if you want it can create a new file and log onto it.

"""


def run_agent(task, llm, max_steps=10,session_id = "test-01", run_id="logger"):
    tracer = Tracer(run_id)
    messages = load_session(session_id)
    if messages is None:
        content = """ You are a helpful agent. For every arithmetic operation, no matter how
    simple, call mathematic_operations — never compute arithmetic yourself, not even one 
    step. If a task needs several operations, call the tool once per operation, using the
    result of one call as the input to the next. Only give a final answer once every operation
    has gone through a tool."""
        
        messages = [{"role": "system", "content": content},]
        tracer.log(f"New session: {run_id}")
    else:
        messages = maybe_summarize(messages, llm)
        tracer.log(f"Resumed session: {run_id} ({len(messages)} messages so far)")

    # the new task is just another user message added onto the history
    messages.append({"role": "user", "content": task})

    #Get all the Schemas from tools list
    schemas = get_all_schemas()

    """
        Agent is a Goal Based it runs untill the goal got satisfied here we giving max_steps for learning.
        if you want you can change  and test it on your own.
        Here we used list comprehension to get the  
    
    #IN DEPTH : tc= tool_call id's, name ,arguments.
        
        tc.id = A unique string LLM assigns to this specific tool call, used to match this result back to that exact request
        tc.name = the name of the function.
        arguments = get the argument for our functions.

    """

    total_tokens = 0
    MAX_TOKENS = 14000

    for step in range(max_steps):
        if total_tokens > MAX_TOKENS:
            tracer.log(f"Stopped: max tokens ({MAX_TOKENS}) reached")
            save_session(session_id, messages)
            tracer.close()
            return {"answer": f"Stopped: max tokens ({MAX_TOKENS}) reached", "steps": step,
                    "tokens": total_tokens, "status": "budget"}

        response = llm.call(messages, tools=schemas)
        total_tokens += response.usage.get("input_tokens", 0) + response.usage.get("output_tokens", 0)

        assistant_msg = {"role": "assistant", "content": response.content}
        if response.tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in response.tool_calls
            ]
        messages.append(assistant_msg)

        if not response.tool_calls:
            save_session(session_id, messages)
            tracer.log(f"Done: {response.content}")
            tracer.close()
            return {"answer": response.content, "steps": step + 1,
                    "tokens": total_tokens, "status": "done"}

        for tc in response.tool_calls:
            result = execute(tc.name, tc.arguments)
            tracer.log(f"{tc.name}({tc.arguments}) -> {result}")
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        save_session(session_id, messages)

    tracer.log(f"Stopped: max steps ({max_steps}) reached")
    save_session(session_id, messages)
    tracer.close()
    return {"answer": "Stopped: max steps reached", "steps": max_steps,
            "tokens": total_tokens, "status": "max_steps"}



"""
    For loacl testing the file you can uncomment the
    below code and run it on your local machine and test it.


# if __name__ == "__main__":
#     llm = LLMClient()
#     while True:
#         task = input(":")
#         if task.lower() == "exit":
#             break
#         result = run_agent(task=task, llm=llm, session_id = "test-01", max_steps=10, run_id="logger")
#         print(result["answer"])

"""