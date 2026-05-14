from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class RunRequest(BaseModel):
    jd: str = Field(..., min_length=1)
    resume: str = Field(..., min_length=1)
    company: Optional[str] = Field(default="")
    extra_requirements: Optional[str] = Field(default="")
    force_route: Optional[Literal["direct", "revise"]] = Field(
        default=None,
        description="用于测试或前端显式指定路由",
    )


class StreamEvent(BaseModel):
    type: Literal["node_start", "node_end", "final", "error", "info"]
    node: str = ""
    message: str = ""
    data: dict[str, Any] = Field(default_factory=dict)
