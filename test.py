from agent.llm import LLMClient
from agent.loop import run_agent

llm = LLMClient()

# tasks = [
#     "What is 15 times 7?",                              # mathematic_operations
#     "What's the weather in Chennai?",                    # get_weather
#     "Use code to find the 20th Fibonacci number",         # run_python_code
#     "What's 100 divided by 0?",                            # error handling — divide by zero
#     "Call a tool that doesn't exist called fly_to_moon",    # unknown tool handling
# ]

# for i, task in enumerate(tasks):
#     print(f"\n=== TEST {i}: {task} ===")
#     answer = run_agent(task=task, llm=llm, session_id=f"smoketest-{i}", run_id=f"smoketest-{i}")
#     print("Answer:", answer)

if __name__ == "__main__":
    llm = LLMClient()
    while True:
        task = input(":")
        if task.lower() == "exit":
            break
        answer = run_agent(task=task, llm=llm, session_id = "test-02", max_steps=10, run_id="logger2")
        print(answer)