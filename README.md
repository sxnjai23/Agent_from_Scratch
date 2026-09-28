# Agent & Harness from Scratch

### Build an AI agent, then the harness that keeps it in line

**Build an AI agent in plain Python, then build the harness around it that makes it safe, observable and testable. No LangChain, no LangGraph, no magic. Just a loop, an LLM API, and a few small files you can read in an evening.**

![License: MIT](https://img.shields.io/badge/license-MIT-green) ![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)

**Built by [Sanjii](https://github.com/sxnjai23)** · [LinkedIn](https://in.linkedin.com/in/sanjai-jayabal)


[What is an agent?](#what-is-an-agent-what-is-a-harness) · [Run it](#run-it-in-5-minutes) · [The harness](#the-harness) · [Learn it step by step](#learn-it-step-by-step) · [The sandbox](#the-sandbox-in-depth) · [Evals](#part-7-testing-it-properly) · [Credits](#credits)

Most agent tutorials start with a framework. That gets you a demo fast, but you come away knowing the framework, not the agent. This repo does it the other way around: you build every piece yourself, see why it exists, and then the frameworks stop looking mysterious.

If you can read basic Python (functions, dicts, classes, `try/except`), you can follow this. You don't need any AI background.

---

## What is an agent? What is a harness?

You'll hear both words everywhere right now. Before any code, here's what they mean in plain terms.

### What is an AI agent?

A normal chatbot answers once: you ask, it replies, done. An **agent** is an AI model that can *do things* to get a job finished. It decides what to do next, uses tools (look something up, run code, call an API, read a file), checks what came back, and keeps going until the goal is met.

Every agent has three ingredients:

| Ingredient | What it is | In this repo |
|---|---|---|
| **A model** | the part that reasons and writes | an LLM hosted on Groq |
| **Tools** | actions the model can ask for | weather lookup, math, running Python |
| **A loop** | ask, act, look at the result, repeat until done | [`agent/loop.py`](agent/loop.py) |

And here's how that differs from a chatbot:

| | Chatbot | Agent |
|---|---|---|
| Steps | one question, one answer | as many steps as the goal needs |
| Actions | none, only text | calls tools |
| Who picks the next step | you | the model |
| What can go wrong | a bad answer | a bad answer, a failed tool, a loop that never ends, a wrong action |

Ask an agent *"What's the weather in Chennai, and what's that temperature times 3?"* and it works out for itself that this takes two steps.

### What is a harness?

> **Harness** = everything you build around the AI model that gives it capabilities, context, rules, state, execution mechanisms, and safeguards to accomplish a goal reliably.

On its own, the model only turns text into text. It can't run a tool, remember yesterday's chat, or stop itself from looping forever. The harness does all of that.

So yes, things like **tool definitions, function schemas, parsing, tool execution, prompts, context management, memory, validation, permissions, agent loops, error handling, and observability** can all be parts of the harness.

A simple way to hold it in your head:

> **Agent = model + harness.** The model brings the intelligence. The harness brings everything else.

| The model gives you | The harness gives you |
|---|---|
| language and reasoning | tools it can actually use |
| a guess at the next step | a loop that carries the steps out |
| answers from what's in its prompt | context, memory and saved state |
| | rules, permissions and safety limits |
| | error handling, retries and logs |

### What is harness engineering?

This is why "harness engineering" has become a useful term. You're not just trying to make the LLM smarter. **You're engineering the environment that lets the LLM perform useful work reliably.**

It's a real skill, because the same model can look brilliant or useless depending on what's around it. Harness engineers decide which tools the model sees, how its context is trimmed, what happens when a tool fails, what it's allowed to do, and how you measure whether any of it is working.

### Where each harness part lives in this repo

| Harness part | Where you'll find it |
|---|---|
| Tool definitions and function schemas | the `@tool` decorator in [`agent/tools.py`](agent/tools.py) |
| Parsing | [`agent/llm.py`](agent/llm.py) turns the model's reply into plain Python objects |
| Tool execution | `execute()` in [`agent/tools.py`](agent/tools.py) |
| Prompts | the system message in [`agent/loop.py`](agent/loop.py) |
| Context management | summarizing long chats in [`agent/context.py`](agent/context.py) |
| Memory and state | saved sessions in [`agent/context.py`](agent/context.py) |
| Validation and error handling | `execute()` catches bad arguments and crashing tools, and [`agent/llm.py`](agent/llm.py) retries failed API calls |
| Permissions | the tool allowlist, plus the Docker sandbox's limits in [`harness/sandbox.py`](harness/sandbox.py) |
| The agent loop | [`agent/loop.py`](agent/loop.py) |
| Observability | logs in [`harness/tracing.py`](harness/tracing.py), run stats, and the evals in [`evals/`](evals/) |

You'll build the agent first, then the harness around it. The full harness breakdown is in [The harness](#the-harness).

---

## What you'll end up with

An agent that answers questions by picking and running tools on its own. Roughly what a run looks like:

```
You:    What's the weather in Chennai, and what's that temperature times 3?

Agent:  calls get_weather("Chennai")               ->  clear sky, 31.2°C
        calls mathematic_operations(31.2 x 3)      ->  93.6
        "It's 31.2°C in Chennai. Times 3, that's 93.6."
```

It has three tools:

| Tool | What it does | Where it runs |
|---|---|---|
| `mathematic_operations` | add, subtract, multiply, divide | your Python process |
| `get_weather` | live weather from OpenWeatherMap | your Python process |
| `run_python_code` | runs a short script the model writes | a locked-down Docker container |

And the part most tutorials skip, the **harness** that makes an agent trustworthy:

- **Retries** when the API hiccups
- **Safe tool execution**, so a broken tool becomes a message, not a crash
- **A step limit**, so it can't loop forever
- **Log files**, so you can read exactly what happened
- **Memory** across conversations, plus **summarizing** long ones
- **A Docker sandbox**, so model-written code can't touch your machine
- **An eval suite**, so you can measure whether a change helped or hurt

> **Spotlight: the sandbox.** When the model writes code, that code never touches your machine. It runs inside a throwaway Docker container with no internet, a memory cap and a timer, and the container is destroyed right after. It's the piece that makes "let the AI run code" safe enough to try, and it has its own section: [how the sandbox works](#the-sandbox-in-depth).

---

## The idea in five minutes

Read this once. Everything else in the repo is this idea, built out.

**A language model only produces text.** It can't run code, call an API, or open a file. So how does an agent "use tools"?

1. You **describe** your tools to the model (name, what it does, what inputs it takes).
2. The model **asks** for one, in a structured message like "please call `get_weather` with `city = Chennai`". That's just text. Nothing has run yet.
3. **Your code** runs the real function.
4. You **send the result back** to the model.
5. The model either asks for another tool or gives its final answer.

That cycle is the agent loop:

```mermaid
flowchart TD
    A[User's question] --> B[Add it to the message list]
    B --> C[Call the model with messages + tool descriptions]
    C --> D{Did it ask for a tool?}
    D -- No --> E[That's the final answer]
    D -- Yes --> F[Your code runs the tool]
    F --> G[Add the result to the message list]
    G --> C
```

Two things to hold onto:

- **The model never runs anything. It can only ask.** Your code decides what actually runs. That's why there's a safe `execute()` function, and a sandbox for code the model writes.
- **The agent is the loop. The harness is everything around it** that keeps it reliable: retries, limits, logs, memory, sandbox, evals. Both are in this repo, and [the next section](#the-harness) shows how they fit together.

---

## The harness

A bare agent loop is easy to write and hard to trust. It works in the demo, then a tool throws an error, the API times out, the model loops forever, or a conversation grows until it breaks. **The harness is everything you build around the loop so those things don't matter.**

A rough way to picture it: the agent is the driver, and the harness is the seatbelt, the dashboard, the speed limiter and the crash test lab. The driver doesn't change. What changes is whether you'd let it out on the road.

### The harness at a glance

| Piece | What goes wrong without it | What it does here | Where |
|---|---|---|---|
| Retries with backoff | one rate limit or network blip ends the run | waits, then tries the API call again a few times | [`agent/llm.py`](agent/llm.py) |
| Safe tool execution | one failing tool crashes the whole agent | catches every error and returns it as text the model can react to | [`agent/tools.py`](agent/tools.py) |
| Tool allowlist | the model calls something you never meant to expose | only functions marked `@tool` can ever run | [`agent/tools.py`](agent/tools.py) |
| Step limit | a confused model loops forever and burns money | stops after `max_steps` and reports why | [`agent/loop.py`](agent/loop.py) |
| Run stats | you can't tell what a run cost | returns steps, tokens and status for every run | [`agent/loop.py`](agent/loop.py) |
| Tracing | "it didn't work" with no way to find out why | writes a readable log line for every action | [`harness/tracing.py`](harness/tracing.py) |
| Session memory | the agent forgets everything between runs | saves and reloads the conversation | [`agent/context.py`](agent/context.py) |
| Summarization | long chats get slow, costly, then impossible | replaces old messages with a short summary | [`agent/context.py`](agent/context.py) |
| Docker sandbox | model-written code runs on your machine | runs it in a locked-down, disposable container | [`harness/sandbox.py`](harness/sandbox.py) |
| Evals | you change something and have no idea if it helped | runs test tasks, grades them, prints a score | [`evals/`](evals/) |

Not every harness piece lives in the `harness/` folder. That folder holds tracing and the sandbox. The others sit next to the code they protect. "Harness" describes the job, not the folder.

### How the harness plugs into the agent

The harness doesn't wrap the agent from the outside. It hooks in at specific points in the loop. Here's every hook, in the order things happen:

```mermaid
flowchart TD
    subgraph BEFORE["Before the loop starts"]
        B1["Open the log file (tracing.py)"] --> B2["Load the saved session (context.py)"] --> B3["Summarize if it got long (context.py)"]
    end
    B3 --> L1
    subgraph LOOP["Every step of the loop"]
        L1{"Steps left? (max_steps in loop.py)"}
        L1 -- yes --> L2["Call the model, with retries (llm.py)"]
        L2 --> L3["Count the tokens (loop.py)"]
        L3 --> L4{"Did it ask for a tool?"}
        L4 -- yes --> L5["execute: allowlist and error catching (tools.py)"]
        L5 --> L6["Log the result and save the session"]
        L6 --> L1
        L5 -. "code tool only" .-> SB["Docker sandbox (sandbox.py)"]
    end
    L4 -- no --> E1
    L1 -- no --> E1
    E1["Return answer, steps, tokens and status"] --> E2["evals/run_evals.py scores many runs"]
```

The same thing as a table, so you can find any hook quickly:

| Hook point | What's attached there | Where to look |
|---|---|---|
| Start of `run_agent` | open the log, load the session, summarize if long | [`agent/loop.py`](agent/loop.py), [`agent/context.py`](agent/context.py) |
| Top of each step | the step limit check | [`agent/loop.py`](agent/loop.py) |
| Around the model call | retries and backoff, then token counting | [`agent/llm.py`](agent/llm.py), [`agent/loop.py`](agent/loop.py) |
| Around every tool call | allowlist lookup and error catching (`execute`) | [`agent/tools.py`](agent/tools.py) |
| Inside one specific tool | the Docker sandbox, used only by `run_python_code` | [`harness/sandbox.py`](harness/sandbox.py) |
| End of each step | log the action, save the session | [`agent/loop.py`](agent/loop.py) |
| End of the run | return a stats dict, close the log | [`agent/loop.py`](agent/loop.py) |
| Outside the agent | evals call `run_agent` like a user would and score the results | [`evals/run_evals.py`](evals/run_evals.py) |

### The rules that keep the integration clean

These are design choices worth copying in your own projects:

- **The loop stays small.** Each harness piece is one function call at a fixed point, not logic scattered through the loop. You can read `loop.py` top to bottom and follow the whole run.
- **One gatekeeper for tools.** Every tool call goes through `execute()`. Safety and error handling live in one place, not in each tool.
- **Tools raise, `execute()` catches.** A tool doesn't need to worry about being safe. If it fails, it raises, and the gatekeeper turns that into a message.
- **The sandbox is just an implementation detail of one tool.** The loop has no idea Docker exists. `run_python_code` is a normal `@tool` function that happens to call the sandbox. That's why you can swap Docker for something else without touching the loop.
- **Nothing outside `llm.py` knows about Groq.** Swap the provider by rewriting one file.
- **Evals sit outside the agent.** They only call `run_agent` and read what comes back, so the agent never depends on its own tests.
- **Failures become text.** Errors, timeouts and crashes are turned into messages instead of exceptions, so the model can often recover on its own.

### Adding your own harness piece

The question to ask first is: *where in the loop would this hook in?* The table above answers it. A few examples:

| You want to add | Where it hooks in |
|---|---|
| a **token budget** | top of each step, next to the step limit: stop if total tokens pass a limit |
| a **circuit breaker** | inside `execute()`: stop calling a tool that keeps failing |
| **human approval** for risky tools | in the loop, just before `execute()` runs |
| a **cost report** | end of the run, from the stats dict you already return |
| **structured logs** | in `tracing.py`: write JSON lines instead of plain text |
| a **new eval metric** | in `evals/run_evals.py`: extend the grader or the report |

### What's not built yet

To be upfront: the loop counts tokens but doesn't yet stop when a budget is exceeded, and there's no circuit breaker. Both are in [What to build next](#what-to-build-next), and both slot in exactly where the table above says.

---

## Where everything lives

Click any file to open it.

| Path | What it's for |
|---|---|
| [`agent/llm.py`](agent/llm.py) | Talks to the Groq API. The only file that knows Groq exists. |
| [`agent/tools.py`](agent/tools.py) | Turns Python functions into tools, runs them safely, and holds the three tools. |
| [`agent/loop.py`](agent/loop.py) | The agent loop itself. |
| [`agent/context.py`](agent/context.py) | Saves and loads conversations, and summarizes long ones. |
| [`harness/tracing.py`](harness/tracing.py) | Writes a readable log file for each run. |
| [`harness/sandbox.py`](harness/sandbox.py) | Runs code inside a disposable Docker container. |
| [`smoke_test.py`](smoke_test.py) | A quick "does it all work together?" script. |
| [`evals/tasks.json`](evals/tasks.json) | The test questions and expected answers. |
| [`evals/run_evals.py`](evals/run_evals.py) | Runs every test, grades it, prints a score. |

Each file has one job. The files only share simple data (dicts and small dataclasses), so you can swap the model provider, add a tool, or change the sandbox without rewriting everything else.

---

## Run it in 5 minutes

**You'll need**

- Python 3.10 or newer
- A free [Groq API key](https://console.groq.com)
- A free [OpenWeatherMap API key](https://openweathermap.org/api) (new keys can take a little while to activate)
- [Docker](https://www.docker.com/products/docker-desktop/), only for the code-running tool

**1. Get the code**

```bash
git clone https://github.com/sxnjai23/Agent_from_Scratch.git
cd Agent_from_Scratch
```

**2. Make a virtual environment and install the packages**

```bash
python -m venv .venv

# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# macOS / Linux
source .venv/bin/activate

pip install groq requests docker python-dotenv
```

**3. Add your keys**

Set them as environment variables in your terminal.

```bash
# Windows (PowerShell)
$env:GROQ_API_KEY = "your-groq-key"
$env:WEATHER_API_KEY = "your-openweather-key"

# macOS / Linux
export GROQ_API_KEY="your-groq-key"
export WEATHER_API_KEY="your-openweather-key"
```

Never paste keys into the code, and never commit them. If a key ever leaks (a commit, a screenshot, a chat), revoke it in the provider's console and make a new one.

**4. Check Docker works** (only needed for the code tool)

```bash
docker run --rm python:3.11-slim python -c "print(1+1)"
```

If that prints `2`, you're set.

**5. Talk to your agent**

```bash
python -m agent.loop
```

Type a question, or `exit` to quit. Try these:

- `What is 15 times 7?`
- `What's the weather in Chennai?`
- `Use code to find the 20th Fibonacci number`
- `Now divide that by 3` (right after one of the above, to test memory)

> **Always run commands from the repo's top folder, and use `python -m ...`.** Running a file by its path (like `python evals/run_evals.py`) breaks the imports and gives `No module named 'agent'`.

---

## Learn it step by step

Seven parts, about 10 to 20 minutes each. For each one: open the file, read it next to the explanation, run the "Try it" step, then move on. You can also rebuild the files yourself from scratch and compare with the repo version. That's the fastest way to really learn it.

### Part 1: Talking to the model
**File:** [`agent/llm.py`](agent/llm.py)

The Groq library returns deeply nested objects, and you'd rather not dig through those in every file. So this file is a translator. It's the only place that imports `groq`. Everything it sends back is a small, plain object: the text the model said, a list of tool requests (each with an id, a name, and arguments), and the token counts.

Two more things it does:

- **Retries.** API calls fail sometimes (rate limits, network blips). It waits a bit and tries again, a few times, before giving up.
- **Parses arguments.** The model sends tool arguments as a JSON string. This file turns them into a real dict once, so nobody else has to.

**Try it:** run `python -m agent.loop` and ask a plain question with no tool needed, like `What is the capital of France?`.

**Good to know:** the tool descriptions must be sent as a *list*. Passing a single dict gives a `400` error saying `'tools' : value must be an array`. Everyone hits this once.

### Part 2: Giving it tools
**File:** [`agent/tools.py`](agent/tools.py)

The model can't see your Python functions. It only sees a description: name, purpose, inputs. Writing that description by hand for every tool gets old fast, so this file builds it automatically from the function itself.

The trick is a **decorator**, the `@tool` line above each function. A decorator is a function that takes a function, does something with it, and hands it back. Here's what `@tool` does:

1. Reads the function's name, its docstring, and its parameters (with their type hints).
2. Builds the description the model needs.
3. Files the function in a dictionary called the registry.

Then it returns your function unchanged, so it's still a normal function you can test directly.

Things worth noticing in the file:

- **The docstring is what the model reads to decide when to use the tool.** Write it for the model. A vague docstring means wrong tool choices.
- **Type hints matter.** They're the only source of type information for the schema.
- **`execute()` is the gatekeeper.** Every tool call goes through it. It checks the tool exists, runs it, and turns *anything* that goes wrong into an error message the model can read and react to. It never crashes the loop.
- **Why a registry instead of running whatever name the model gives?** A registry is an allowlist. Only functions you marked with `@tool` can ever run. Looking names up in `globals()` would let the model call any function in scope.

**Try it:** ask for weather in a city that doesn't exist (`asdkjasdkj`). You should get a sensible reply, not a traceback. Then ask what 100 divided by 0 is.

**Exercise:** add your own tool. Write a function with type hints and a one-line docstring, put `@tool` on top, and ask the agent something that needs it. A "what time is it?" tool takes two minutes.

### Part 3: The agent loop
**File:** [`agent/loop.py`](agent/loop.py)

This is the whole agent, and it's short. The conversation lives in a list called `messages`, a growing transcript with four kinds of entries:

| Role | Who wrote it |
|---|---|
| `system` | your instructions to the model |
| `user` | the person's question |
| `assistant` | the model's reply, possibly including tool requests |
| `tool` | the result of a tool you ran |

Each round: ask the model, save its reply, and if it asked for tools, run them and save the results. Repeat until it answers without asking for anything.

Details that trip people up:

- **A tool call needs two messages.** First the assistant's request, then your tool result. Skip the first one and the next API call fails, because there's an answer with no question.
- **`tc.id` is a receipt number, not a memory address.** It's a string the API generates for each request, so results can be matched to requests when the model asks for several tools at once.
- **The tools are sent on every call.** The model doesn't remember them between requests. Look for `tools=schemas` in the loop.
- **`max_steps` is your safety net.** Without it, a confused model could loop forever and run up a bill.
- **Don't put `"tool_calls": null` in a message.** If there are no tool calls, leave the key out entirely. The API rejects `null`.
- **It returns a small dict** (answer, steps used, tokens used, status), not just a string, so the eval suite can measure runs.

**Follow one question all the way through.** Ask: *"What's the weather in Chennai, and what's that temperature times 3?"*

1. Your question goes into `messages`.
2. The model gets `messages` plus the tool descriptions. It replies with a request: `get_weather("Chennai")`.
3. Your code runs it and adds the result to `messages`.
4. The model sees the weather and asks for `mathematic_operations` with `31.2 x 3`.
5. Your code runs that, adds the result.
6. The model has what it needs and replies with plain text. No tool request, so the loop ends.

**Try it:** ask that exact question, then open the `.log` file for the run (see Part 4) and match each line to the steps above.

**Exercise:** temporarily print `messages` before every model call. Watching that list grow is the fastest way to understand agents.

### Part 4: Seeing what happened
**File:** [`harness/tracing.py`](harness/tracing.py)

Terminal output vanishes when you close the window. A log file doesn't. This one is deliberately simple: one timestamped line per event, like "used this tool with these arguments, got this back". It writes each line to disk immediately, so if a run crashes halfway, everything up to the crash is still there.

When something goes wrong, this is where you look first.

**Try it:** run a question, open its `.log` file, and check you can explain every line.

### Part 5: Memory
**File:** [`agent/context.py`](agent/context.py)

Out of the box, `messages` disappears when the function returns. Two ideas fix that.

**Saving and loading.** The conversation is written to a file named after a `session_id` (in `sessions/`). Same id next time means the agent picks up where you left off. A different id is a stranger. It saves after every step, so a crash doesn't lose progress.

**Summarizing.** Every request sends the *whole* transcript, so cost and size grow with every turn. When a conversation gets long, the old middle part is replaced with a short summary written by the model, while the most recent messages stay word for word.

One thing to be careful about when trimming: a tool result must always stay next to the assistant message that asked for it. Split them apart and the API rejects the request.

**Try it:** ask `What is 15 times 7?`, then `Now divide that by 3`. The agent should answer 35 because it can see the first exchange. Open the file in `sessions/` and read it.

**Good to know:** if you change how messages are saved and start getting strange `400` errors, delete the old files in `sessions/`. They may still hold the old, broken format.

### Part 6: Running code safely
**File:** [`harness/sandbox.py`](harness/sandbox.py)

`run_python_code` is different from the other tools. For `get_weather`, you wrote every line that runs. Here the model decides what code runs, and you can't predict it. It could delete files, read your keys, hit the network, or loop forever. Running that on your own machine is a real risk.

So it runs in a **disposable Docker container**:

- **The image** (`python:3.11-slim`) is a ready-made snapshot of a tiny Linux system with Python. Docker makes a fresh copy for every run.
- **Only the model's code runs inside.** None of your project exists in there: no `tools.py`, no keys, no `requests`. It's bare Python.
- **No network, and a memory cap.** The Linux kernel enforces these. It isn't trusting the code to behave.
- **The timeout is enforced from outside.** The container has no idea about your time limit. Your code waits, and if time runs out, it kills the container itself.
- **Output comes back as raw bytes.** Data crossing between your program and something else (a container, a socket, a file) travels as bytes, and you decode it into text. That's why you'll see `.decode("utf-8")` and a `.strip()` for the trailing newline that `print()` adds.
- **Cleanup always runs**, whether the code succeeded, crashed, or timed out.

**Try it:**

1. Ask: `Use code to find the 20th Fibonacci number`. You should get 6765.
2. Ask: `Use code to run an infinite loop: while True: pass`. It should be stopped after a few seconds.
3. Run `docker ps -a`. Nothing from your tests should be left behind. That's the real proof cleanup works.

**Want the full picture?** Skip ahead to [The sandbox in depth](#the-sandbox-in-depth) for a diagram, a step-by-step walkthrough, and a table of what happens when the model's code misbehaves.

**What this is and isn't:** it's a one-shot calculator. Every call starts fresh and is thrown away, so nothing persists between calls. A "coding assistant" that builds and tests projects would need a persistent workspace, file tools, and tighter controls. See [What to build next](#what-to-build-next).

### Part 7: Testing it properly
**Files:** [`smoke_test.py`](smoke_test.py), [`evals/tasks.json`](evals/tasks.json), [`evals/run_evals.py`](evals/run_evals.py)

Now stop eyeballing answers and measure them.

**Start with the smoke test.** It runs three questions, one per tool, and prints the answers.

```bash
python -m smoke_test
```

**Then break things on purpose.** The most useful tests are the ones built to fail. For each safety feature, trigger the failure it was made for:

| Break it by | You should see |
|---|---|
| asking `What is 100 divided by 0?` | an explanation, not a crash |
| asking for weather in `asdkjasdkj` | an error message, not a traceback |
| `Use code to run 1/0` | the sandbox reporting the crash |
| `Use code to run: while True: pass` | a timeout, and nothing left in `docker ps -a` |
| a task that needs 3 steps with `max_steps=1` | "Stopped: max steps reached" |
| a follow-up using "that" in the same session | the earlier result being used |
| turning off Wi-Fi and asking for weather | an error message, not a crash |

Every crash you find here is a missing piece of the harness.

**Then run the eval suite.** An eval is three things repeated: a task, the answer you expect, and a check that compares them.

```bash
python -m evals.run_evals
```

Roughly what you'll see:

```
PASS  math-1     steps=2  tokens=640   status=done
PASS  code-1     steps=2  tokens=910   status=done
FAIL  fail-1     steps=2  tokens=700   status=done

Score: 8/9 passed, 6420 tokens total
```

Design choices in the runner:

- **Every task gets a fresh session.** Otherwise tasks would remember each other and skew the results.
- **One crashing task doesn't stop the run.** It's recorded as a failure and the rest continue.
- **The grader is simple on purpose:** does the expected text appear in the answer? It will sometimes be too strict. When a task fails, open its log before blaming the agent. It's always one of three things: the grader was too strict, the agent chose badly, or you found a real bug.
- **It pauses between tasks** to stay under free-tier rate limits.

---

## The sandbox in depth

This is the most interesting part of the harness, so it gets its own section. Read [`harness/sandbox.py`](harness/sandbox.py) alongside it.

### Why it exists

Every other tool in this repo runs code *you* wrote. You know exactly what `get_weather` does. `run_python_code` is different: it runs code the model wrote a few seconds ago, and you have no idea what it says until it arrives. It might be a tidy loop. It might be a bug that fills your disk, a script that reads your API keys, or something that hangs forever.

You can't fix that by trusting the model more. You fix it by making sure the code runs somewhere it can't do any damage.

### The picture

Think of a disposable glass room. You slide a note (the code) through a slot, watch from outside, collect whatever gets printed, and then demolish the room. Nothing inside can reach your house. The next note gets a brand-new room.

```mermaid
sequenceDiagram
    participant M as Model
    participant A as Your agent (execute)
    participant S as sandbox.py
    participant D as Docker
    participant C as Container
    M->>A: asks for run_python_code(code)
    A->>S: run_python_code(code)
    S->>D: create a container (no network, memory capped)
    D->>C: start it: python -c "code"
    S->>D: wait, but only up to the timeout
    C-->>D: prints output, exits
    S->>D: read the output (raw bytes)
    S->>D: remove the container
    S-->>A: plain text: the output, or an error message
    A-->>M: tool result
```

The model only ever produces the text of the code. Everything after that arrow is your program's decision.

### What happens, step by step

1. **The model asks.** It sends `run_python_code` with a `code` argument. That's just a string. Nothing has run.
2. **`execute()` finds the tool** in the registry and calls the sandbox function.
3. **Docker builds a fresh container** from the `python:3.11-slim` image (a tiny Linux system with Python), with the network switched off and a memory limit set.
4. **The only thing that runs inside** is `python -c "<the model's code>"`. Your program isn't blocked; it starts the container in the background and watches the clock.
5. **Finished in time?** Your program reads what the code printed and checks the exit code. `0` means success. Anything else means the script itself crashed, and that becomes an error message.
6. **Too slow?** Your program kills the container itself. The container has no idea a timer exists, so the outside has to enforce it.
7. **Cleanup always happens.** The container is removed whether the code worked, crashed or timed out.
8. **The result goes back as text**, and the model reads it and carries on.

### What's inside the box, and what isn't

| Inside the container | Not inside the container |
|---|---|
| Python 3.11 and its standard library | your project files (`tools.py`, `loop.py`, ...) |
| the one script the model wrote | your API keys and environment variables |
| a small memory allowance | your other files and folders |
| its own empty, temporary filesystem | the internet and your local network |
| | packages like `requests` |
| | your agent's conversation |

### The guardrails

| Guardrail | What it protects you from | How it works |
|---|---|---|
| Fresh container every call | leftovers from one run affecting the next | the container is removed after each call |
| No network | code sending data out or downloading things | networking is disabled when the container is created |
| Memory cap | a script eating all your RAM | the Linux kernel kills anything over the limit |
| Timeout | infinite loops and hangs | your program waits with a deadline, then kills the container |
| Cleanup in `finally` | dead containers piling up | cleanup runs on success, crash and timeout alike |
| Errors become text | a bad script crashing your agent | crashes and timeouts turn into messages the model can read |

The memory limit and the timeout are defaults in the file. Both are easy to change.

### What happens when the model's code misbehaves

| The code tries to... | What actually happens |
|---|---|
| loop forever | the timeout fires, the container is killed, the model gets a "took too long" message |
| divide by zero or hit any other error | the script crashes, the exit code is non-zero, the model gets an error message with the output |
| read your `.env` or your project files | they don't exist in there, so it fails |
| print environment variables | it sees the container's own, and your keys aren't among them |
| call a web API | there's no network, so it fails |
| `import requests` | `ModuleNotFoundError`, since only the standard library is installed |
| delete files | it can only touch the throwaway container's own files, which are destroyed anyway |
| use huge amounts of memory | the kernel kills it once it passes the limit |

### Why the output comes back as bytes

Anything that crosses a boundary between your program and something else (a container, a network socket, a file) travels as raw bytes. The Docker library gives you exactly that, so the code decodes it into text (UTF-8) and strips the trailing newline that `print()` adds. If you've ever wondered why a `b'2\n'` shows up, that's why.

### Try it yourself

1. Ask: `Use code to find the 20th Fibonacci number`. You should get 6765.
2. **Watch the box appear.** Keep a second terminal open and run `docker ps` a few times while the agent works on: `Use code to run: import time; time.sleep(4); print("done")`. You'll see a container show up and then vanish.
3. Trigger the timeout: `Use code to run an infinite loop: while True: pass`.
4. Trigger a crash: `Use code to run 1/0`.
5. **Try to peek out.** Ask: `Use code to print all environment variables`. You'll see the container's environment, not yours.
6. Run `docker ps -a`. It should be empty of your test containers. That's the proof cleanup works.

### Honest limits

- **It's a one-shot tool.** Every call starts from nothing, and nothing survives. The model can't save a file and use it in the next call, and it can't install packages.
- **Only memory and time are capped.** There's no CPU cap, no limit on how many processes it can start, and the filesystem isn't read-only. The timeout is what stops a script that spins.
- **Docker isn't a perfect wall.** Containers share the host's kernel. That's plenty for a learning project running your own agent, but it's not what you'd rely on for hostile code at scale.
- **Docker has to be running.** If it isn't, the tool returns an error message, and everything else in the agent keeps working.

### How real agent platforms go further

The idea is the same, with more layers:

- **Warm pools:** containers are started ahead of time so there's no wait
- **MicroVMs and gVisor:** stronger isolation than a plain container (Firecracker is a well-known example)
- **Syscall filtering (seccomp):** blocking dangerous system calls at a lower level
- **Files in and out:** so the code can produce a chart or a CSV and hand it back
- **Live resource watching:** killing runaway code early instead of waiting for the full timeout
- **Never reusing a sandbox** across two different runs of untrusted code

### Ideas to extend it

- Add a CPU limit, a process limit and a read-only filesystem
- Mount a workspace folder so the agent can write files and iterate, which is the step from "calculator" to "coding assistant"
- Let it use a short list of approved packages
- Start containers in advance so calls feel instant

---

## Experiments to try

This is why the eval suite exists. **Change exactly one thing per run**, re-run the same tasks, and write down the score.

| Experiment | What to change | What you'll learn |
|---|---|---|
| Different models | the model name in the runner | which model picks tools most reliably, and what it costs in tokens |
| Vague tool description | rewrite one docstring badly | how much descriptions drive tool choice |
| No sandbox | remove `run_python_code` | how many tasks truly need it |
| System prompt | one line vs. a detailed prompt | how much instructions matter |
| No safety net | remove the `try/except` in `execute()` | how fast things break without it |

Keep your own results table:

| Run | Model | Change | Score | Avg steps | Total tokens |
|---|---|---|---|---|---|
| 1 | | baseline | | | |

---

## Stuck?

| What you see | Likely cause and fix |
|---|---|
| `No module named 'agent'` | You ran a file by path. From the repo's top folder, use `python -m ...`. |
| `KeyError: 'GROQ_API_KEY'` | The key isn't set in this terminal. Set it again (see the setup step). |
| `400 ... 'tools' : value must be an array` | Tools must be a list, even with one tool. |
| `400 ... tool_calls : Value is not nullable` | A message has `"tool_calls": null`. Leave the key out, then delete the old files in `sessions/`. |
| A `400` right after a tool ran | A tool result lost its matching assistant message. |
| Weather gives a 401 | New OpenWeatherMap keys take a while to activate. Also check the key. |
| `Could not start the sandbox` | Docker isn't running. Start Docker Desktop and re-check with the `docker run` command. |
| `429` / rate limit errors | Free tiers have limits. Add a longer pause in the eval runner, or use fewer tasks. |
| Leftover containers | Run `docker ps -a`, then `docker rm -f <id>`. |

---

## Staying safe

- **Keys live in environment variables (or a `.env` file that's in `.gitignore`), never in code.**
- **Never run model-written code on your own machine.** Sandbox it.
- **Use allowlists.** The registry only runs registered tools. Don't run model output through `eval()`, `exec()` or `globals()`.
- **Think before adding tools.** A file tool should be locked to one folder (and block `../` tricks). A shell tool can be steered by text the model reads, which is called prompt injection.
- **Retries can repeat side effects.** Retrying a read is harmless. Retrying something that writes, sends, or pays can do it twice.

---

## Words you'll meet

| Term | Meaning |
|---|---|
| **Agent** | a model in a loop that can choose and use tools to reach a goal |
| **Harness** | everything around the agent that keeps it reliable: retries, limits, logs, memory, sandbox, evals |
| **Tool calling** | the model asks for a named function with arguments; your code runs it |
| **Schema** | the description of a tool (name, purpose, inputs) that the model reads |
| **Decorator** | a function that takes a function and returns a function, like `@tool` |
| **Registry** | a dictionary of tool names to functions |
| **Session** | a saved conversation, identified by a `session_id` |
| **Token** | a chunk of text; model cost and limits are counted in tokens |
| **Context window** | the most text a model can take in one request |
| **Sandbox** | an isolated place to run code you don't trust |
| **Container** | a lightweight isolated process that acts like its own small computer |
| **Image** | the ready-made snapshot a container starts from (here, `python:3.11-slim`) |
| **Eval** | an automated test: tasks, expected answers, and a grader |

---

## What to build next

**Small upgrades**

- A **token budget** that stops a run when it gets too expensive
- Smarter retries: only on rate limits, server errors and connection drops, and honoring `retry-after`
- A description for each tool argument, not just the tool
- A **circuit breaker** that stops calling a tool that keeps failing
- Structured logs (JSON lines) and a small replay script
- More tools: web search, a folder-restricted file reader/writer

**Bigger projects**

- A **persistent sandbox workspace** so the agent can write files and iterate, which turns the calculator into a coding assistant
- **Port it to LangGraph or Google ADK** and compare. You'll see exactly what a framework adds and what it hides.
- Human approval before risky tools run
- Streaming and parallel tool calls

**Good code to read after you've built your own**

- [SWE-agent/mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent): a tiny agent with a clean split between agent, model and environment
- [sergenes/mini_agent](https://github.com/sergenes/mini_agent): a framework-free agent with a reliability layer
- [pguso/agents-from-scratch](https://github.com/pguso/agents-from-scratch): a lesson-by-lesson build with evals and telemetry

---

## Credits

**Built by [Sanjii](https://github.com/sxnjai23)** · [LinkedIn](https://in.linkedin.com/in/sanjai-jayabal)

**Built with:** Python, the [Groq](https://groq.com) API, the [OpenWeatherMap](https://openweathermap.org) API and [Docker](https://www.docker.com).

**Inspired by:** the small agent codebases listed under [What to build next](#what-to-build-next): mini-swe-agent, mini_agent and agents-from-scratch. They're worth reading once you've built your own.

## Contributing

Found a bug, a confusing explanation, or a step that didn't work on your machine? Please [open an issue](https://github.com/sxnjai23/Agent_from_Scratch/issues). Fixes to the tutorial are as welcome as fixes to the code. If this helped you, a star on the repo means a lot.

## License

[MIT](LICENSE). Use it, learn from it, build on it.
