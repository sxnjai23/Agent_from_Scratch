from .llm import LLMClient
from .tools import get_all_schemas, execute
from harness.tracing import Tracer
import json

def run_agent(task ,max_steps ,llm , run_id):
    tracer = Tracer(run_id)
    messages = [{"role":"system" , "content" : "you are helpfull ai agent with multiple tools you can choose whatever you want"},
               {"role":"user" , "content":task}]


    schemas = get_all_schemas()
    tracer.log({"event": "schemas", "schemas": schemas})
    print("=== SCHEMAS SENT TO MODEL ===")
    print(json.dumps(schemas, indent=2))

    for step in range(max_steps):
        tracer.log({"event": "request", "step": step, "messages": messages})
        print("--- messages going INTO this call ---")
        print(json.dumps(messages, indent=2, default=str))

        response = llm.call(messages, tools = schemas)

        tracer.log({
            "event": "response",
            "step": step,
            "content": response.content,
            "tool_calls": response.tool_calls,
            "usage": response.usage,
        })

        print("--- raw response from model ---")
        print("content:", response.content)
        print("tool_calls:", response.tool_calls)
        print("usage:", response.usage)

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
        print("--- assistant message appended ---")
        print(json.dumps(assistant_msg, indent=2))

        if not response.tool_calls:
            tracer.log({"event": "final_answer", "step": step, "answer": response.content})
            tracer.close()
            return response.content

        for tc in response.tool_calls:
            print(f"\n--- running tool: {tc.name}({tc.arguments}) ---")
            result = execute(tc.name, tc.arguments)
            print(f"--- tool result: {result} ---")

            tool_msg = {
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            }
            messages.append(tool_msg)
            tracer.log({"event": "tool_call", "step": step, "name": tc.name, "args": tc.arguments, "result": result})
            print("--- tool message appended ---")
            print(json.dumps(tool_msg, indent=2))
    
    tracer.log({"event": "max_steps_reached", "step": step})
    tracer.close()
    return "Stopped: max steps reached"


if __name__ == "__main__":
    llm = LLMClient(model="openai/gpt-oss-20b")
    answer = run_agent(max_steps=10 ,task= "use the math tool",llm=llm,run_id="logger")
    print(answer)