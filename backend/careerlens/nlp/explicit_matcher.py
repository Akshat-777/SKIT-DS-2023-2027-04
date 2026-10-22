"""Explicit Skill Extraction Engine for CareerLens.
Uses an Aho-Corasick automaton with case-insensitivity, custom token boundary checks
for punctuation variants (C++, C#, Node.js, scikit-learn, etc.), alias normalization,
longest-match preference, and contextual disambiguation rules (Go, R, Spring, Word, Excel, etc.).
"""

from __future__ import annotations

import collections
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from careerlens.nlp.taxonomy_loader import SkillTaxonomy, normalize_lookup_key


class TrieNode:
    """Node for Aho-Corasick Trie Automaton."""
    __slots__ = ("children", "fail", "outputs")

    def __init__(self):
        self.children: Dict[str, TrieNode] = {}
        self.fail: Optional[TrieNode] = None
        # outputs stores tuples of (canonical_name, pattern_len, original_pattern)
        self.outputs: List[Tuple[str, int, str]] = []


class AhoCorasickAutomaton:
    """
    Pure Python Aho-Corasick automaton with linear time multi-string pattern matching.
    """

    def __init__(self):
        self.root = TrieNode()
        self._built = False

    def insert(self, pattern: str, canonical_name: str) -> None:
        """Insert pattern in lower-case form."""
        node = self.root
        pattern_norm = pattern.lower()
        for char in pattern_norm:
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.outputs.append((canonical_name, len(pattern_norm), pattern))
        self._built = False

    def build(self) -> None:
        """Construct failure links using breadth-first search (BFS)."""
        queue: collections.deque[TrieNode] = collections.deque()

        # Set depth-1 failure links to root
        for child in self.root.children.values():
            child.fail = self.root
            queue.append(child)

        # BFS for deeper nodes
        while queue:
            curr = queue.popleft()

            for char, child in curr.children.items():
                fail_state = curr.fail
                while fail_state is not None and char not in fail_state.children:
                    fail_state = fail_state.fail

                child.fail = fail_state.children[char] if fail_state is not None else self.root
                # Inherit outputs from fail state
                if child.fail.outputs:
                    child.outputs.extend(child.fail.outputs)

                queue.append(child)

        self._built = True

    def search_all(self, text: str) -> List[Tuple[int, int, str, str]]:
        """
        Scan text and return matches as (start_idx, end_idx, canonical_name, matched_pattern).
        """
        if not self._built:
            self.build()

        matches: List[Tuple[int, int, str, str]] = []
        node = self.root
        text_lower = text.lower()

        for idx, char in enumerate(text_lower):
            while node is not None and char not in node.children:
                node = node.fail

            if node is None:
                node = self.root
                continue

            node = node.children[char]
            if node.outputs:
                for canonical_name, pat_len, pat in node.outputs:
                    start_idx = idx - pat_len + 1
                    end_idx = idx + 1
                    matches.append((start_idx, end_idx, canonical_name, pat))

        return matches


# Punctuation chars that can be part of skill names
SKILL_PUNCTUATION = {"+", "#", ".", "-", "/", "_"}


def is_valid_token_boundary(text: str, start: int, end: int, pattern: str) -> bool:
    """
    Accurately validates word and punctuation boundaries.
    Handles tricky variants like C++, C#, .NET, Node.js, Next.js, and scikit-learn.
    """
    text_len = len(text)

    # 1. Check preceding boundary
    if start > 0:
        prev_char = text[start - 1]
        # If pattern starts with an alphanumeric char, prev_char must not be alphanumeric or symbol forming an identifier
        if pattern[0].isalnum():
            if prev_char.isalnum():
                return False
            # Prevent matching inside filenames or other extensions (e.g. "myc++" or "abc.js")
            if prev_char in {"+", "#", "@"}:
                return False
        elif pattern[0] == ".":
            # e.g. ".NET"
            if prev_char.isalnum():
                return False

    # 2. Check trailing boundary
    if end < text_len:
        next_char = text[end]
        last_pat_char = pattern[-1]

        # If pattern ends with an alphanumeric char, next_char must not be alphanumeric
        if last_pat_char.isalnum():
            if next_char.isalnum():
                return False
            # Prevent "JS" matching inside "JSON" or "JSP"
            if next_char in {"+", "#"}:
                return False
        elif last_pat_char in {"+", "#"}:
            # For C++ or C#, ensure not followed by another + or #
            if next_char in {"+", "#"} or next_char.isalnum():
                return False
        elif last_pat_char == ".":
            if next_char.isalnum():
                return False

    return True


