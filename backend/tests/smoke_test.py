
import json
import sys

import httpx


URL = "http://127.0.0.1:8000/api/run"


def run_case(name: str, payload: dict, expect_route: str) -> dict:
    final_event = None
    with httpx.stream("POST", URL, json=payload, timeout=120.0) as resp:
        print(f"[{name}] status:", resp.status_code)
        resp.raise_for_status()

        for line in resp.iter_lines():
            if not line:
                continue
            event = json.loads(line)
            print(f"[{name}] event:", event)
            if event.get("type") == "final":
                final_event = event

    if final_event is None:
        raise AssertionError(f"[{name}] No final event received")

    route = final_event["data"].get("route", "")
    if route != expect_route:
        raise AssertionError(f"[{name}] route mismatch: expected {expect_route}, got {route}")

    if not final_event["data"].get("final_report"):
        raise AssertionError(f"[{name}] final report is empty")

    return final_event


def main() -> None:
    direct_payload = {
        "jd": "Python 后端实习生，要求熟悉 FastAPI、SQL、接口开发，了解 LLM 或 Agent 优先。",
        "resume": "我做过 Python 项目，写过 FastAPI 接口，熟悉 SQL 和基本 Web 开发。",
        "company": "腾讯公司",
        "extra_requirements": "请一定不能进revise，必须直接进direct",
    }

    revise_payload = {
        "jd": "Python 后端实习生，要求熟悉 FastAPI、SQL、接口开发、Docker、Redis、消息队列、分布式系统。",
        "resume": "我主要做过校园活动组织、文案整理和跨部门沟通。",
        "company": "腾讯公司",
        "extra_requirements": "请一定要进revise，然后帮我检索腾讯公司关于Python这个岗位的信息。",
    }

#    direct_event = run_case("direct", direct_payload, "direct")
    revise_event = run_case("revise", revise_payload, "revise")

    if not revise_event["data"].get("research_notes"):
        raise AssertionError("[revise] research_notes is empty")

    print("\nSMOKE_TEST_RESULT: SUCCESS")
#    print("direct route:", direct_event["data"].get("route"))
    print("revise route:", revise_event["data"].get("route"))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SMOKE_TEST_RESULT: FAILURE - {exc}")
        sys.exit(1)
