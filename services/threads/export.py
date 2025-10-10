from __future__ import annotations
import datetime
from html import escape
from pathlib import Path
from typing import Dict, List, Optional

from services.retriever.citations import map_citations_to_sources
from services.threads import store

_FONT_MAP: Dict[str, Dict[str, str]] = {
    "standard": {
        "body": "16px",
        "title": "28px",
        "meta": "14px",
        "heading": "20px",
    },
    "large": {
        "body": "20px",
        "title": "36px",
        "meta": "18px",
        "heading": "24px",
    },
}


def _fmt_ts(ts: Optional[int]) -> str:
    if not ts:
        return "Unknown"
    try:
        return datetime.datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M")
    except (OSError, OverflowError, ValueError):
        return str(ts)


def _render_messages(messages: List[Dict]) -> str:
    parts: List[str] = []
    for idx, message in enumerate(messages, 1):
        role_raw = message.get("role") or "assistant"
        role = escape(str(role_raw)).title()
        text_raw = message.get("text")
        if text_raw is None:
            text_raw = message.get("content") or ""
        body = escape(str(text_raw))
        body = body.replace("\n", "<br/>")
        timestamp = _fmt_ts(message.get("ts"))
        parts.append(
            f"<section class=\"message\">\n"
            f"  <header><span class=\"role\">{role}</span> <span class=\"timestamp\">{timestamp}</span></header>\n"
            f"  <div class=\"text\">{body}</div>\n"
        )

        cites = message.get("citations") or []
        if cites:
            cite_items = []
            mapped = map_citations_to_sources(cites)
            for cite in mapped:
                file_name = escape(str(cite.get("file", "")))
                date_val = escape(str(cite.get("date", "")))
                cite_items.append(f"    <li>{file_name} — {date_val}</li>")
            parts.append("  <footer>\n    <ul class=\"citations\">\n" + "\n".join(cite_items) + "\n    </ul>\n  </footer>")

        parts.append("</section>")
    return "\n".join(parts)


def render_thread_html(thread_id: str, options: Optional[Dict[str, str]] = None) -> str:
    thread = store.get_thread(thread_id)
    if thread is None:
        raise ValueError(f"Thread not found: {thread_id}")

    opts = options or {}
    font_key = (opts.get("font") or "standard").lower()
    font_sizes = _FONT_MAP.get(font_key, _FONT_MAP["standard"])

    created = _fmt_ts(thread.get("created_at"))
    updated = _fmt_ts(thread.get("updated_at"))
    client_slug = escape(str(thread.get("client_slug") or "default"))
    source_slug = escape(str(thread.get("source_slug") or "unknown"))
    source_path = escape(str(thread.get("source_path") or ""))

    title = escape(str(thread.get("title") or "Conversation"))
    body_html = _render_messages(thread.get("messages", []))

    appendix = []
    all_citations: List[Dict] = []
    for message in thread.get("messages", []):
        all_citations.extend(message.get("citations") or [])
    mapped_sources = map_citations_to_sources(all_citations)
    if mapped_sources:
        items = []
        for src in mapped_sources:
            file_name = escape(str(src.get("file") or ""))
            date_val = escape(str(src.get("date") or ""))
            items.append(f"        <li>{file_name} — {date_val}</li>")
        appendix_html = "\n".join(items)
        appendix.append(
            "    <section class=\"appendix\">\n"
            "      <h2>Sources</h2>\n"
            "      <ul>\n" + appendix_html + "\n      </ul>\n"
            "    </section>"
        )

    styles = f"""
    <style>
      body {{ font-family: 'Arial', sans-serif; font-size: {font_sizes['body']}; color: #111; margin: 0; padding: 32px; }}
      h1 {{ font-size: {font_sizes['title']}; margin-bottom: 8px; }}
      h2 {{ font-size: {font_sizes['heading']}; margin-top: 32px; margin-bottom: 8px; }}
      .meta {{ font-size: {font_sizes['meta']}; color: #333; margin-bottom: 24px; }}
      .meta dt {{ font-weight: bold; }}
      .meta dd {{ margin: 0 0 8px 0; }}
      .message {{ border-top: 1px solid #ddd; padding-top: 16px; margin-top: 16px; }}
      .message header {{ font-size: {font_sizes['meta']}; color: #555; margin-bottom: 8px; display: flex; gap: 8px; }}
      .message .text {{ line-height: 1.6; }}
      .citations {{ font-size: {font_sizes['meta']}; color: #444; margin: 12px 0 0 0; padding-left: 20px; }}
      .appendix ul {{ padding-left: 20px; }}
    </style>
    """

    meta_rows = [
        f"        <dt>Client</dt><dd>{client_slug}</dd>",
        f"        <dt>Source</dt><dd>{source_slug}</dd>",
        f"        <dt>Source Path</dt><dd>{source_path or '—'}</dd>",
        f"        <dt>Created</dt><dd>{created}</dd>",
        f"        <dt>Updated</dt><dd>{updated}</dd>",
    ]

    appendix_block = "\n".join(appendix) if appendix else ""

    html = (
        "<!DOCTYPE html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\"/>\n"
        f"    <title>{title}</title>\n"
        f"{styles}\n"
        "  </head>\n"
        "  <body>\n"
        f"    <h1>{title}</h1>\n"
        "    <dl class=\"meta\">\n"
        + "\n".join(meta_rows)
        + "\n    </dl>\n"
        f"    {body_html}\n"
        f"{appendix_block}\n"
        "  </body>\n"
        "</html>"
    )
    return html
