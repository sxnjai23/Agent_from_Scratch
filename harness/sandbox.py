from __future__ import annotations

import os
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")  # Must be before FAISS import

import operator
import sys
import uuid
from pathlib import Path
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.vectorstores import FAISS
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_store
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.store.memory import InMemoryStore
from langchain_groq import ChatGroq


def demo_short_term_memory(llm: ChatGroq) -> None:
    """
    Short-term memory = this thread's message list, restored by the checkpointer.

    The same thread_id on each invoke reloads prior turns into state["messages"]
    so the model sees continuity without you manually merging history.
    """

    def chat(state: MessagesState) -> dict:
        # state["messages"] already contains ALL prior turns for this thread_id,
        # restored from the checkpoint. We pass the full list to the LLM.
        return {"messages": [llm.invoke(state["messages"])]}

    graph = StateGraph(MessagesState)
    graph.add_node("model", chat)
    graph.add_edge(START, "model")
    graph.add_edge("model", END)

    # Compile with a checkpointer. Without this, state is not saved between invokes.
    app = graph.compile(checkpointer=InMemorySaver())

    tid = "session-stm-demo"
    cfg: dict = {"configurable": {"thread_id": tid}}

    # First turn: store the codename.
    app.invoke({"messages": [HumanMessage("My codename for this session is Bluejay.")]}, cfg)

    # Second turn: only the new message is passed in.
    # The checkpointer reloads the first turn automatically.
    out = app.invoke({"messages": [HumanMessage("What codename did I give?")]}, cfg)
    print("[STM] Last reply:", out["messages"][-1].content)