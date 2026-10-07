"""Conversion helpers for ParsedResume and market-job payloads."""

from typing import Any


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return "\n".join(part for item in value if (part := _text(item)))
    if isinstance(value, dict):
        return "\n".join(f"{key}: {part}" for key, raw in value.items()
                         if (part := _text(raw)))
    return ""


def resume_texts(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    sections = payload.get("sections") or {}
    summary = _text(sections.get("summary") or payload.get("summary"))
    experience_bullets = []
    for item in payload.get("experience") or []:
        title = _text(item.get("title"))
        company = _text(item.get("company"))
        for bullet in item.get("bullets") or []:
            text = _text(bullet)
            if text:
                experience_bullets.append(" — ".join(part for part in (title, company, text) if part))
    skills = []
    for skill in payload.get("skills") or []:
        if isinstance(skill, dict):
            name = _text(skill.get("name"))
            evidence = _text(skill.get("evidence"))
            combined = ": ".join(part for part in (name, evidence) if part)
        else:
            combined = _text(skill)
        if combined:
            skills.append(combined)
    projects = _text(sections.get("projects") or sections.get("project") or payload.get("projects"))
    if not projects:
        projects = _text(sections.get("project_details"))
    whole_parts = [summary, *experience_bullets, *skills, projects,
                   _text(sections.get("education")), _text(payload.get("raw_text"))]
    whole = "\n".join(part for part in whole_parts if part)
    if not whole.strip():
        raise ValueError("resume must include summary, experience bullets, skills, projects, education, or raw_text")
    return whole, {"summary": summary, "experience_bullets": experience_bullets,
                   "skills": "\n".join(skills), "projects": projects}


def job_texts(payload: dict[str, Any]) -> tuple[str, dict[str, str]]:
    title = _text(payload.get("title"))
    skills_value = payload.get("skills_required") or payload.get("skills") or []
    skills = _text(skills_value)
    description = _text(payload.get("description"))
    whole = "\n".join(part for part in (f"Title: {title}" if title else "",
                                         f"Required skills: {skills}" if skills else "",
                                         description) if part)
    if not whole.strip():
        raise ValueError("job posting must include title, skills_required, or description")
    return whole, {"title": title, "skills": skills, "description": description}
