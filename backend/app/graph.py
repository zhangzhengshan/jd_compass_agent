from __future__ import annotations

from typing import Literal
from typing_extensions import TypedDict

try:
    from langgraph.graph import END, START, StateGraph  # type: ignore
except Exception:  # pragma: no cover
    START = "__start__"
    END = "__end__"

    class _CompiledGraph:
        def __init__(self, nodes, edges, conditional_edges):
            self.nodes = nodes
            self.edges = edges
            self.conditional_edges = conditional_edges

        def stream(self, state, stream_mode="updates"):
            current = self.edges.get(START)
            while current and current != END:
                update = self.nodes[current](state)
                if isinstance(update, dict):
                    state.update(update)
                yield {current: update}

                if current in self.conditional_edges:
                    chooser, mapping = self.conditional_edges[current]
                    key = chooser(state)
                    current = mapping.get(key, key)
                else:
                    next_nodes = self.edges.get(current, [])
                    current = next_nodes[0] if next_nodes else END

    class StateGraph:  # type: ignore
        def __init__(self, state_type):
            self.state_type = state_type
            self.nodes = {}
            self.edges = {}
            self.conditional_edges = {}

        def add_node(self, name, fn):
            self.nodes[name] = fn

        def add_edge(self, start, end):
            self.edges[start] = end if start == START else [end]

        def add_conditional_edges(self, name, chooser, mapping):
            self.conditional_edges[name] = (chooser, mapping)

        def compile(self):
            return _CompiledGraph(self.nodes, self.edges, self.conditional_edges)

try:
    from langchain_core.messages import HumanMessage, SystemMessage  # type: ignore
except Exception:  # pragma: no cover
    class SystemMessage:  # type: ignore
        def __init__(self, content: str):
            self.content = content

    class HumanMessage:  # type: ignore
        def __init__(self, content: str):
            self.content = content

from .llm import get_deepseek_llm
from .prompts import COMPOSE_SYSTEM_PROMPT, PARSE_SYSTEM_PROMPT, ROUTE_SYSTEM_PROMPT
from .tools import build_research_notes, extract_skills, normalize_text, safe_json_loads, tokenize


class JDCompassState(TypedDict, total=False):
    jd: str
    resume: str
    company: str
    extra_requirements: str
    jd_clean: str
    resume_clean: str
    jd_keywords: list[str]
    resume_keywords: list[str]
    parse_result: dict
    route_result: dict
    research_notes: str
    final_report: str


def _fallback_parse(state: JDCompassState) -> dict:
    jd_clean = state.get("jd_clean", state["jd"])
    resume_clean = state.get("resume_clean", state["resume"])
    jd_keywords = tokenize(jd_clean, limit=12)
    resume_keywords = tokenize(resume_clean, limit=12)
    jd_skills = extract_skills(jd_clean)
    resume_skills = extract_skills(resume_clean)
    overlap = sorted(set(jd_skills) & set(resume_skills))
    missing = sorted(set(jd_skills) - set(resume_skills))
    return {
        "job_title": "未识别岗位",
        "jd_keywords": jd_keywords,
        "resume_keywords": resume_keywords,
        "must_have_skills": jd_skills,
        "resume_strengths": overlap[:5] if overlap else ["有基础的工程表达能力"],
        "resume_gaps": missing[:5] if missing else ["暂无明显缺口"],
        "candidate_summary": "当前使用本地兜底逻辑完成解析。",
    }


