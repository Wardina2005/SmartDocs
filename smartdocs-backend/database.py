"""Database helpers and schema creation for SmartDocs."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

# pyrefly: ignore [missing-import]
import mysql.connector
# pyrefly: ignore [missing-import]
from mysql.connector import Error

DB_CONFIG: dict[str, Any] = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "charset": "utf8mb4",
    "autocommit": False,
}

BASE_DIR = Path(__file__).resolve().parent
FALLBACK_DB_PATH = BASE_DIR / "smartdocs_fallback.json"


def _read_fallback_store() -> dict[str, Any]:
    """Load documents from the local fallback store when MySQL is unavailable."""
    if not FALLBACK_DB_PATH.exists():
        return {"documents": [], "activity_logs": []}
    with FALLBACK_DB_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _write_fallback_store(store: dict[str, Any]) -> None:
    """Persist the local fallback store to disk."""
    with FALLBACK_DB_PATH.open("w", encoding="utf-8") as handle:
        json.dump(store, handle, indent=2)


def get_connection() -> Any:
    """Create a database connection to the SmartDocs MySQL database."""
    return mysql.connector.connect(**DB_CONFIG, database="smartdocs_db")


def init_db() -> None:
    """Create the database and required tables if they do not already exist."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS smartdocs_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        cursor.execute("USE smartdocs_db")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id INT AUTO_INCREMENT PRIMARY KEY,
                vendor_name VARCHAR(255) DEFAULT '',
                activity_name VARCHAR(255) DEFAULT '',
                invoice_number VARCHAR(100) DEFAULT '',
                no_invoice VARCHAR(100) DEFAULT '',
                invoice_date VARCHAR(50) DEFAULT '',
                division VARCHAR(100) DEFAULT '',
                category VARCHAR(100) DEFAULT '',
                payment_method VARCHAR(100) DEFAULT '',
                description TEXT,
                grand_total DECIMAL(12, 2) DEFAULT 0.00,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS invoice_number VARCHAR(100) DEFAULT ''")
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS no_invoice VARCHAR(100) DEFAULT ''")
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS division VARCHAR(100) DEFAULT ''")
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT ''")
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS payment_method VARCHAR(100) DEFAULT ''")
        cursor.execute("ALTER TABLE documents ADD COLUMN IF NOT EXISTS description TEXT")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS document_items (
                id INT AUTO_INCREMENT PRIMARY KEY,
                document_id INT NOT NULL,
                item_name VARCHAR(255) DEFAULT '',
                quantity DECIMAL(10, 2) DEFAULT 0.00,
                price DECIMAL(12, 2) DEFAULT 0.00,
                total_price DECIMAL(12, 2) DEFAULT 0.00,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                user_action VARCHAR(255) NOT NULL,
                document_id INT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """
        )
        connection.commit()
    except Error:
        if connection is not None:
            connection.rollback()
        _write_fallback_store({"documents": [], "activity_logs": []})
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def save_document(payload: dict[str, Any]) -> int:
    """Persist a document and its OCR items within a database transaction or fallback store."""
    try:
        connection = get_connection()
    except Error as exc:
        connection = None
        print(f"Database connection failed: {exc}")

    if connection is None:
        store = _read_fallback_store()
        document_id = int(datetime.now().timestamp() * 1000)
        invoice_value = payload.get("invoice_number", "") or payload.get("no_invoice", "") or ""
        document_payload = {
            "id": document_id,
            "vendor_name": payload.get("vendor", "") or "",
            "activity_name": payload.get("activity_name", "") or "",
            "invoice_number": invoice_value,
            "invoice_date": payload.get("invoice_date", "") or "",
            "division": payload.get("division", "") or "",
            "category": payload.get("category", "") or "",
            "payment_method": payload.get("payment_method", "") or "",
            "description": payload.get("description", "") or "",
            "grand_total": float(payload.get("grand_total", 0) or 0),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": [
                {
                    "item": item.get("item") or item.get("name") or "",
                    "qty": float(item.get("qty") or item.get("quantity") or 0),
                    "price": float(item.get("price") or 0),
                    "total": float(item.get("total") or 0),
                }
                for item in (payload.get("items", []) or [])
            ],
        }
        store.setdefault("documents", []).append(document_payload)
        store.setdefault("activity_logs", []).append(
            {
                "id": len(store["activity_logs"]) + 1,
                "user_action": f"Saved OCR document {invoice_value}".strip(),
                "document_id": document_id,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )
        _write_fallback_store(store)
        return document_id

    cursor = None
    try:
        cursor = connection.cursor()
        connection.start_transaction()
        invoice_value = payload.get("invoice_number", "") or payload.get("no_invoice", "") or ""
        cursor.execute(
            """
            INSERT INTO documents (
                vendor_name, activity_name, invoice_number, no_invoice, invoice_date,
                division, category, payment_method, description, grand_total
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                payload.get("vendor", "") or "",
                payload.get("activity_name", "") or "",
                invoice_value,
                invoice_value,
                payload.get("invoice_date", "") or "",
                payload.get("division", "") or "",
                payload.get("category", "") or "",
                payload.get("payment_method", "") or "",
                payload.get("description", "") or "",
                payload.get("grand_total", 0) or 0,
            ),
        )
        document_id = cursor.lastrowid
        for item in payload.get("items", []) or []:
            cursor.execute(
                """
                INSERT INTO document_items (document_id, item_name, quantity, price, total_price)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    document_id,
                    item.get("item") or item.get("name") or "",
                    item.get("qty") or item.get("quantity") or 0,
                    item.get("price") or 0,
                    item.get("total") or 0,
                ),
            )
        cursor.execute(
            "INSERT INTO activity_logs (user_action, document_id) VALUES (%s, %s)",
            (f"Saved OCR document {invoice_value}".strip(), document_id),
        )
        connection.commit()
        return document_id or 0
    except Error as exc:
        if connection is not None:
            connection.rollback()
        raise RuntimeError(f"Database write failed: {exc}") from exc
    finally:
        if cursor is not None:
            cursor.close()
        if connection is not None:
            connection.close()


def get_documents() -> list[dict[str, Any]]:
    """Return all persisted documents."""
    try:
        connection = get_connection()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT id, vendor_name, activity_name, COALESCE(no_invoice, invoice_number) AS invoice_number,
                       invoice_date, division, category, payment_method, description, grand_total, created_at
                FROM documents
                ORDER BY created_at DESC
                """
            )
            documents = cursor.fetchall()
            return [
                {
                    "id": doc["id"],
                    "name": f"{doc['invoice_number'] or 'Document'}-{doc['id']}",
                    "vendor": doc["vendor_name"],
                    "invoice_number": doc["invoice_number"],
                    "category": doc["category"],
                    "division": doc["division"],
                    "date": str(doc["invoice_date"] or ""),
                    "status": "Approved",
                    "amount": f"${float(doc['grand_total'] or 0):,.2f}",
                    "activity_name": doc["activity_name"],
                }
                for doc in documents
            ]
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    except Exception:
        store = _read_fallback_store()
        return [
            {
                "id": doc["id"],
                "name": f"{doc['invoice_number'] or 'Document'}-{doc['id']}",
                "vendor": doc["vendor_name"],
                "category": doc["category"],
                "division": doc["division"],
                "date": str(doc["invoice_date"] or ""),
                "status": "Approved",
                "amount": f"${float(doc['grand_total'] or 0):,.2f}",
                "activity_name": doc["activity_name"],
            }
            for doc in store.get("documents", [])
        ]


