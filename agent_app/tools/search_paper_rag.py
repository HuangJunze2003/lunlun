from typing import Any

import requests
from agentscope.tool import Toolkit, ToolResponse


ACADEMIC_RETRIEVER_SEARCH_URL = "http://192.168.3.15:8765/search"
ACADEMIC_RETRIEVER_TIMEOUT_SECONDS = 15


SECTION_ALIASES = {
    "abstract": "ABSTRACT",
    "摘要": "ABSTRACT",
    "intro": "INTRODUCTION",
    "introduction": "INTRODUCTION",
    "引言": "INTRODUCTION",
    "背景": "INTRODUCTION",
    "motivation": "INTRODUCTION",
    "problem": "INTRODUCTION",
    "overview": "OVERVIEW",
    "概览": "OVERVIEW",
    "background": "BACKGROUND",
    "preliminary": "BACKGROUND",
    "design": "DESIGN",
    "method": "DESIGN",
    "methods": "DESIGN",
    "approach": "DESIGN",
    "方案设计": "DESIGN",
    "设计": "DESIGN",
    "implementation": "IMPLEMENTATION",
    "实现": "IMPLEMENTATION",
    "evaluation": "EVALUATION",
    "eval": "EVALUATION",
    "experiment": "EVALUATION",
    "experiments": "EVALUATION",
    "实验": "EVALUATION",
    "评估": "EVALUATION",
    "results": "EVALUATION",
    "discussion": "DISCUSSION",
    "分析": "DISCUSSION",
    "related work": "RELATED_WORK",
    "related_work": "RELATED_WORK",
    "relatedwork": "RELATED_WORK",
    "相关工作": "RELATED_WORK",
    "conclusion": "CONCLUSION",
    "总结": "CONCLUSION",
    "结论": "CONCLUSION",
}


def _text_response(text: str, metadata: dict[str, Any] | None = None) -> ToolResponse:
    return ToolResponse(
        content=[{"type": "text", "text": text}],
        metadata=metadata or {},
    )


def _truncate(text: str, limit: int = 280) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3] + "..."


def _normalize_venue(venue: str) -> str:
    normalized = (venue or "").strip()
    return normalized.upper() if normalized else "NSDI"


def _normalize_section(section: str) -> str:
    raw = (section or "").strip()
    if not raw:
        return "INTRODUCTION"

    canonical = SECTION_ALIASES.get(raw.lower())
    if canonical:
        return canonical

    return raw.upper().replace(" ", "_")


def _normalize_n_results(n_results: int) -> int:
    try:
        value = int(n_results)
    except (TypeError, ValueError):
        value = 3

    return max(1, min(value, 5))


def _format_similarity(similarity: Any) -> str:
    if isinstance(similarity, (int, float)):
        return f"{similarity:.3f}"
    return "unknown"


def _build_result_summary(index: int, item: dict[str, Any]) -> str:
    metadata = item.get("metadata") or {}
    title = metadata.get("title") or "Unknown Title"
    venue = metadata.get("venue") or "Unknown Venue"
    year = metadata.get("year") or "Unknown Year"
    section_head = metadata.get("section_head") or metadata.get("section_canonical") or ""
    text = _truncate(item.get("text") or "", limit=320)

    header = (
        f"{index}. {title} | {venue} {year} | "
        f"similarity={_format_similarity(item.get('similarity'))}"
    )
    if section_head:
        header += f" | section={section_head}"

    lines = [header, f"主片段：{text}"]

    adjacent_chunks = item.get("adjacent_chunks") or []
    adjacent_texts: list[str] = []
    for adjacent in adjacent_chunks[:2]:
        snippet = _truncate(adjacent.get("text") or "", limit=180)
        if snippet:
            adjacent_texts.append(snippet)
    if adjacent_texts:
        lines.append(f"相邻上下文：{' | '.join(adjacent_texts)}")

    return "\n".join(lines)


def _build_result_metadata(item: dict[str, Any]) -> dict[str, Any]:
    metadata = item.get("metadata") or {}
    return {
        "chunk_id": item.get("chunk_id"),
        "similarity": item.get("similarity"),
        "title": metadata.get("title"),
        "venue": metadata.get("venue"),
        "year": metadata.get("year"),
        "section_canonical": metadata.get("section_canonical"),
        "section_head": metadata.get("section_head"),
        "paper_id": metadata.get("paper_id"),
        "dblp_key": metadata.get("dblp_key"),
        "tei_path": metadata.get("tei_path"),
    }


