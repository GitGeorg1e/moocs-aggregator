from __future__ import annotations

import json
import re
import time
from datetime import datetime
from typing import Iterable, List, Optional, Set
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from lxml import etree
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.schemas.course import CourseCreate


class CourseraConnector:
    def __init__(
        self,
        source_id: int,
        course_sitemap_url: str,
        max_urls: int,
        timeout_s: int,
        sleep_ms: int,
        max_retries: int,
    ) -> None:
        self.source_id = source_id
        self.course_sitemap_url = course_sitemap_url
        self.max_urls = max_urls
        self.timeout_s = timeout_s
        self.sleep_ms = sleep_ms
        self.max_retries = max_retries

        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "mooc-aggregator-bot/1.0 (course metadata harvester)"}
        )

    def fetch_courses(self, since: Optional[datetime] = None) -> Iterable[CourseCreate]:
        urls = self._discover_course_urls()
        for i, url in enumerate(urls):
            html = self._get_text(url)
            course = self._parse_course_page(url, html)
            if course is None:
                continue
            if since is not None and course.last_updated_at_source is not None:
                if course.last_updated_at_source < since:
                    continue
            yield course
            self._sleep()

    def _discover_course_urls(self) -> List[str]:
        xml = self._get_text(self.course_sitemap_url)
        root = etree.fromstring(xml.encode("utf-8"))

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = root.xpath("//sm:url/sm:loc/text()", namespaces=ns)

        seen: Set[str] = set()
        out: List[str] = []
        for loc in locs:
            if "/learn/" not in loc:
                continue
            if loc in seen:
                continue
            seen.add(loc)
            out.append(loc)
            if len(out) >= self.max_urls:
                break

        return out

    def _parse_course_page(self, url: str, html: str) -> Optional[CourseCreate]:
        soup = BeautifulSoup(html, "html.parser")
        ld_json = self._extract_json_ld_course(soup)

        title = None
        description = None
        language = None
        keywords = None
        level = None
        updated = None
        topic = None
        skills: List[str] = []

        if ld_json:
            title = ld_json.get("name")
            description = ld_json.get("description")
            language = self._normalize_language(ld_json.get("inLanguage"))
            keywords = self._normalize_keywords(ld_json.get("keywords"))
            level = self._normalize_level(ld_json.get("educationalLevel"))
            topic = self._pick_first_keyword(
                self._normalize_keywords(
                    ld_json.get("about")
                    or ld_json.get("topic")
                    or ld_json.get("subject")
                    or ld_json.get("keywords")
                )
            )
            updated = self._parse_dt(ld_json.get("dateModified"))

        slug = self._slug_from_url(url)
        source_course_id = slug or url

        if not title:
            og = soup.find("meta", attrs={"property": "og:title"})
            title = og.get("content") if og else None

        if not description:
            meta = soup.find("meta", attrs={"name": "description"})
            description = meta.get("content") if meta else None

        # Fallback language detection from multiple sources
        if not language:
            language = self._extract_language_from_html(soup)

        embedded_payloads = self._extract_embedded_json_payloads(soup)
        skills = self._extract_skills_from_page(soup, ld_json, embedded_payloads)

        keywords_list = self._split_keywords(keywords)
        if skills:
            keywords_list.extend(skills)
        if not keywords_list:
            meta_kw = soup.find("meta", attrs={"name": "keywords"})
            if meta_kw and meta_kw.get("content"):
                keywords_list = self._split_keywords(meta_kw.get("content"))
        keywords = self._join_keywords(self._dedupe_preserve(keywords_list))

        if not topic:
            topic = self._extract_topic_from_payloads(embedded_payloads)
        if not topic and skills:
            topic = skills[0]
        if not topic and keywords:
            topic = self._pick_first_keyword(keywords)
        if not topic:
            topic = "General"
        if not keywords:
            keywords = topic

        # Fallback level detection from page content
        if not level:
            level = self._extract_level_from_html(soup)
        if not level:
            level = self._extract_level_from_embedded_json(embedded_payloads)
        if not level:
            level = "Unknown"

        if not title:
            return None

        short_description = description[:480] if description else None

        return CourseCreate(
            source_id=self.source_id,
            source_course_id=source_course_id,
            title=title,
            short_description=short_description,
            full_description=description,
            keywords=keywords,
            topic=topic,
            language=language,
            level=level,
            course_url=url,
            enrollment_url=url,
            image_url=self._normalize_image_url(ld_json.get("image")) if ld_json else None,
            last_updated_at_source=updated,
        )

    def _extract_json_ld_course(self, soup: BeautifulSoup) -> Optional[dict]:
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        for s in scripts:
            try:
                data = json.loads(s.get_text(strip=True))
            except Exception:
                continue

            candidates = []
            if isinstance(data, dict):
                candidates = [data]
                graph = data.get("@graph")
                if isinstance(graph, list):
                    candidates += [x for x in graph if isinstance(x, dict)]
            elif isinstance(data, list):
                candidates = [x for x in data if isinstance(x, dict)]

            for obj in candidates:
                t = obj.get("@type")
                if t == "Course" or (isinstance(t, list) and "Course" in t):
                    return obj

        return None

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
    def _get_text(self, url: str) -> str:
        r = self.session.get(url, timeout=self.timeout_s)
        r.raise_for_status()
        return self._decode_response_text(r)

    def _sleep(self) -> None:
        if self.sleep_ms > 0:
            time.sleep(self.sleep_ms / 1000.0)

    @staticmethod
    def _slug_from_url(url: str) -> str:
        p = urlparse(url)
        m = re.search(r"/learn/([^/]+)", p.path)
        return m.group(1) if m else ""

    @staticmethod
    def _parse_dt(v: Optional[str]) -> Optional[datetime]:
        if not v:
            return None
        try:
            return datetime.fromisoformat(v.replace("Z", "+00:00"))
        except Exception:
            return None

    @staticmethod
    def _normalize_keywords(v: object) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            values: List[str] = []
            for item in v:
                if item is None:
                    continue
                if isinstance(item, str):
                    values.append(item)
                    continue
                if isinstance(item, dict):
                    name = item.get("name") or item.get("@id") or item.get("label") or item.get("value")
                    if name:
                        values.append(str(name))
                        continue
                values.append(str(item))
            return ",".join(values) if values else None
        if isinstance(v, dict):
            name = v.get("name") or v.get("@id") or v.get("label") or v.get("value")
            return str(name) if name else None
        return str(v)

    @staticmethod
    def _split_keywords(v: Optional[str]) -> List[str]:
        if not v:
            return []
        return [part.strip() for part in v.split(",") if part and part.strip()]

    @staticmethod
    def _dedupe_preserve(values: List[str]) -> List[str]:
        seen = set()
        out: List[str] = []
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            key = cleaned.lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cleaned)
        return out

    @staticmethod
    def _join_keywords(values: List[str], max_len: int = 500) -> Optional[str]:
        if not values:
            return None
        out: List[str] = []
        total = 0
        for value in values:
            cleaned = value.strip()
            if not cleaned:
                continue
            sep = ", " if out else ""
            if total + len(sep) + len(cleaned) > max_len:
                break
            out.append(cleaned)
            total += len(sep) + len(cleaned)
        return ", ".join(out) if out else None

    @staticmethod
    def _pick_first_keyword(keywords: Optional[str]) -> Optional[str]:
        if not keywords:
            return None
        first = keywords.split(",", 1)[0].strip()
        return first if first else None

    @staticmethod
    def _normalize_level(value: object) -> Optional[str]:
        if value is None:
            return None
        if isinstance(value, str):
            return CourseraConnector._normalize_level_value(value)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    normalized = CourseraConnector._normalize_level_value(item)
                    if normalized:
                        return normalized
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("value")
                    if isinstance(name, str):
                        normalized = CourseraConnector._normalize_level_value(name)
                        if normalized:
                            return normalized
            return None
        if isinstance(value, dict):
            name = value.get("name") or value.get("value") or value.get("level")
            if isinstance(name, str):
                return CourseraConnector._normalize_level_value(name)
        return None

    @staticmethod
    def _normalize_level_value(value: str) -> Optional[str]:
        text = value.strip().lower()
        if not text:
            return None
        if "beginner" in text or "introductory" in text:
            return "Beginner"
        if "intermediate" in text:
            return "Intermediate"
        if "advanced" in text:
            return "Advanced"
        if "mixed" in text:
            return "Mixed"
        if "all levels" in text or "all level" in text:
            return "All Levels"
        return None

    @staticmethod
    def _normalize_image_url(v: object) -> Optional[str]:
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, list):
            for item in v:
                if isinstance(item, str):
                    return item
        if isinstance(v, dict):
            u = v.get("url") or v.get("@id")
            if isinstance(u, str):
                return u
        return None

    @staticmethod
    def _decode_response_text(response: requests.Response) -> str:
        encoding = response.encoding
        if not encoding:
            encoding = response.apparent_encoding
        if not encoding or encoding.lower() in {"iso-8859-1", "latin-1", "cp1252"}:
            encoding = "utf-8"
        return response.content.decode(encoding, errors="replace")

    @staticmethod
    def _normalize_language(lang: Optional[str]) -> Optional[str]:
        """Normalize language codes (e.g., 'en-US' -> 'en', 'zh-TW' -> 'zh')."""
        if not lang:
            return None
        lang = lang.strip()
        if not lang:
            return None
        # Return full code for important variants, otherwise base language
        # Keep codes like zh-TW, zh-CN, pt-BR distinct
        return lang.lower()

    # Map of common language names to ISO codes
    LANGUAGE_NAME_TO_CODE = {
        "english": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "portuguese": "pt",
        "chinese": "zh",
        "japanese": "ja",
        "korean": "ko",
        "russian": "ru",
        "arabic": "ar",
        "italian": "it",
        "dutch": "nl",
        "polish": "pl",
        "turkish": "tr",
        "vietnamese": "vi",
        "thai": "th",
        "indonesian": "id",
        "hindi": "hi",
        "bengali": "bn",
        "ukrainian": "uk",
        "greek": "el",
        "hebrew": "he",
        "persian": "fa",
        "swedish": "sv",
        "danish": "da",
        "norwegian": "no",
        "finnish": "fi",
        "czech": "cs",
        "hungarian": "hu",
        "romanian": "ro",
        "catalan": "ca",
        "tamil": "ta",
        "telugu": "te",
        "marathi": "mr",
        "gujarati": "gu",
        "kannada": "kn",
        "malayalam": "ml",
        "punjabi": "pa",
        "urdu": "ur",
        "swahili": "sw",
        "malay": "ms",
        "filipino": "fil",
        "tagalog": "tl",
        # Chinese variants
        "mandarin": "zh",
        "cantonese": "zh-yue",
        "traditional chinese": "zh-tw",
        "simplified chinese": "zh-cn",
        # Portuguese variants
        "brazilian portuguese": "pt-br",
        # Spanish variants  
        "latin american spanish": "es-419",
    }

    SKILL_HEADING_RE = re.compile(
        r"skills?\s+(?:you'?ll|you will)\s+gain|skills?\s+you\s+acquire",
        re.I,
    )
    SKILL_KEY_RE = re.compile(r"skills?(gained|gain|list)?", re.I)
    TOPIC_KEY_RE = re.compile(r"(topic|subject|category|domain|discipline|field)", re.I)
    LEVEL_KEY_RE = re.compile(r"(difficulty|level)", re.I)
    MAX_SKILL_LEN = 80

    def _extract_language_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract course language from Coursera page content (not UI language)."""
        
        # 1. Look for "Taught in [Language]" pattern in the page
        page_text = soup.get_text(separator=" ")
        
        # Pattern: "Taught in English", "Taught in Spanish", etc.
        taught_match = re.search(r"(?:taught|available)\s+in\s+([A-Za-z]+(?:\s+[A-Za-z]+)?)", page_text, re.I)
        if taught_match:
            lang_name = taught_match.group(1).lower().strip()
            if lang_name in self.LANGUAGE_NAME_TO_CODE:
                return self.LANGUAGE_NAME_TO_CODE[lang_name]
        
        # 2. Look for language in course metadata elements
        # Coursera often has elements with data-e2e or specific classes for language
        for elem in soup.find_all(attrs={"data-e2e": re.compile(r"language", re.I)}):
            text = elem.get_text(strip=True).lower()
            for lang_name, code in self.LANGUAGE_NAME_TO_CODE.items():
                if lang_name in text:
                    return code
        
        # 3. Look for language in "About" or metadata sections
        for elem in soup.find_all(["div", "span", "p"], class_=re.compile(r"language|locale", re.I)):
            text = elem.get_text(strip=True).lower()
            for lang_name, code in self.LANGUAGE_NAME_TO_CODE.items():
                if lang_name in text:
                    return code
        
        # 4. Look for "Language: [X]" pattern
        lang_pattern = re.search(r"language[:\s]+([A-Za-z]+(?:\s+[A-Za-z]+)?)", page_text, re.I)
        if lang_pattern:
            lang_name = lang_pattern.group(1).lower().strip()
            if lang_name in self.LANGUAGE_NAME_TO_CODE:
                return self.LANGUAGE_NAME_TO_CODE[lang_name]
        
        # Don't fallback to HTML lang - that's the UI language, not course language
        return None

    def _extract_embedded_json_payloads(self, soup: BeautifulSoup) -> List[object]:
        payloads: List[object] = []
        for script in soup.find_all("script"):
            if script.get("type") == "application/ld+json":
                continue
            text = script.string or script.get_text()
            if not text:
                continue
            text = text.strip()
            if not text:
                continue
            if script.get("id") == "__NEXT_DATA__" or script.get("type") == "application/json":
                if text.startswith("{") or text.startswith("["):
                    try:
                        payloads.append(json.loads(text))
                        continue
                    except Exception:
                        pass
            for var_name in ("__APOLLO_STATE__", "__INITIAL_STATE__", "__PRELOADED_STATE__"):
                payload = self._extract_json_from_assignment(text, var_name)
                if payload is not None:
                    payloads.append(payload)
        return payloads

    @staticmethod
    def _extract_json_from_assignment(script_text: str, var_name: str) -> Optional[object]:
        idx = script_text.find(var_name)
        if idx == -1:
            return None
        eq_idx = script_text.find("=", idx)
        if eq_idx == -1:
            return None
        match = re.search(r"[{\[]", script_text[eq_idx:])
        if not match:
            return None
        raw = script_text[eq_idx + match.start():].lstrip()
        try:
            payload, _ = json.JSONDecoder().raw_decode(raw)
        except Exception:
            return None
        return payload

    @staticmethod
    def _extract_strings_from_value(value: object) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            out: List[str] = []
            for item in value:
                out.extend(CourseraConnector._extract_strings_from_value(item))
            return out
        if isinstance(value, dict):
            for key in ("name", "label", "title", "value", "slug"):
                val = value.get(key)
                if isinstance(val, str):
                    return [val]
            return []
        return []

    def _extract_strings_from_json_by_key(self, data: object, key_pattern) -> List[str]:
        results: List[str] = []

        def walk(node: object) -> None:
            if isinstance(node, dict):
                for key, value in node.items():
                    if key_pattern.search(str(key)):
                        results.extend(self._extract_strings_from_value(value))
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        return results

    def _extract_skills_from_page(
        self,
        soup: BeautifulSoup,
        ld_json: Optional[dict],
        embedded_payloads: List[object],
    ) -> List[str]:
        skills: List[str] = []
        if ld_json:
            skills.extend(self._extract_strings_from_json_by_key(ld_json, self.SKILL_KEY_RE))
        for payload in embedded_payloads:
            skills.extend(self._extract_strings_from_json_by_key(payload, self.SKILL_KEY_RE))
        skills.extend(self._extract_skills_from_html(soup))

        cleaned: List[str] = []
        for skill in skills:
            text = re.sub(r"\s+", " ", skill.strip())
            if not text:
                continue
            if self.SKILL_HEADING_RE.search(text):
                continue
            if len(text) > self.MAX_SKILL_LEN:
                continue
            cleaned.append(text)

        return self._dedupe_preserve(cleaned)

    def _extract_skills_from_html(self, soup: BeautifulSoup) -> List[str]:
        skills: List[str] = []
        for heading in soup.find_all(string=self.SKILL_HEADING_RE):
            container = heading.find_parent()
            if not container:
                continue
            section = container.find_parent(["section", "div"]) or container
            skills.extend(self._extract_skill_tokens(section))
            if skills:
                return skills

        for elem in soup.find_all(attrs={"data-e2e": re.compile(r"skill", re.I)}):
            skills.extend(self._extract_skill_tokens(elem))
        for elem in soup.find_all(attrs={"data-testid": re.compile(r"skill", re.I)}):
            skills.extend(self._extract_skill_tokens(elem))

        return skills

    @staticmethod
    def _extract_skill_tokens(root) -> List[str]:
        tokens: List[str] = []
        for tag in root.find_all(["a", "span", "li", "button"], recursive=True):
            text = tag.get_text(" ", strip=True)
            if text:
                tokens.append(text)
        return tokens

    def _extract_topic_from_payloads(self, payloads: List[object]) -> Optional[str]:
        candidates: List[str] = []
        for payload in payloads:
            candidates.extend(self._extract_strings_from_json_by_key(payload, self.TOPIC_KEY_RE))
        for candidate in self._dedupe_preserve(candidates):
            if candidate and len(candidate) <= 100:
                return candidate.strip()
        return None

    def _extract_level_from_embedded_json(self, payloads: List[object]) -> Optional[str]:
        for payload in payloads:
            candidates = self._extract_strings_from_json_by_key(payload, self.LEVEL_KEY_RE)
            for candidate in candidates:
                normalized = self._normalize_level_value(candidate)
                if normalized:
                    return normalized
        return None

    def _extract_level_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract course level from page content."""
        # Look for level indicators in the page text
        page_text = soup.get_text(separator=" ").lower()

        # Common level patterns on Coursera
        level_patterns = [
            (r"\bbeginner\s*level\b", "Beginner"),
            (r"\bintermediate\s*level\b", "Intermediate"),
            (r"\badvanced\s*level\b", "Advanced"),
            (r"\bmixed\s*level\b", "Mixed"),
            (r"\ball\s*levels?\b", "All Levels"),
            # Without "level" suffix
            (r"\b(suitable\s+for\s+)?beginners?\b", "Beginner"),
        ]

        for pattern, level in level_patterns:
            if re.search(pattern, page_text):
                return level

        # Look for structured data in specific elements (Coursera often has difficulty badges)
        for elem in soup.find_all(["span", "div", "p"], class_=re.compile(r"level|difficulty", re.I)):
            text = elem.get_text(strip=True).lower()
            if "beginner" in text:
                return "Beginner"
            if "intermediate" in text:
                return "Intermediate"
            if "advanced" in text:
                return "Advanced"
            if "mixed" in text:
                return "Mixed"

        return None
