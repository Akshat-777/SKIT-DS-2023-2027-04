"""FastAPI router for role taxonomy, skill demand, and skill detail endpoints."""

import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse


def create_market_router(index_dir: Path | None = None) -> APIRouter:
    """Create a standalone router; pass it to the API's FastAPI app with ``include_router``."""
    output_dir = index_dir or Path(os.getenv("MARKET_INDEX_DIR", Path(__file__).resolve().parent.parent / "data" / "processed"))
    router = APIRouter(tags=["market"])

    def load(name: str, fallback: Any) -> Any:
        path = output_dir / name
        if not path.exists():
            return fallback
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError(f"Could not read {name}: {exc}") from exc

    @router.get("/market/roles")
    def get_roles():
        try:
            return {"roles": load("roles.json", [])}
        except RuntimeError as exc:
            return JSONResponse(status_code=503, content={"error": {"code": "MARKET_INDEX_UNAVAILABLE", "message": str(exc)}})

    @router.get("/market/skill-demand")
    def get_skill_demand(role: str | None = None, top_n: str = "15",
                         seniority: str | None = None):
        try:
            limit = int(top_n)
        except ValueError:
            return JSONResponse(status_code=400, content={"error": {"code": "INVALID_TOP_N",
                "message": "top_n must be an integer from 1 through 100"}})
        if not 1 <= limit <= 100:
            return JSONResponse(status_code=400, content={"error": {"code": "INVALID_TOP_N",
                "message": "top_n must be an integer from 1 through 100"}})
        try:
            rows = load("skill_demand.json", [])
        except RuntimeError as exc:
            return JSONResponse(status_code=503, content={"error": {"code": "MARKET_INDEX_UNAVAILABLE", "message": str(exc)}})
        if role:
            rows = [row for row in rows if row["role"].casefold() == role.casefold()]
        if seniority:
            rows = [row for row in rows if row["seniority"].casefold() == seniority.casefold()]
        else:
            rows = [row for row in rows if row["seniority"] == "All"]
        rows.sort(key=lambda row: (row["role"], row["seniority"], row["rank"]))
        return {"role": role, "seniority": seniority, "top_n": limit, "items": rows[:limit]}

    @router.get("/market/skills/{skill}")
    def get_skill(skill: str):
        try:
            taxonomy = load("skills_taxonomy.json", [])
            demand = load("skill_demand.json", [])
        except RuntimeError as exc:
            return JSONResponse(status_code=503, content={"error": {"code": "MARKET_INDEX_UNAVAILABLE", "message": str(exc)}})
        canonical = next((item["name"] for item in taxonomy
                          if item["name"].casefold() == skill.casefold()
                          or any(alias.casefold() == skill.casefold() for alias in item["aliases"])), None)
        if canonical is None:
            from .taxonomy import normalize_skill
            candidate = normalize_skill(skill)
            canonical = candidate if any(item["name"] == candidate for item in taxonomy) else None
        if canonical is None:
            return JSONResponse(status_code=404, content={"error": {"code": "SKILL_NOT_FOUND",
                "message": f"Skill '{skill}' is not present in the canonical taxonomy"}})
        definition = next(item for item in taxonomy if item["name"] == canonical)
        return {"skill": definition, "demand": [row for row in demand if row["skill"] == canonical]}

    return router


router = create_market_router()
