"""
tools.py — turns Python functions into schemas the LLM can read,
and runs them safely when the model asks for one.
"""

import inspect
import json
import os
import requests
from harness.sandbox import run_python_code as _run_python_code


TOOLS = {}  # name -> function, with .schema attached


def tool(func):
    """Decorator: builds a schema for func and registers it."""
    sig = inspect.signature(func)  #--> Mathematic , Weather

    properties = {}
    required = []

    type_map = {str: "string", int: "integer", float: "number", bool: "boolean"}

    for name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else str
        properties[name] = {"type": type_map.get(annotation, "string")}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    func.schema = {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {"type": "object", "properties": properties, "required": required},
        },
    }
    TOOLS[func.__name__] = func
    return func


def get_all_schemas() -> list[dict]:
    return [func.schema for func in TOOLS.values()]


def execute(name: str, args: dict) -> str:
    """Run a tool call safely. Never raises — always returns a string."""
    if name not in TOOLS:
        return f"Error: unknown tool '{name}'"

    try:
        result = TOOLS[name](**args)
    except Exception as e:
        return f"Error: '{name}' failed: {e}"

    return json.dumps(result) if isinstance(result, (dict, list)) else str(result)


# ---- tools ----

@tool
def mathematic_operations(a: float, b: float, operation: str) -> float:
    """Perform a math operation on two numbers. operation must be one of:
    'add', 'sub', 'multiply', 'divide'."""
    if operation == "add":
        return a + b
    elif operation == "sub":
        return a - b
    elif operation == "multiply":
        return a * b
    elif operation == "divide":
        return a / b
    else:
        raise ValueError(f"unknown operation '{operation}'")


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    api_key = os.environ.get("WEATHER_API_KEY")
    response = requests.get(
        "https://api.openweathermap.org/data/2.5/weather",
        params={"q": city, "appid": api_key, "units": "metric"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()
    return f"{city}: {data['weather'][0]['description']}, {data['main']['temp']}°C"

@tool
def run_python_code(code: str) -> str:
    """Run Python code in an isolated, network-disabled sandbox and return its output."""
    return _run_python_code(code)


# if __name__ == "__main__":
#     print(execute("mathematic_operations", {"a": 5, "b": 3, "operation": "multiply"}))
#     print(execute("get_weather", {"city": "Chennai"}))
#     print(execute("nonexistent_tool", {}))