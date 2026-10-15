"""Skill Taxonomy Loader for CareerLens.
Reads canonical skills with aliases, categories, and parent skills,
creates/supplements starter taxonomy with 340+ skills if needed,
and builds O(1) normalized lookup tables.
"""

from __future__ import annotations

import csv
import json
import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from careerlens.nlp.taxonomy_data import STARTER_SKILLS_DATA

LOG = logging.getLogger("careerlens.nlp.taxonomy")

# Known ambiguous skills that require context validation
AMBIGUOUS_SKILLS = {
    "Go", "R", "C", "Spring", "Word", "Excel", "React", "Swift", "Rust", "Dart", "Git"
}


def normalize_lookup_key(text: str) -> str:
    """
    Standardize text for dictionary lookups:
    - Lowercase
    - Strip surrounding whitespace
    - Normalize internal whitespace
    - Retain relevant punctuation chars: +, #, ., -, /
    """
    cleaned = re.sub(r"\s+", " ", str(text).strip().lower())
    return cleaned


class SkillTaxonomy:
    """
    In-memory representation of the skill taxonomy with fast O(1) lookups,
    alias normalization, and exemplar mappings for implicit embedding comparisons.
    """

    def __init__(self, taxonomy_path: Optional[str] = None):
        self.taxonomy_path = taxonomy_path
        self._skills_by_canonical: Dict[str, Dict[str, Any]] = {}
        self._alias_to_canonical: Dict[str, str] = {}
        self._category_to_skills: Dict[str, List[str]] = {}
        self._parent_to_children: Dict[str, List[str]] = {}
        self._multiword_skills: Set[str] = set()
        self._exemplars_list: List[Tuple[str, str]] = []  # (exemplar_text, canonical_skill)

        self._load_taxonomy()

    def _load_taxonomy(self) -> None:
        """Loads taxonomy from file if available, otherwise bootstraps starter dataset."""
        loaded_data: List[Dict[str, Any]] = []

        # Determine target file path
        target_path = None
        if self.taxonomy_path and os.path.exists(self.taxonomy_path):
            target_path = Path(self.taxonomy_path)
        else:
            # Check default locations
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            candidate_paths = [
                repo_root / "data" / "skills_taxonomy.json",
                repo_root / "data" / "processed" / "skills_taxonomy.json",
                repo_root / "data" / "processed" / "skills_taxonomy.csv",
            ]
            for p in candidate_paths:
                if p.exists() and p.stat().st_size > 500:
                    target_path = p
                    break

        if target_path and target_path.exists():
            try:
                if target_path.suffix.lower() == ".json":
                    with open(target_path, "r", encoding="utf-8") as f:
                        loaded_data = json.load(f)
                elif target_path.suffix.lower() == ".csv":
                    with open(target_path, "r", encoding="utf-8-sig") as f:
                        reader = csv.DictReader(f)
                        for row in reader:
                            aliases = [a.strip() for a in row.get("aliases", "").split(";") if a.strip()]
                            loaded_data.append({
                                "name": row.get("name") or row.get("canonical_name"),
                                "aliases": aliases,
                                "category": row.get("category", "General"),
                                "parent": row.get("parent") or None,
                                "exemplars": [e.strip() for e in row.get("exemplars", "").split(";") if e.strip()]
                            })
            except Exception as e:
                LOG.warning(f"Failed to read existing taxonomy at {target_path}: {e}")

        # If existing taxonomy is small (< 300 skills), merge starter skills data
        existing_names = {item.get("name") for item in loaded_data if item.get("name")}
        
        # Merge starter dataset to guarantee at least 300+ skills
        for starter_item in STARTER_SKILLS_DATA:
            name = starter_item["name"]
            if name not in existing_names:
                loaded_data.append(starter_item)
                existing_names.add(name)
            else:
                # Merge any missing exemplars or aliases
                for item in loaded_data:
                    if item.get("name") == name:
                        existing_aliases = set(item.get("aliases", []))
                        for a in starter_item.get("aliases", []):
                            if a not in existing_aliases:
                                item.setdefault("aliases", []).append(a)
                        existing_ex = set(item.get("exemplars", []))
                        for ex in starter_item.get("exemplars", []):
                            if ex not in existing_ex:
                                item.setdefault("exemplars", []).append(ex)
                        break

        # Save merged starter file if target didn't exist or had < 300 skills
        try:
            repo_root = Path(__file__).resolve().parent.parent.parent.parent
            save_path = repo_root / "data" / "skills_taxonomy.json"
            save_path.parent.mkdir(parents=True, exist_ok=True)
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(loaded_data, f, indent=2)
        except Exception as e:
            LOG.debug(f"Note: Could not persist merged taxonomy JSON: {e}")

        # Build index lookups
        self._index_taxonomy(loaded_data)

    def _index_taxonomy(self, data: List[Dict[str, Any]]) -> None:
        """Indexes skills into fast dictionary lookup structures."""
        self._skills_by_canonical.clear()
        self._alias_to_canonical.clear()
        self._category_to_skills.clear()
        self._parent_to_children.clear()
        self._multiword_skills.clear()
        self._exemplars_list.clear()

        for item in data:
            name = item.get("name", "").strip()
            if not name:
                continue

            category = item.get("category", "General")
            parent = item.get("parent")
            aliases = item.get("aliases", [])
            exemplars = item.get("exemplars", [])

            self._skills_by_canonical[name] = {
                "name": name,
                "category": category,
                "parent": parent,
                "aliases": aliases,
                "exemplars": exemplars
            }

            # Map canonical name to itself
            self._alias_to_canonical[normalize_lookup_key(name)] = name

            # Map all aliases to canonical name
            for alias in aliases:
                norm_alias = normalize_lookup_key(alias)
                if norm_alias:
                    self._alias_to_canonical[norm_alias] = name

            # Track multi-word skills for phrase matching
            if len(name.split()) > 1 or "-" in name or "/" in name:
                self._multiword_skills.add(name)

            for alias in aliases:
                if len(alias.split()) > 1 or "-" in alias or "/" in alias:
                    self._multiword_skills.add(alias)

            # Category index
            self._category_to_skills.setdefault(category, []).append(name)

            # Hierarchy parent index
            if parent:
                self._parent_to_children.setdefault(parent, []).append(name)

            # Exemplar mapping for semantic embedding layer
            if exemplars:
                for ex in exemplars:
                    self._exemplars_list.append((ex.strip(), name))
            else:
                # Default exemplar fallback: skill name + category
                self._exemplars_list.append((f"demonstrated proficiency in {name} for {category}", name))

    @property
    def total_skills_count(self) -> int:
        return len(self._skills_by_canonical)

    @property
    def canonical_skills(self) -> List[str]:
        return list(self._skills_by_canonical.keys())

    def get_canonical(self, alias_or_name: str) -> Optional[str]:
        """Normalize an alias or string to its canonical skill name."""
        return self._alias_to_canonical.get(normalize_lookup_key(alias_or_name))

    def get_skill_info(self, canonical_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve full skill metadata."""
        return self._skills_by_canonical.get(canonical_name)

    def is_ambiguous(self, skill_name: str) -> bool:
        """Returns True if skill requires contextual disambiguation."""
        return skill_name in AMBIGUOUS_SKILLS

    def get_all_patterns(self) -> List[Tuple[str, str]]:
        """Returns list of (search_pattern, canonical_name) for matching."""
        patterns: List[Tuple[str, str]] = []
        for norm_pattern, canonical in self._alias_to_canonical.items():
            patterns.append((norm_pattern, canonical))
        return patterns

    def get_all_exemplars(self) -> List[Tuple[str, str]]:
        """Returns list of (exemplar_phrase, canonical_name)."""
        return list(self._exemplars_list)