def parse_node(state: JDCompassState) -> JDCompassState:
    jd_clean = normalize_text(state["jd"])
    resume_clean = normalize_text(state["resume"])

    llm = get_deepseek_llm(temperature=0.1)
    user_prompt = (
        "请分析下面的信息，并严格按 JSON 输出。\n\n"
        f"【公司名】\n{state.get('company', '') or '未填写'}\n\n"
        f"【额外要求】\n{state.get('extra_requirements', '') or '无'}\n\n"
        f"【岗位 JD】\n{jd_clean}\n\n"
        f"【简历】\n{resume_clean}\n"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=PARSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        parse_result = safe_json_loads(response.content)
    except Exception:
        parse_result = _fallback_parse({
            "jd": state["jd"],
            "resume": state["resume"],
            "jd_clean": jd_clean,
            "resume_clean": resume_clean,
        })

    return {
        "jd_clean": jd_clean,
        "resume_clean": resume_clean,
        "jd_keywords": parse_result.get("jd_keywords", []),
        "resume_keywords": parse_result.get("resume_keywords", []),
        "parse_result": parse_result,
    }


def _fallback_route(state: JDCompassState) -> dict:
    parse_result = state.get("parse_result", {})

    jd_skills = set(parse_result.get("must_have_skills", []))
    resume_keywords = set(parse_result.get("resume_keywords", []))
    overlap_count = len(jd_skills & resume_keywords)

    if overlap_count >= 2:
        score = 85
        fit_level = "high"
        route_label = "direct"
    elif overlap_count == 1:
        score = 65
        fit_level = "medium"
        route_label = "direct"
    else:
        score = 35
        fit_level = "low"
        route_label = "revise"

    return {
        "fit_level": fit_level,
        "route_label": route_label,
        "score": score,
        "core_gap": "缺少关键岗位技能的直观证明",
        "next_action": "先补充简历中的关键项目描述",
        "routing_summary": "当前使用本地兜底逻辑完成路由判断。",
    }


def route_node(state: JDCompassState) -> JDCompassState:
    parse_result = state.get("parse_result", {})
    llm = get_deepseek_llm(temperature=0.1)
    user_prompt = (
        "请基于下面的解析结果输出路由判断 JSON。\n\n"
        f"【岗位解析结果】\n{parse_result}\n\n"
        f"【输入补充】\n公司名：{state.get('company', '') or '未填写'}\n"
        f"额外要求：{state.get('extra_requirements', '') or '无'}\n\n"
        "要求：\n"
        "- 严格只输出 JSON。\n"
        "- route_label 为 direct 时直接进入输出；为 revise 时先进入研究分支。\n"
    )

    try:
        response = llm.invoke([
            SystemMessage(content=ROUTE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        route_result = safe_json_loads(response.content)
    except Exception:
        route_result = _fallback_route(state)

    route_result.setdefault("fit_level", "medium")
    route_result.setdefault("route_label", "direct")
    route_result.setdefault("score", 60)
    route_result.setdefault("core_gap", "需要进一步优化简历表达")
    route_result.setdefault("next_action", "先把最相关的项目经历前置")
    route_result.setdefault("routing_summary", "路由判断已完成")

    if route_result.get("route_label") not in {"direct", "revise"}:
        route_result["route_label"] = "direct"

    return {"route_result": route_result}


def research_node(state: JDCompassState) -> JDCompassState:
    parse_result = state.get("parse_result", {})
    company = state.get("company", "") or "未填写"
    jd_keywords = parse_result.get("jd_keywords", [])

    research_notes = build_research_notes(
        company=company,
        extra_requirements=state.get("extra_requirements", ""),
        jd_keywords=jd_keywords,
    )

    return {"research_notes": research_notes}


def compose_node(state: JDCompassState) -> JDCompassState:
    llm = get_deepseek_llm(temperature=0.2)
    user_prompt = (
        "请根据以下信息生成最终 Markdown 报告。\n\n"
        f"【岗位 JD】\n{state.get('jd_clean', state['jd'])}\n\n"
        f"【简历】\n{state.get('resume_clean', state['resume'])}\n\n"
        f"【需求解析结果】\n{state.get('parse_result', {})}\n\n"
        f"【路由结果】\n{state.get('route_result', {})}\n\n"
        f"【研究补充】\n{state.get('research_notes', '')}\n"
    )
    research_notes = state.get("research_notes", "")

    try:
        response = llm.invoke([
            SystemMessage(content=COMPOSE_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ])
        final_report = response.content
    except Exception:
        parse_result = state.get("parse_result", {})
        route_result = state.get("route_result", {})
        research_notes = state.get("research_notes", "")
        final_report = (
            "# JD Compass 分析报告\n\n"
            "## 基本信息\n"
            f"- 公司：{state.get('company', '') or '未填写'}\n"
            f"- 匹配度：{route_result.get('score', 0)}/100\n\n"
            "## 岗位解读\n"
            f"- 关键词：{', '.join(parse_result.get('jd_keywords', [])) or '无'}\n\n"
            "## 匹配优势\n"
            f"- {', '.join(parse_result.get('resume_strengths', [])) or '暂无'}\n\n"
            "## 主要缺口\n"
            f"- {', '.join(parse_result.get('resume_gaps', [])) or '暂无'}\n\n"
            "## 简历修改建议\n"
            "- 把最相关的项目经历前置。\n"
            "- 用结果和数字替代空话。\n\n"
            "## 面试追问\n"
            "- 请讲一个你用过最熟的技术栈项目。\n\n"
            "## 研究补充\n"
            f"- {research_notes or '未进入研究分支'}\n\n"
            "## 最终建议\n"
            f"- {route_result.get('routing_summary', '已完成分析')}\n"
        )

    return {"final_report": final_report, "research_notes": research_notes}


builder = StateGraph(JDCompassState)
builder.add_node("parse_node", parse_node)
builder.add_node("route_node", route_node)
builder.add_node("research_node", research_node)
builder.add_node("compose_node", compose_node)

builder.add_edge(START, "parse_node")
builder.add_edge("parse_node", "route_node")
builder.add_conditional_edges(
    "route_node",
    lambda state: "research_node" if state.get("route_result", {}).get("route_label") == "revise" else "compose_node",
    {
        "research_node": "research_node",
        "compose_node": "compose_node",
    },
)
builder.add_edge("research_node", "compose_node")
builder.add_edge("compose_node", END)

graph = builder.compile()
