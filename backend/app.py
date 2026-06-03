from __future__ import annotations

import os
import sys
from typing import Any, Dict

from flask import Flask, jsonify, request, send_from_directory

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT_DIR)

from compiler import compile_and_run  # noqa: E402

from database import init_db, insert_run


FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")


def create_app() -> Flask:
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='/static')
    init_db()

    @app.get("/")
    def index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    @app.post("/api/compile")
    def api_compile():
        payload: Dict[str, Any] = request.get_json(force=True)
        source = payload.get("source", "")
        run = bool(payload.get("run", True))

        result = compile_and_run(source=source, run=run)

        run_id = insert_run(
            source_hash=result.source_hash,
            source_text=source,
            ok=result.ok,
            output_text=result.output_text,
            error_text=result.error_text,
            bytecode=result.bytecode,
        )

        if result.ok:
            return jsonify(
                {
                    "ok": True,
                    "run_id": run_id,
                    "output": result.output_text,
                    "bytecode": result.bytecode,
                }
            )

        return jsonify(
            {
                "ok": False,
                "run_id": run_id,
                "error": result.error_text,
                "bytecode": result.bytecode,
            }
        )

    return app


if __name__ == "__main__":
    init_db()
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )

