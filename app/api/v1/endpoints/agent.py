"""
api/v1/endpoints/agent.py
Agentic workflow: one request drives search -> pick -> fetch -> target -> train.

POST /api/v1/agent/start        — start a run (may pause for a user decision)
GET  /api/v1/agent/{id}         — current state
POST /api/v1/agent/{id}/answer  — answer the agent's question; it resumes
"""

import uuid

from fastapi import APIRouter, HTTPException
from langgraph.types import Command

from schemas.agent import AgentStartRequest, AgentAnswerRequest, AgentResponse
from agent.graph import get_graph

router = APIRouter(prefix="/agent", tags=["Agent"])


def _config(agent_id: str) -> dict:
    return {"configurable": {"thread_id": agent_id}}


def _response(agent_id: str, result: dict) -> AgentResponse:
    interrupts = result.get("__interrupt__")
    if interrupts:
        return AgentResponse(agent_id=agent_id, status="awaiting", question=interrupts[0].value)
    report = result.get("report") or {}
    return AgentResponse(agent_id=agent_id, status=report.get("status", "done"), report=report or None)


@router.post("/start", response_model=AgentResponse, summary="Start an agentic run")
def start(body: AgentStartRequest) -> AgentResponse:
    agent_id = str(uuid.uuid4())
    try:
        result = get_graph().invoke(
            {"query": body.query, "sources": body.sources}, _config(agent_id)
        )
    except RuntimeError as e:  # LLM not configured (needed for target resolution)
        raise HTTPException(status_code=503, detail=str(e))
    return _response(agent_id, result)


@router.post("/{agent_id}/answer", response_model=AgentResponse, summary="Answer + resume")
def answer(agent_id: str, body: AgentAnswerRequest) -> AgentResponse:
    result = get_graph().invoke(Command(resume=body.value), _config(agent_id))
    return _response(agent_id, result)


@router.get("/{agent_id}", response_model=AgentResponse, summary="Agent run state")
def status(agent_id: str) -> AgentResponse:
    snap = get_graph().get_state(_config(agent_id))
    if not snap or not snap.values:
        raise HTTPException(status_code=404, detail="Agent run not found.")
    for task in snap.tasks:
        if task.interrupts:
            return AgentResponse(agent_id=agent_id, status="awaiting", question=task.interrupts[0].value)
    report = snap.values.get("report") or {}
    return AgentResponse(agent_id=agent_id, status=report.get("status", "done"), report=report or None)
