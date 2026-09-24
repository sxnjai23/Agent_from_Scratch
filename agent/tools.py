"""
tools.py — turns plain Python functions into Groq tool schemas,
and safely executes tool calls coming back from the model.
"""

import inspect
import json
import os
import requests

TOOLS: dict[str, callable] = {}


def crct_annotation(annotation) -> str:
    """Map a Python type annotation to a JSON schema type string."""
    mapping = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
    }
    return mapping.get(annotation, "string")  # default to string if unknown/missing


def build_schema(func) -> dict:
    """Build a Groq-compatible tool schema from a function's signature + docstring."""
    sig = inspect.signature(func)
    properties = {}
    required = []

    for name, param in sig.parameters.items():
        annotation = param.annotation if param.annotation is not inspect.Parameter.empty else str
        properties[name] = {
            "type": crct_annotation(annotation),
            "description": name,  # simple placeholder; refine per-arg later if you want
        }
        if param.default is inspect.Parameter.empty:
            required.append(name)

    return {
        "type": "function",
        "function": {
            "name": func.__name__,
            "description": (func.__doc__ or "").strip(),
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def tool(func):
    """Decorator: attaches a schema to func and registers it. Does not wrap behavior."""
    func.schema = build_schema(func)
    TOOLS[func.__name__] = func
    return func


def get_all_schemas() -> list[dict]:
    return [func.schema for func in TOOLS.values()]


def execute(name: str, args: dict) -> str:
    """Run a tool call safely. Never raises — always returns a string."""
    if name not in TOOLS:
        return f"Error: unknown tool '{name}'. Available tools: {list(TOOLS.keys())}"

    func = TOOLS[name]
    try:
        result = func(**args)
    except TypeError as e:
        return f"Error: invalid arguments for '{name}': {e}"
    except Exception as e:
        return f"Error: '{name}' failed while running: {e}"

    if isinstance(result, (dict, list)):
        return json.dumps(result)
    return str(result)


# ---- tool definitions below ----

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
        if b == 0:
            raise ValueError("division by zero")
        return a / b
    else:
        raise ValueError(f"unknown operation '{operation}'")


WEATHER_API_KEY = "4cf17135f4ff861cc44674d95c17b517"
WEATHER_API_URL = "https://api.openweathermap.org/data/2.5/weather"


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    if not WEATHER_API_KEY:
        raise RuntimeError("WEATHER_API_KEY not set")

    response = requests.get(
        WEATHER_API_URL,
        params={"q": city, "appid": WEATHER_API_KEY, "units": "metric"},
        timeout=10,
    )
    response.raise_for_status()
    data = response.json()

    desc = data["weather"][0]["description"]
    temp = data["main"]["temp"]
    feels_like = data["main"]["feels_like"]

    return f"{city}: {desc}, {temp}°C (feels like {feels_like}°C)."

# print(execute("add", {"a": 5, "b": 3, "operation": "multiply"}))
# print(execute("add", {"a": 5, "b": 0, "operation": "divide"}))       # should error cleanly
# print(execute("get_weather", {"city": "Chennai"}))
# print(execute("get_weather", {"city": "asdkjasdkj"}))                # should error cleanly
print(execute("nonexistent_tool", {}))
print(json.dumps(get_all_schemas(), indent=2))