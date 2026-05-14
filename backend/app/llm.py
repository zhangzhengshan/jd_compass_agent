from __future__ import annotations

import ast
import json
import os
import re
from dataclasses import dataclass

from langchain_openai import ChatOpenAI

from .config import settings
from .tools import extract_skills, safe_json_loads, tokenize


@dataclass
class _FakeMessage:
    content: str


class _LocalFallbackLLM:
    def __init__(self, mode: str, temperature: float = 0.2):
        self.mode = mode
        self.temperature = temperature

    def invoke(self, messages):
        system = getattr(messages[0], "content", "") if messages else ""
        human = getattr(messages[-1], "content", "") if messages else ""

        if "需求解析 Agent" in system:
            return _FakeMessage(self._parse(human))
        if "路由 Agent" in system:
            return _FakeMessage(self._route(human))
        if "输出 Agent" in system:
            return _FakeMessage(self._compose(human))
        return _FakeMessage("{}")

    def _extract_block(self, text: str, start: str, end: str | None = None) -> str:
        pattern = re.escape(start) + r"\n(.*?)(?=\n【|\Z)"
        if end:
            pattern = re.escape(start) + r"\n(.*?)(?=\n" + re.escape(end) + r"|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _parse(self, human: str) -> str:
        company = self._extract_block(human, "【公司名】") or "未填写"
        extra = self._extract_block(human, "【额外要求】") or "无"
        jd = self._extract_block(human, "【岗位 JD】")
        resume = self._extract_block(human, "【简历】")

        jd_keywords = tokenize(jd, limit=12)
        resume_keywords = tokenize(resume, limit=12)
        jd_skills = extract_skills(jd)
        resume_skills = extract_skills(resume)
        overlap = sorted(set(jd_skills) & set(resume_skills))
        missing = sorted(set(jd_skills) - set(resume_skills))

        payload = {
            "job_title": jd_keywords[0] if jd_keywords else "未识别岗位",
            "jd_keywords": jd_keywords,
            "resume_keywords": resume_keywords,
            "must_have_skills": jd_skills,
            "resume_strengths": overlap[:5] if overlap else ["有基础的工程表达能力"],
            "resume_gaps": missing[:5] if missing else ["暂无明显缺口"],
            "candidate_summary": f"公司：{company}；补充要求：{extra}",
        }
        return json.dumps(payload, ensure_ascii=False)

    def _route(self, human: str) -> str:
        try:
            parsed = ast.literal_eval(self._extract_block(human, "【岗位解析结果】"))
        except Exception:
            parsed = {}

        jd_skills = set(parsed.get("must_have_skills", []))
        resume_keywords = set(parsed.get("resume_keywords", []))
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

        payload = {
            "fit_level": fit_level,
            "route_label": route_label,
            "score": score,
            "core_gap": "缺少关键岗位技能的直观证明" if route_label == "revise" else "整体匹配度较高",
            "next_action": "先补充简历中的关键项目描述" if route_label == "revise" else "直接输出结果",
            "routing_summary": "本地兜底路由判断已完成。",
        }
        return json.dumps(payload, ensure_ascii=False)

    def _compose(self, human: str) -> str:
        jd = self._extract_block(human, "【岗位 JD】")
        parse_text = self._extract_block(human, "【需求解析结果】")
        route_text = self._extract_block(human, "【路由结果】")
        research_text = self._extract_block(human, "【研究补充】")

        try:
            parse_result = ast.literal_eval(parse_text)
        except Exception:
            parse_result = {}

        try:
            route_result = ast.literal_eval(route_text)
        except Exception:
            route_result = {}

        report = (
            "# JD Compass 分析报告\n\n"
            "## 基本信息\n"
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
            f"{research_text or '未进入研究分支。'}\n\n"
            "## 最终建议\n"
            f"- {route_result.get('routing_summary', '已完成分析')}\n"
        )
        return report


def get_deepseek_llm(*, temperature: float = 0.2):
    api_key = settings.deepseek_api_key or os.getenv("DEEPSEEK_API_KEY", "")
    if not api_key:
        return _LocalFallbackLLM(mode="fallback", temperature=temperature)

    return ChatOpenAI(
        model=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
        api_key=api_key,
        temperature=temperature,
        timeout=60,
        max_retries=2,
    )