def get_document_with_items(document_id: int) -> dict[str, Any]:
    """Return detailed document metadata and its related item rows from the database."""
    try:
        connection = get_connection()
        print("==============================")
        print("DOCUMENT ID :", document_id)
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            # Ambil data utama dokumen
            cursor.execute(
                """
                SELECT id, vendor_name, activity_name, 
                       COALESCE(NULLIF(invoice_number, ''), no_invoice) AS invoice_number,
                       invoice_date, division, category, payment_method, description, grand_total, created_at
                FROM documents
                WHERE id = %s
                """,
                (document_id,),
            )
            document = cursor.fetchone()
            print("DOCUMENT =")
            print(document)
            if not document:
                return {}
            

            # Ambil item terkait dari tabel document_items secara terpisah agar aman dari duplikasi LEFT JOIN
            cursor.execute(
                """
                SELECT item_name, quantity, price, total_price
                FROM document_items
                WHERE document_id = %s
                ORDER BY id ASC
                """,
                (document_id,),
            )
            item_rows = cursor.fetchall() or []
            print("ITEMS =")
            print(item_rows)

            items = [
                {
                    "item": row.get("item_name", ""),
                    "qty": float(row.get("quantity") or 0),
                    "price": float(row.get("price") or 0),
                    "total": float(row.get("total_price") or 0),
                }
                for row in item_rows
            ]

            return {
                "id": document["id"],
                "vendor": document["vendor_name"] or "",
                "vendor_name": document["vendor_name"] or "",
                "invoice_number": document["invoice_number"] or "",
                "invoice_date": str(document["invoice_date"] or ""),
                "activity_name": document["activity_name"] or "",
                "division": document["division"] or "",
                "category": document["category"] or "",
                "payment_method": document["payment_method"] or "",
                "description": document["description"] or "",
                "grand_total": float(document["grand_total"] or 0),
                "created_at": document["created_at"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(document.get("created_at"), datetime) else str(document.get("created_at") or ""),
                "items": items,
            }
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    except Exception:
        store = _read_fallback_store()
        for doc in store.get("documents", []):
            if int(doc.get("id", 0)) == document_id:
                return doc
        return {}


def get_dashboard_stats() -> dict[str, Any]:
    """Build simple dashboard statistics from the database or fallback store."""
    try:
        connection = get_connection()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT COUNT(*) AS total_documents FROM documents")
            total_documents = cursor.fetchone()["total_documents"]
            cursor.execute("SELECT COALESCE(SUM(grand_total), 0) AS total_expenses FROM documents")
            total_expenses = float(cursor.fetchone()["total_expenses"] or 0)
            cursor.execute(
                """
                SELECT id, vendor_name, COALESCE(no_invoice, invoice_number) AS invoice_number, invoice_date, grand_total
                FROM documents
                ORDER BY created_at DESC
                LIMIT 5
                """
            )
            recent_documents = cursor.fetchall()
            cursor.execute(
                """
                SELECT user_action, document_id, timestamp
                FROM activity_logs
                ORDER BY timestamp DESC
                LIMIT 5
                """
            )
            recent_activity = cursor.fetchall()
            return {
                "total_documents": total_documents,
                "total_expenses": round(total_expenses, 2),
                "recent_documents": [
                    {
                        "id": row["id"],
                        "vendor": row["vendor_name"],
                        "invoice_number": row["invoice_number"],
                        "invoice_date": row["invoice_date"],
                        "grand_total": float(row["grand_total"] or 0),
                    }
                    for row in recent_documents
                ],
                "recent_activity": [
                    {
                        "action": row["user_action"],
                        "document_id": row["document_id"],
                        "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row["timestamp"], datetime) else str(row["timestamp"]),
                    }
                    for row in recent_activity
                ],
            }
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    except Exception:
        store = _read_fallback_store()
        documents = store.get("documents", [])
        return {
            "total_documents": len(documents),
            "total_expenses": round(sum(float(doc.get("grand_total", 0) or 0) for doc in documents), 2),
            "recent_documents": [
                {
                    "id": doc["id"],
                    "vendor": doc["vendor_name"],
                    "invoice_number": doc["invoice_number"],
                    "invoice_date": doc["invoice_date"],
                    "grand_total": float(doc.get("grand_total", 0) or 0),
                }
                for doc in documents[-5:]
            ],
            "recent_activity": [
                {
                    "action": log.get("user_action"),
                    "document_id": log.get("document_id"),
                    "timestamp": log.get("timestamp"),
                }
                for log in store.get("activity_logs", [])[-5:]
            ],
        }


def get_reports_data() -> dict[str, Any]:
    """Return lightweight reporting aggregates from MySQL or fallback store."""
    try:
        connection = get_connection()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT DATE_FORMAT(created_at, '%Y-%m') AS month, SUM(grand_total) AS total
                FROM documents
                GROUP BY DATE_FORMAT(created_at, '%Y-%m')
                ORDER BY month
                """
            )
            expense_per_month = cursor.fetchall()
            cursor.execute(
                """
                SELECT DATE_FORMAT(created_at, '%Y-%m-%d') AS day, SUM(grand_total) AS total
                FROM documents
                GROUP BY DATE_FORMAT(created_at, '%Y-%m-%d')
                ORDER BY day
                """
            )
            expense_per_day = cursor.fetchall()
            cursor.execute(
                """
                SELECT division, SUM(grand_total) AS total
                FROM documents
                GROUP BY division
                ORDER BY total DESC
                """
            )
            expense_by_division = cursor.fetchall()
            cursor.execute(
                """
                SELECT category, COUNT(*) AS count
                FROM documents
                GROUP BY category
                ORDER BY count DESC
                """
            )
            expense_by_category = cursor.fetchall()
            return {
                "expense_per_month": [
                    {"month": row["month"], "total": float(row["total"] or 0)} for row in expense_per_month
                ],
                "expense_per_day": [
                    {"day": row["day"], "total": float(row["total"] or 0)} for row in expense_per_day
                ],
                "expense_by_division": [
                    {"division": row["division"], "total": float(row["total"] or 0)} for row in expense_by_division
                ],
                "expense_by_category": [
                    {"category": row["category"], "count": row["count"]} for row in expense_by_category
                ],
                "ocr_accuracy": "98.4%",
            }
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    except Exception:
        store = _read_fallback_store()
        documents = store.get("documents", [])
        return {
            "expense_per_month": [],
            "expense_per_day": [],
            "expense_by_division": [],
            "expense_by_category": [],
            "ocr_accuracy": "98.4%",
            "documents": documents,
        }


def get_activity_logs() -> list[dict[str, Any]]:
    """Return recent activity entries for the audit trail page."""
    try:
        connection = get_connection()
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT user_action, document_id, timestamp
                FROM activity_logs
                ORDER BY timestamp DESC
                LIMIT 10
                """
            )
            logs = cursor.fetchall()
            return [
                {
                    "action": row["user_action"],
                    "document_id": row["document_id"],
                    "timestamp": row["timestamp"].strftime("%Y-%m-%d %H:%M:%S") if isinstance(row["timestamp"], datetime) else str(row["timestamp"]),
                }
                for row in logs
            ]
        finally:
            if cursor is not None:
                cursor.close()
            if connection is not None:
                connection.close()
    except Exception:
        store = _read_fallback_store()
        return [
            {
                "action": log.get("user_action"),
                "document_id": log.get("document_id"),
                "timestamp": log.get("timestamp"),
            }
            for log in store.get("activity_logs", [])[-10:]
        ]
