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

from backend.app.connectors.base import BaseConnector
from backend.app.schemas.course import CourseCreate


class MitOcwConnector(BaseConnector):
    TOPIC_HEADING_RE = re.compile(r"\btopics?\b", re.I)
    LEVEL_VALUE_RE = re.compile(
        r"\b(undergraduate|graduate|high school|non[-\s]?credit|postgraduate)\b",
        re.I,
    )
    MAX_TOPIC_LEN = 100

    def __init__(
        self,
        source_id: int,
        sitemap_index_url: Optional[str],
        sitemap_urls: List[str],
        max_urls: int,
        timeout_s: int,
        sleep_ms: int,
        max_retries: int,
    ) -> None:
        self.source_id = source_id
        self.sitemap_index_url = (sitemap_index_url or "").strip()
        self.sitemap_urls = [u.strip() for u in sitemap_urls if u and u.strip()]
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
        for url in urls:
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
        sitemap_queue: List[str] = []
        if self.sitemap_index_url:
            sitemap_queue.append(self.sitemap_index_url)
        sitemap_queue.extend(self.sitemap_urls)

        seen_sitemaps: Set[str] = set()
        found: Set[str] = set()
        out: List[str] = []

        ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

        while sitemap_queue:
            sitemap_url = sitemap_queue.pop(0)
            if sitemap_url in seen_sitemaps:
                continue
            seen_sitemaps.add(sitemap_url)

            xml = self._get_text(sitemap_url)
            root = etree.fromstring(xml.encode("utf-8"))

            sitemap_locs = root.xpath("//sm:sitemap/sm:loc/text()", namespaces=ns)
            if sitemap_locs:
                for loc in sitemap_locs:
                    if loc not in seen_sitemaps:
                        sitemap_queue.append(loc)
                continue

            url_locs = root.xpath("//sm:url/sm:loc/text()", namespaces=ns)
            for loc in url_locs:
                if not self._is_course_url(loc):
                    continue
                if loc in found:
                    continue
                found.add(loc)
                out.append(loc)
                if len(out) >= self.max_urls:
                    return out

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
        image_url = None
        topic = None
        topics: List[str] = []

        if ld_json:
            title = ld_json.get("name") or ld_json.get("headline")
            description = ld_json.get("description")
            language = self._normalize_language(
                ld_json.get("inLanguage") or ld_json.get("language")
            )
            keywords = self._normalize_keywords(
                ld_json.get("keywords") or ld_json.get("about")
            )
            level = self._normalize_level(ld_json.get("educationalLevel"))
            updated = self._parse_dt(
                ld_json.get("dateModified")
                or ld_json.get("datePublished")
                or ld_json.get("dateCreated")
            )
            image_url = self._normalize_image_url(
                ld_json.get("image") or ld_json.get("thumbnailUrl")
            )

        if not title:
            og = soup.find("meta", attrs={"property": "og:title"})
            title = og.get("content") if og else None
        if not title:
            h1 = soup.find("h1")
            title = h1.get_text(strip=True) if h1 else None

        if not description:
            meta = soup.find("meta", attrs={"name": "description"})
            description = meta.get("content") if meta else None

        if not image_url:
            og_img = soup.find("meta", attrs={"property": "og:image"})
            image_url = og_img.get("content") if og_img else None

        if not keywords:
            meta_kw = soup.find("meta", attrs={"name": "keywords"})
            keywords = meta_kw.get("content") if meta_kw else None

        topics = self._extract_topics_from_html(soup)
        keywords_list = self._split_keywords(keywords)
        if topics:
            keywords_list.extend(topics)
        keywords = self._join_keywords(self._dedupe_preserve(keywords_list))

        if topics:
            topic = topics[0]
        if not topic and keywords:
            topic = self._pick_first_keyword(keywords)
        if not topic:
            topic = "General"
        if not keywords:
            keywords = topic

        if not language:
            language = self._extract_language_from_html(soup)

        if not level:
            level = self._extract_level_from_html(soup)
        if not level:
            level = "Unknown"

        if not title:
            return None

        slug = self._slug_from_url(url)
        short_description = description[:480] if description else None

        return CourseCreate(
            source_id=self.source_id,
            source_course_id=slug or url,
            title=title,
            short_description=short_description,
            full_description=description,
            keywords=keywords,
            topic=topic,
            language=language,
            level=level,
            course_url=url,
            enrollment_url=url,
            image_url=image_url,
            last_updated_at_source=updated,
        )

    def _extract_json_ld_course(self, soup: BeautifulSoup) -> Optional[dict]:
        scripts = soup.find_all("script", attrs={"type": "application/ld+json"})
        fallback = None
        for s in scripts:
            try:
                data = json.loads(s.get_text(strip=True))
            except Exception:
                continue

            candidates: List[dict] = []
            if isinstance(data, dict):
                candidates = [data]
                graph = data.get("@graph")
                if isinstance(graph, list):
                    candidates += [x for x in graph if isinstance(x, dict)]
            elif isinstance(data, list):
                candidates = [x for x in data if isinstance(x, dict)]

            for obj in candidates:
                t = obj.get("@type")
                types = []
                if isinstance(t, list):
                    types = t
                elif t:
                    types = [t]
                if "Course" in types:
                    return obj
                if "CourseInstance" in types and fallback is None:
                    fallback = obj

        return fallback

    @retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(5))
    def _get_text(self, url: str) -> str:
        r = self.session.get(url, timeout=self.timeout_s)
        r.raise_for_status()
        return self._decode_response_text(r)

    def _sleep(self) -> None:
        if self.sleep_ms > 0:
            time.sleep(self.sleep_ms / 1000.0)

    @staticmethod
    def _is_course_url(url: str) -> bool:
        try:
            p = urlparse(url)
        except Exception:
            return False
        if p.netloc != "ocw.mit.edu":
            return False
        if not p.path.startswith("/courses/"):
            return False
        path = p.path.rstrip("/")
        tail = path[len("/courses/"):]
        if not tail or "/" in tail:
            return False
        return True

    @staticmethod
    def _slug_from_url(url: str) -> str:
        p = urlparse(url)
        if not p.path.startswith("/courses/"):
            return ""
        slug = p.path[len("/courses/"):].strip("/")
        if "/" in slug:
            return ""
        return slug

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
                    name = item.get("name") or item.get("@id")
                    if name:
                        values.append(str(name))
                        continue
                values.append(str(item))
            return ",".join(values) if values else None
        if isinstance(v, dict):
            name = v.get("name") or v.get("@id")
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
            return MitOcwConnector._normalize_level_value(value)
        if isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    normalized = MitOcwConnector._normalize_level_value(item)
                    if normalized:
                        return normalized
                elif isinstance(item, dict):
                    name = item.get("name") or item.get("value")
                    if isinstance(name, str):
                        normalized = MitOcwConnector._normalize_level_value(name)
                        if normalized:
                            return normalized
            return None
        if isinstance(value, dict):
            name = value.get("name") or value.get("value") or value.get("level")
            if isinstance(name, str):
                return MitOcwConnector._normalize_level_value(name)
        return None

    @staticmethod
    def _normalize_level_value(value: str) -> Optional[str]:
        text = value.strip().lower()
        if not text:
            return None
        if "undergraduate" in text:
            return "Beginner"
        if "high school" in text or "highschool" in text:
            return "Beginner"
        if "graduate" in text or "postgraduate" in text:
            return "Advanced"
        if "non-credit" in text or "non credit" in text or "noncredit" in text:
            return "All Levels"
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
                if isinstance(item, dict):
                    u = item.get("url") or item.get("@id")
                    if isinstance(u, str):
                        return u
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
        if not lang:
            return None
        lang = lang.strip()
        if not lang:
            return None
        return lang.lower()

    def _extract_language_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            lang = self._normalize_language(html_tag.get("lang"))
            if lang:
                return lang

        content_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
        if content_lang and content_lang.get("content"):
            lang = self._normalize_language(content_lang.get("content"))
            if lang:
                return lang

        dc_lang = soup.find("meta", attrs={"name": re.compile(r"dc\.language", re.I)})
        if dc_lang and dc_lang.get("content"):
            lang = self._normalize_language(dc_lang.get("content"))
            if lang:
                return lang

        og_locale = soup.find("meta", attrs={"property": "og:locale"})
        if og_locale and og_locale.get("content"):
            locale = og_locale.get("content", "").replace("_", "-")
            lang = self._normalize_language(locale)
            if lang:
                return lang

        return None

    def _extract_topics_from_html(self, soup: BeautifulSoup) -> List[str]:
        topics: List[str] = []
        for heading in soup.find_all(string=self.TOPIC_HEADING_RE):
            container = heading.find_parent()
            if not container:
                continue
            section = container.find_parent(["section", "div", "aside", "ul"]) or container
            topics.extend(self._extract_topic_tokens(section))
            if topics:
                break

        if not topics:
            for elem in soup.find_all(attrs={"class": re.compile(r"topic", re.I)}):
                topics.extend(self._extract_topic_tokens(elem))
            for elem in soup.find_all(attrs={"id": re.compile(r"topic", re.I)}):
                topics.extend(self._extract_topic_tokens(elem))

        cleaned: List[str] = []
        for topic in topics:
            text = re.sub(r"\s+", " ", topic.strip())
            if not text:
                continue
            if self.TOPIC_HEADING_RE.fullmatch(text):
                continue
            if len(text) > self.MAX_TOPIC_LEN:
                continue
            cleaned.append(text)

        return self._dedupe_preserve(cleaned)

    @staticmethod
    def _extract_topic_tokens(root) -> List[str]:
        tokens: List[str] = []
        for tag in root.find_all(["a", "li", "span", "button"], recursive=True):
            text = tag.get_text(" ", strip=True)
            if text:
                tokens.append(text)
        return tokens

    def _extract_level_from_html(self, soup: BeautifulSoup) -> Optional[str]:
        for elem in soup.find_all(attrs={"class": re.compile(r"level", re.I)}):
            normalized = self._normalize_level_value(elem.get_text(" ", strip=True))
            if normalized:
                return normalized
        for elem in soup.find_all(attrs={"id": re.compile(r"level", re.I)}):
            normalized = self._normalize_level_value(elem.get_text(" ", strip=True))
            if normalized:
                return normalized

        page_text = soup.get_text(separator=" ")
        label_match = re.search(
            r"\blevel\b[^A-Za-z0-9]{0,10}(undergraduate|graduate|high school|non[-\s]?credit|postgraduate)",
            page_text,
            re.I,
        )
        if label_match:
            return self._normalize_level_value(label_match.group(1))

        value_match = self.LEVEL_VALUE_RE.search(page_text)
        if value_match:
            return self._normalize_level_value(value_match.group(0))

        return None