class ExplicitSkillMatcher:
    """
    High-performance, context-aware explicit skill extractor.
    """

    def __init__(self, taxonomy: Optional[SkillTaxonomy] = None):
        self.taxonomy = taxonomy or SkillTaxonomy()
        self.automaton = AhoCorasickAutomaton()
        self._init_automaton()

    def _init_automaton(self) -> None:
        """Loads all patterns and aliases into the Aho-Corasick automaton."""
        for pattern, canonical in self.taxonomy.get_all_patterns():
            # Skip very short single character patterns from blind automaton matching;
            # they are handled with strict context rules in ambiguity checks
            if len(pattern.strip()) >= 1:
                self.automaton.insert(pattern.strip(), canonical)

        self.automaton.build()

    def _check_ambiguity(
        self,
        canonical: str,
        matched_str: str,
        sentence: str,
        section_name: str,
        all_matched_canonicals: Set[str]
    ) -> Tuple[bool, float]:
        """
        Contextual disambiguation for ambiguous words:
        Returns (is_valid, confidence).
        """
        sent_lower = sentence.lower()
        matched_lower = matched_str.lower()
        in_skills_section = any(k in section_name.lower() for k in ["skill", "technical", "technologies", "competencies"])

        # 1. "Go"
        if canonical == "Go":
            if matched_lower in ["golang", "go language", "go programming"]:
                return True, 1.0
            # Plain "go" or "Go"
            # Rejection patterns: action verbs, phrases
            if re.search(r"\b(to\s+go|let's\s+go|go\s+through|go\s+live|go-to|on\s+the\s+go|go\s+ahead)\b", sent_lower):
                return False, 0.0
            # Accept if in skills section or surrounded by tech stack terms
            tech_indicators = {"docker", "kubernetes", "k8s", "microservices", "backend", "concurrency", "goroutines", "grpc", "c++", "python", "rust"}
            if in_skills_section or any(ind in sent_lower for ind in tech_indicators) or any(t in all_matched_canonicals for t in ["Docker", "Kubernetes", "gRPC", "Python"]):
                return True, 0.90
            return False, 0.0

        # 2. "R"
        if canonical == "R":
            if matched_lower in ["r language", "r programming", "r script", "r package", "rstudio"]:
                return True, 1.0
            # Check for false positives: initials like "John R. Smith", R&D
            if re.search(r"\b(r&d|r\s+&\s+d|r\s+and\s+d)\b", sent_lower):
                return False, 0.0
            if re.search(r"(\b[A-Z][a-z]+\s+R\.\s+[A-Z][a-z]+|\bR\.\s+[A-Z][a-z]+)", sentence):
                return False, 0.0
            # Accept if accompanied by programming languages or data keywords
            if any(lang in sent_lower for lang in ["python", "sql", "julia", "sas", "spss", "matlab", "tableau"]):
                return True, 0.95
            if in_skills_section:
                return True, 0.90
            stats_indicators = {"statistics", "statistical", "regression", "ggplot", "data analysis", "analyzed data", "data analytics", "modeling", "bioinformatics", "econometrics"}
            if any(ind in sent_lower for ind in stats_indicators):
                return True, 0.90
            return False, 0.0

        # 3. "Spring"
        if canonical in ["Spring Boot", "Spring MVC"]:
            return True, 1.0
        if canonical == "Spring":
            # Reject semester / graduation dates: "Spring 2022", "Spring semester", "Spring 2024"
            if re.search(r"\bspring\s+(20\d{2}|19\d{2}|semester|term|break)\b", sent_lower):
                return False, 0.0
            # Accept if Java / backend context or skills section
            if in_skills_section or any(k in sent_lower for k in ["java", "boot", "mvc", "backend", "hibernate", "microservice"]):
                return True, 0.92
            return False, 0.0

        # 4. "Word"
        if canonical == "Microsoft Word":
            if matched_lower in ["microsoft word", "ms word", "ms-word"]:
                return True, 1.0
            # Plain "word" is almost always the English word
            return False, 0.0

        # 5. "Excel"
        if canonical == "Excel":
            if matched_lower in ["microsoft excel", "ms excel", "excel vba", "advanced excel"]:
                return True, 1.0
            # Plain "excel" as verb: "excel in", "to excel", "excelled at"
            if re.search(r"\b(excel\s+in|to\s+excel|excelled|ability\s+to\s+excel)\b", sent_lower):
                return False, 0.0
            if in_skills_section or any(k in sent_lower for k in ["spreadsheet", "vlookup", "pivot", "formulas", "power bi"]):
                return True, 0.90
            return False, 0.0

        # 6. "C"
        if canonical == "C":
            if matched_lower in ["c programming", "c language", "ansi c", "embedded c", "c/c++"]:
                return True, 1.0
            # Solitary "C": require explicit programming indicator or paired with C++
            if re.search(r"\b(c/c\+\+|c\s+and\s+c\+\+|c\s+programming|c\s+language)\b", sent_lower):
                return True, 0.95
            if in_skills_section and re.search(r"(c,\s*c\+\+|c\+\+,\s*c\b|c,\s*java|python,\s*c\b)", sent_lower):
                return True, 0.88
            return False, 0.0

        # 7. "React"
        if canonical == "React":
            if matched_lower in ["react.js", "reactjs", "react framework"]:
                return True, 1.0
            # Check for general English verb: "react to", "react quickly"
            if re.search(r"\b(react\s+to|react\s+quickly|ability\s+to\s+react)\b", sent_lower):
                return False, 0.0
            if in_skills_section or any(k in sent_lower for k in ["javascript", "frontend", "redux", "next.js", "hooks", "ui", "web", "dom"]):
                return True, 0.95
            return False, 0.0

        # 8. "Swift"
        if canonical == "Swift":
            if matched_lower in ["swift language", "swiftui"]:
                return True, 1.0
            if re.search(r"\b(swift\s+response|swift\s+action|swiftly)\b", sent_lower):
                return False, 0.0
            if in_skills_section or any(k in sent_lower for k in ["ios", "apple", "xcode", "mobile", "uikit"]):
                return True, 0.95
            return False, 0.0

        # 9. "Rust"
        if canonical == "Rust":
            if matched_lower in ["rustlang", "rust programming"]:
                return True, 1.0
            if in_skills_section or any(k in sent_lower for k in ["cargo", "memory safe", "systems", "c++", "concurrency"]):
                return True, 0.95
            return False, 0.0

        # 10. "Dart"
        if canonical == "Dart":
            if matched_lower in ["dart language", "dart lang"]:
                return True, 1.0
            if in_skills_section or any(k in sent_lower for k in ["flutter", "mobile", "widget"]):
                return True, 0.95
            return False, 0.0

        # 11. "Git"
        if canonical == "Git":
            if in_skills_section or any(k in sent_lower for k in ["github", "gitlab", "branch", "commit", "merge", "repo", "version control"]):
                return True, 1.0
            return False, 0.0

        return True, 1.0

    def extract_from_text(
        self,
        text: str,
        section_name: str = "General"
    ) -> List[Dict[str, Any]]:
        """
        Extracts explicit skills from text block with token boundary checks,
        longest-match resolution, and contextual disambiguation.
        """
        raw_matches = self.automaton.search_all(text)
        if not raw_matches:
            return []

        # Filter valid token boundaries
        valid_matches: List[Tuple[int, int, str, str]] = []
        for start, end, canonical, pattern in raw_matches:
            if is_valid_token_boundary(text, start, end, pattern):
                valid_matches.append((start, end, canonical, pattern))

        # Longest match resolution: prioritize longer spanning matches
        # e.g., "Spring Boot" over "Spring", "React Native" over "React", "Node.js" over "Node"
        valid_matches.sort(key=lambda m: (m[0], -(m[1] - m[0])))
        filtered_matches: List[Tuple[int, int, str, str]] = []
        last_end = -1

        for match in valid_matches:
            start, end, canonical, pattern = match
            if start >= last_end:
                filtered_matches.append(match)
                last_end = end
            else:
                # If nested, pick the longer pattern
                prev_match = filtered_matches[-1]
                if (end - start) > (prev_match[1] - prev_match[0]):
                    filtered_matches[-1] = match
                    last_end = end

        # Extract sentences for evidence tracking
        sentences = [s.strip() for s in re.split(r"(?<=[.!?\n])\s+", text) if s.strip()]
        all_found_canonicals = {m[2] for m in filtered_matches}

        skills_dict: Dict[str, Dict[str, Any]] = {}

        for start, end, canonical, pattern in filtered_matches:
            # Find evidence sentence
            matched_slice = text[start:end]
            evidence_sent = ""
            for sent in sentences:
                if matched_slice in sent:
                    evidence_sent = sent
                    break
            if not evidence_sent:
                evidence_sent = text[max(0, start - 40):min(len(text), end + 40)].strip()

            # Ambiguity check
            is_valid, conf = self._check_ambiguity(
                canonical=canonical,
                matched_str=matched_slice,
                sentence=evidence_sent,
                section_name=section_name,
                all_matched_canonicals=all_found_canonicals
            )
            if not is_valid:
                continue

            # Standard confidence weighting: exact canonical = 1.0, direct alias = 0.95
            is_canonical_name = (matched_slice.strip().lower() == canonical.lower())
            final_conf = conf if not is_canonical_name else min(conf, 1.0)
            if not is_canonical_name and final_conf == 1.0:
                final_conf = 0.95

            # Deduplicate by canonical name, keeping higher confidence
            if canonical in skills_dict:
                if final_conf > skills_dict[canonical]["confidence"]:
                    skills_dict[canonical]["confidence"] = round(final_conf, 2)
                    skills_dict[canonical]["evidence"] = f"[{section_name}] {evidence_sent}"
            else:
                skills_dict[canonical] = {
                    "name": canonical,
                    "type": "explicit",
                    "confidence": round(final_conf, 2),
                    "evidence": f"[{section_name}] {evidence_sent}"
                }

        return list(skills_dict.values())

    def extract_from_sections(self, sections: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Extracts skills across categorized resume sections.
        """
        all_skills: Dict[str, Dict[str, Any]] = {}
        for section_name, section_text in sections.items():
            section_skills = self.extract_from_text(section_text, section_name=section_name)
            for skill in section_skills:
                cname = skill["name"]
                if cname in all_skills:
                    if skill["confidence"] > all_skills[cname]["confidence"]:
                        all_skills[cname] = skill
                else:
                    all_skills[cname] = skill
        return list(all_skills.values())
