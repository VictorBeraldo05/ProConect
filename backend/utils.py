from typing import Any, Dict, Optional

from flask import jsonify


def ok(data: Any, status: int = 200):
    return jsonify(data), status


def fail(message: str, status: int = 400):
    return jsonify({"error": message}), status


def to_int(value: Optional[str], default: int = 0) -> int:
    try:
        return int(value) if value is not None else default
    except Exception:
        return default


def paginate_params(args) -> Dict[str, int]:
    page = max(to_int(args.get("page"), 1), 1)
    page_size = min(max(to_int(args.get("page_size"), 20), 1), 100)
    offset = (page - 1) * page_size
    return {"page": page, "page_size": page_size, "offset": offset, "limit": page_size}

