"""
    Importing the Main Parts like llm.py and Tools.py
    and traccer for traccing.
"""

from .llm import LLMClient
from .tools import get_all_schemas, execute
from harness.tracing import Tracer
import json

"""
    run_agent is used to run the AGENT and act as a agent .
    LOL - No acting this is how a actuall agent WORKS!
    It creates a tracer id if you want it can create a new file and log onto it.

"""


def run_agent(task, llm, max_steps=10, run_id="logger"):
    tracer = Tracer(run_id)
    messages = [
        {"role": "system", "content": "You are a helpful agent. Use tools when needed."},
        {"role": "user", "content": task},
    ]

    #Get all the Schemas from tools list
    schemas = get_all_schemas()

    """
        Agent is a Goal Based it runs untill the goal got satisfied here we giving max_steps for learning.
        if you want you can change  and test it on your own.
        Here we used list comprehension to get the  
    
    #IN DEPTH : tc= tool_call id's, name ,arguments.
        
        tc.id = the function id--> address stored in ram
        tc.name = the name of the function.
        arguments = get the argument for our functions.

    """
    

    for step in range(max_steps):
        response = llm.call(messages, tools=schemas)

        assistant_msg = {
            "role": "assistant",
            "content": response.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
                }
                for tc in response.tool_calls
            ] if response.tool_calls else None,
        }
        
        messages.append(assistant_msg)

        if not response.tool_calls:
            tracer.log(f"Done: {response.content}")
            tracer.close()
            return response.content

        for tc in response.tool_calls:
            result = execute(tc.name, tc.arguments)
            tracer.log(f"{tc.name}({tc.arguments}) -> {result}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    tracer.log(f"Stopped: max steps ({max_steps}) reached")
    tracer.close()
    return "Stopped: max steps reached"


if __name__ == "__main__":
    llm = LLMClient()
    answer = run_agent(task="before this message what is asked ?", llm=llm)
    print(answer)