def search_paper_rag(
    query: str,
    venue: str = "NSDI",
    section: str = "INTRODUCTION",
    n_results: int = 3,
    endpoint: str = ACADEMIC_RETRIEVER_SEARCH_URL,
    api_key: str | None = None,
    timeout_seconds: int = ACADEMIC_RETRIEVER_TIMEOUT_SECONDS,
) -> ToolResponse:
    """
    检索顶会论文片段，为论文写作分析、改写和对标提供真实参考。

    当用户希望参考某个 venue 的写法、某个章节的表达方式，或需要用真实论文片段辅助润色时，优先调用此工具。

    Args:
        query: 用户的论文句子、段落、摘要草稿，或想检索的研究问题描述。
        venue: 目标会议名称，如 NSDI、SIGCOMM、CoNEXT、IMC。
        section: 目标章节，如 INTRODUCTION、DESIGN、EVALUATION、RELATED_WORK。
        n_results: 返回结果数，建议 1 到 5。
        endpoint: 检索服务地址。通常通过 Toolkit preset_kwargs 注入，不需要让模型填写。
        api_key: 可选的接口鉴权密钥。通常通过 Toolkit preset_kwargs 注入。
        timeout_seconds: 请求超时时间。通常通过 Toolkit preset_kwargs 注入。
    """
    cleaned_query = (query or "").strip()
    if not cleaned_query:
        return _text_response("检索失败：query 不能为空。")

    normalized_venue = _normalize_venue(venue)
    normalized_section = _normalize_section(section)
    normalized_n_results = _normalize_n_results(n_results)

    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key

    payload = {
        "query": cleaned_query,
        "venue": normalized_venue,
        "section": normalized_section,
        "n_results": normalized_n_results,
    }

    try:
        response = requests.post(
            endpoint,
            json=payload,
            headers=headers,
            timeout=timeout_seconds,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return _text_response(
            f"论文检索超时：请求 {endpoint} 超过 {timeout_seconds} 秒未返回。",
            metadata=payload,
        )
    except requests.exceptions.RequestException as exc:
        response_text = ""
        if getattr(exc, "response", None) is not None:
            response_text = _truncate(exc.response.text, limit=240)
        error_text = f"论文检索请求失败：{exc}"
        if response_text:
            error_text += f"；响应片段：{response_text}"
        return _text_response(error_text, metadata=payload)

    try:
        data = response.json()
    except ValueError:
        return _text_response(
            f"论文检索失败：服务返回了非 JSON 响应。原始片段：{_truncate(response.text, limit=240)}",
            metadata=payload,
        )

    results = data.get("results") or []
    if not results:
        return _text_response(
            (
                "未检索到可用论文片段。"
                f" venue={normalized_venue} section={normalized_section} query={cleaned_query}"
            ),
            metadata={
                **payload,
                "count": data.get("count", 0),
            },
        )

    lines = [
        (
            f"已检索到 {len(results)} 条论文参考片段。"
            f"目标 venue={data.get('venue', normalized_venue)}，"
            f"section={data.get('section', normalized_section)}。"
            "请优先借鉴叙事结构、术语选择和信息密度，不要逐字照抄。"
        )
    ]

    summarized_results = []
    for index, item in enumerate(results, start=1):
        lines.append(_build_result_summary(index, item))
        summarized_results.append(_build_result_metadata(item))

    return _text_response(
        "\n\n".join(lines),
        metadata={
            "source": "academic_retriever",
            "endpoint": endpoint,
            "query": data.get("query", cleaned_query),
            "venue": data.get("venue", normalized_venue),
            "section": data.get("section", normalized_section),
            "count": data.get("count", len(results)),
            "results": summarized_results,
        },
    )


def register_search_paper_rag_tools(
    toolkit: Toolkit,
) -> None:
    toolkit.register_tool_function(
        search_paper_rag,
        preset_kwargs={
            "endpoint": ACADEMIC_RETRIEVER_SEARCH_URL,
            "api_key": None,
            "timeout_seconds": ACADEMIC_RETRIEVER_TIMEOUT_SECONDS,
        },
    )
