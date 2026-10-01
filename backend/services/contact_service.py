from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from backend.database import get_connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _row_to_contact(row: Any) -> dict[str, str]:
    return {
        "id": str(row["contact_id"]),
        "group": str(row["group_name"]),
        "organization": str(row["organization"]),
        "label": str(row["label"]),
        "phone": str(row["phone"]),
        "note": str(row["note"]),
        "source": "관리자 등록",
        "sourceUrl": str(row["source_url"]),
    }


def _rows() -> list[Any]:
    with get_connection() as connection:
        return list(connection.execute("SELECT * FROM admin_contacts ORDER BY updated_at DESC").fetchall())


def merge_contact_directory(base_directory: dict[str, Any]) -> dict[str, Any]:
    rows = _rows()
    overrides = {str(row["contact_id"]): row for row in rows}
    contacts: list[dict[str, str]] = []
    base_ids: set[str] = set()

    for contact in base_directory.get("contacts", []):
        contact_id = str(contact.get("id", ""))
        base_ids.add(contact_id)
        override = overrides.get(contact_id)
        if override:
            if int(override["is_deleted"]):
                continue
            contacts.append(_row_to_contact(override))
        else:
            contacts.append(contact)

    for row in rows:
        contact_id = str(row["contact_id"])
        if contact_id not in base_ids and not int(row["is_deleted"]):
            contacts.append(_row_to_contact(row))

    return {
        **base_directory,
        "source": f"{base_directory.get('source', '공식 매뉴얼')} · 관리자 연락처",
        "contacts": contacts,
    }


def find_contact(base_directory: dict[str, Any], contact_id: str) -> dict[str, str] | None:
    return next(
        (contact for contact in merge_contact_directory(base_directory)["contacts"] if contact["id"] == contact_id),
        None,
    )


def save_contact(*, contact_id: str | None, payload: dict[str, str], user_id: int) -> dict[str, str]:
    resolved_id = contact_id or f"admin_{uuid.uuid4().hex[:12]}"
    now = _now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO admin_contacts (
                contact_id, group_name, organization, label, phone, note,
                source_url, is_deleted, updated_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(contact_id) DO UPDATE SET
                group_name = excluded.group_name,
                organization = excluded.organization,
                label = excluded.label,
                phone = excluded.phone,
                note = excluded.note,
                source_url = excluded.source_url,
                is_deleted = 0,
                updated_by = excluded.updated_by,
                updated_at = excluded.updated_at
            """,
            (
                resolved_id,
                payload["group"].strip(),
                payload["organization"].strip(),
                payload["label"].strip(),
                payload["phone"].strip(),
                payload.get("note", "").strip(),
                payload.get("sourceUrl", "").strip(),
                user_id,
                now,
                now,
            ),
        )
        row = connection.execute("SELECT * FROM admin_contacts WHERE contact_id = ?", (resolved_id,)).fetchone()
    return _row_to_contact(row)


def hide_contact(contact: dict[str, str], user_id: int) -> None:
    now = _now()
    with get_connection() as connection:
        connection.execute(
            """
            INSERT INTO admin_contacts (
                contact_id, group_name, organization, label, phone, note,
                source_url, is_deleted, updated_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            ON CONFLICT(contact_id) DO UPDATE SET
                is_deleted = 1,
                updated_by = excluded.updated_by,
                updated_at = excluded.updated_at
            """,
            (
                contact["id"], contact["group"], contact["organization"],
                contact["label"], contact["phone"], contact.get("note", ""),
                contact.get("sourceUrl", ""), user_id, now, now,
            ),
        )
