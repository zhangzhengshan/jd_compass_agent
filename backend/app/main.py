from __future__ import annotations

import json
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .config import settings
from .graph import graph
from .schemas import RunRequest, StreamEvent


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "app": settings.app_name}


def _event(**kwargs) -> bytes:
    return (json.dumps(StreamEvent(**kwargs).model_dump(), ensure_ascii=False) + "\n").encode("utf-8")


async def stream_run(payload: RunRequest) -> AsyncIterator[bytes]:
    state = payload.model_dump()
    yield _event(type="info", node="system", message="开始执行 JD Compass 三节点固定流程")

    step_names = {
        "parse_node": "需求解析 Agent",
        "route_node": "路由 Agent",
        "compose_node": "输出 Agent",
    }

    try:
        for chunk in graph.stream(state, stream_mode="updates"):
            if not isinstance(chunk, dict):
                continue

            for node_name, update in chunk.items():
                friendly = step_names.get(node_name, node_name)
                if isinstance(update, dict):
                    state.update(update)

                yield _event(
                    type="node_start",
                    node=node_name,
                    message=f"{friendly} 已触发",
                    data={
                        "update": update,
                        "route": (state.get("route_result", {}) or {}).get("route_label", ""),
                        "research_notes": state.get("research_notes", ""),
                    },
                )

                yield _event(
                    type="node_end",
                    node=node_name,
                    message=f"{friendly} 已完成",
                    data={
                        "update": update,
                        "route": (state.get("route_result", {}) or {}).get("route_label", ""),
                        "research_notes": state.get("research_notes", ""),
                    },
                )

        yield _event(
            type="final",
            node="compose_node",
            message="流程结束",
            data={
                "final_report": state.get("final_report", ""),
                "route": (state.get("route_result", {}) or {}).get("route_label", ""),
                "route_result": state.get("route_result", {}),
                "parse_result": state.get("parse_result", {}),
                "research_notes": state.get("research_notes", ""),
                "jd_skills": state.get("jd_keywords", []),
                "resume_skills": state.get("resume_keywords", []),
            },
        )
    except Exception as exc:  # pragma: no cover
        yield _event(type="error", node="system", message=str(exc), data={})


@app.post("/api/run", response_class=StreamingResponse)
async def run(payload: RunRequest):
    return StreamingResponse(stream_run(payload), media_type="application/x-ndjson; charset=utf-8")
