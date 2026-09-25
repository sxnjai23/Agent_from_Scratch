"""
    llm.py — talks to Groq. Nothing else in the project should import `groq`
    directly; everything else just calls LLMClient.call(...) and gets back
    plain Python objects.
"""

import json
import os
import time
from dataclasses import dataclass, field
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

"""
    Validation - Structuring the Tool call Retrurns and LLM 
    Response if its not following
    the STRUCTURE it simply through a error. 

"""
@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]
    usage: dict = field(default_factory=dict)


"""
    This class defines the entire LLM Operations and Normalizing the Response.
    
       1._init__ (constructor) where we simply pass the info 
    like model,and llm initilization.

       2.  call the LLM and pass info such as model , messages-> user and system. 
    ,max_tokens. if tools available kwargs will append the tool in the dict 
    and it sent to the model. as unpacked. where we also defining the 
    max_retries for the agent .

        3. _normalize TOOL CALL -> list where its store what tool called 
    (function) what arguments its parsed. id , name , Arguments. and also get the 
    token usage from the model.

"""
GROQ_API = os.environ["GROQ_API_KEY"]


class LLMClient:
    def __init__(self):
        self.model = "openai/gpt-oss-20b"
        self.client = Groq(api_key = GROQ_API)

    def call(self, messages: list[dict], tools: list[dict] | None = None , max_retries = 3) -> LLMResponse:
        for attempt in range(max_retries):
            try:
                kwargs = {"model": self.model, "messages": messages, "max_tokens": 256}
                if tools:
                    kwargs["tools"] = tools
                    kwargs["tool_choice"] = "auto"

                resp = self.client.chat.completions.create(**kwargs)
                return self._normalize(resp)

            except Exception as e:
                if attempt == 2:  # last attempt failed, give up
                    raise
                time.sleep(2 ** attempt)  # wait 1s, then 2s, before retrying

    def _normalize(self, resp) -> LLMResponse:
        msg = resp.choices[0].message

        tool_calls = []
        for tc in (msg.tool_calls or []):
            args = json.loads(tc.function.arguments)
            tool_calls.append(ToolCall(id=tc.id, name=tc.function.name, arguments=args))

        usage = {}
        if resp.usage:
            usage = {
                "input_tokens": resp.usage.prompt_tokens,
                "output_tokens": resp.usage.completion_tokens,
            }

        return LLMResponse(content=msg.content, tool_calls=tool_calls, usage=usage)