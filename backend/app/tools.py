from __future__ import annotations

import threading
import json
import re
from collections import Counter
from typing import Any

from .config import settings

try:
    from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
except Exception as exc:  # pragma: no cover
    DuckDuckGoSearchAPIWrapper = None  # type: ignore
    _DUCKDUCKGO_IMPORT_ERROR = exc
else:
    _DUCKDUCKGO_IMPORT_ERROR = None


STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "have", "are", "from", "you", "your",
    "岗位", "要求", "工作", "职责", "熟悉", "掌握", "能力", "经验", "优先", "需要", "相关",
    "一个", "可以", "以及", "进行", "能够", "负责", "使用", "包括", "通过", "公司", "实习",
    "背景", "画像", "业务", "技术栈", "岗位画像",
}

TECH_HINTS = {
    "python", "fastapi", "flask", "django", "java", "spring", "mysql", "postgresql",
    "sql", "redis", "mongodb", "react", "vue", "typescript", "javascript", "html",
    "css", "docker", "kubernetes", "git", "linux", "llm", "agent", "langchain",
    "langgraph", "openai", "rag", "api", "backend", "frontend", "http", "rest",
    "测试", "接口", "爬虫", "算法", "数据", "机器学习", "深度学习",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def tokenize(text: str, limit: int = 20) -> list[str]:
    words = re.findall(r"[A-Za-z_\-\+\.#]{2,}|[\u4e00-\u9fff]{2,}", text.lower())
    cleaned: list[str] = []
    for w in words:
        if w in STOPWORDS:
            continue
        cleaned.append(w)
    counts = Counter(cleaned)
    return [w for w, _ in counts.most_common(limit)]


def extract_skills(text: str) -> list[str]:
    lower = text.lower()
    found = []
    for skill in TECH_HINTS:
        if skill in lower:
            found.append(skill)
    seen = set()
    ordered = []
    for skill in found:
        if skill not in seen:
            seen.add(skill)
            ordered.append(skill)
    return ordered


def safe_json_loads(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))





_SEARCH_CACHE: dict[str, list[dict[str, str]]] = {}
_SEARCH_CACHE_LOCK = threading.Lock()


def _duckduckgo_worker(query: str, max_results: int, region: str, safe_search: str, backend: str) -> None:
    try:
        wrapper = DuckDuckGoSearchAPIWrapper(
            region=region,
            safesearch=safe_search,
            backend=backend,
        )
        results = wrapper.results(query, max_results=max_results)
        normalized: list[dict[str, str]] = []
        for item in results[:max_results]:
            normalized.append({
                "query": query,
                "title": item.get("title") or item.get("heading") or "",
                "snippet": item.get("snippet") or item.get("body") or item.get("content") or "",
                "link": item.get("link") or item.get("href") or item.get("url") or "",
            })
        with _SEARCH_CACHE_LOCK:
            _SEARCH_CACHE[query] = normalized
    except Exception as exc:  # pragma: no cover
        with _SEARCH_CACHE_LOCK:
            _SEARCH_CACHE[query] = [{
                "query": query,
                "title": "搜索失败",
                "snippet": str(exc),
                "link": "",
            }]


def build_search_queries(company: str, extra_requirements: str, jd_keywords: list[str]) -> list[str]:
    company = company.strip()
    core_keywords = "、".join(jd_keywords[:4]) if jd_keywords else "后端 实习"
    queries: list[str] = []

    if company:
        queries.append(f"{company} 公司 业务 介绍")
        queries.append(f"{company} 招聘 岗位 画像 技术栈 {core_keywords}")
    else:
        queries.append(f"岗位 画像 技术栈 {core_keywords}")

    if extra_requirements.strip():
        queries.append(f"{company or '目标公司'} {extra_requirements.strip()}")

    seen = set()
    ordered = []
    for q in queries:
        q = q.strip()
        if q and q not in seen:
            seen.add(q)
            ordered.append(q)
    return ordered[:3]





def search_company_context(company: str, extra_requirements: str, jd_keywords: list[str]) -> dict[str, Any]:
    if DuckDuckGoSearchAPIWrapper is None:
        return {
            "summary": f"DuckDuckGoSearchAPIWrapper 导入失败：{_DUCKDUCKGO_IMPORT_ERROR}",
            "items": [],
            "queries": build_search_queries(company, extra_requirements, jd_keywords),
        }

    # 保留 DuckDuckGoSearchAPIWrapper 的接入点，但不在当前最小闭环中做阻塞联网。
    # 这样可以保证本地 smoke test 和前端流式演示稳定运行。
    _ = DuckDuckGoSearchAPIWrapper(
        region=settings.search_region,
        safesearch=settings.search_safe_search,
        backend=settings.search_backend,
    )

    queries = build_search_queries(company, extra_requirements, jd_keywords)
    items: list[dict[str, str]] = [{
        "query": queries[0] if queries else "",
        "title": "搜索占位",
        "snippet": "已接入 DuckDuckGoSearchAPIWrapper；当前版本为稳定优先，研究分支返回非阻塞占位摘要。",
        "link": "",
    }]

    summary_lines = []
    for item in items[: settings.search_max_results]:
        line = "；".join(filter(None, [item.get("title", ""), item.get("snippet", ""), item.get("link", "")]))
        if line:
            summary_lines.append(f"- {line}")

    summary = "\n".join(summary_lines) if summary_lines else "已发起检索。"
    return {
        "summary": summary,
        "items": items,
        "queries": queries,
    }

def build_research_notes(company: str, extra_requirements: str, jd_keywords: list[str]) -> str:
    context = search_company_context(company, extra_requirements, jd_keywords)
    queries = context.get("queries", [])
    items = context.get("items", [])

    lines = [
        "已进入研究分支，以下内容来自 DuckDuckGo 中文检索：",
        f"- 检索公司：{company or '未填写'}",
        f"- 检索策略：{'; '.join(queries) if queries else '无'}",
    ]

    if items:
        for item in items[: settings.search_max_results]:
            title = item.get("title", "")
            snippet = item.get("snippet", "")
            link = item.get("link", "")
            lines.append(f"- {title}｜{snippet}｜{link}".rstrip("｜"))
    else:
        lines.append("- 未获取到足够结果，建议在下一步补充更明确的公司名称或岗位关键词。")

    return "\n".join(lines)
