from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from backend.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def merge_quick_guides(base_catalog: dict[str, Any]) -> dict[str, Any]:
    with get_connection() as connection:
        rows = connection.execute("SELECT * FROM guide_overrides").fetchall()
    overrides = {str(row["guide_id"]): row for row in rows}
    guides: list[dict[str, Any]] = []

    for original in base_catalog.get("guides", []):
        guide = dict(original)
        override = overrides.get(str(guide.get("id", "")))
        if override:
            guide.update(
                {
                    "title": str(override["title"]),
                    "description": str(override["description"]),
                    "sections": json.loads(str(override["sections_json"])),
                    "cautions": json.loads(str(override["cautions_json"])),
                }
            )
        guides.append(guide)

    return {**base_catalog, "guides": guides}


def save_guide_override(
    *,
    guide_id: str,
    payload: dict[str, Any],
    user_id: int,
) -> None:
    now = _now()
    sections = [
        {
            "title": str(section.get("title", "")).strip(),
            "timeLabel": str(section.get("timeLabel", "")).strip(),
            "steps": [str(step).strip() for step in section.get("steps", []) if str(step).strip()],
        }
        for section in payload.get("sections", [])
        if str(section.get("title", "")).strip()
    ]
    cautions = [str(item).strip() for item in payload.get("cautions", []) if str(item).strip()]

    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO guide_overrides (
                guide_id, title, description, sections_json, cautions_json,
                updated_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(guide_id) DO UPDATE SET
                title = excluded.title,
                description = excluded.description,
                sections_json = excluded.sections_json,
                cautions_json = excluded.cautions_json,
                updated_by = excluded.updated_by,
                updated_at = excluded.updated_at
            """,
            (
                guide_id,
                str(payload["title"]).strip(),
                str(payload["description"]).strip(),
                json.dumps(sections, ensure_ascii=False),
                json.dumps(cautions, ensure_ascii=False),
                user_id,
                now,
                now,
            ),
        )


def delete_guide_override(guide_id: str) -> bool:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM guide_overrides WHERE guide_id = ?", (guide_id,))
        return cursor.rowcount > 0
