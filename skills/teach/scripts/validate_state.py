from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_FILES = ("GOALS.md", "RESOURCES.md", "LESSONS.md", "PROGRESS.md")
ARTIFACT_RE = re.compile(r"<!--\s*teach:artifact\s+([^>]*?)-->")
MARKER_RE = re.compile(r"<!--\s*teach:([a-z-]+)\s+([^>]*?)-->")
ATTR_RE = re.compile(r'([A-Za-z][A-Za-z0-9_-]*)\s*=\s*("[^"]*"|\'[^\']*\'|[^\s]+)')
FIELD_RE = re.compile(r"^- ([^:]+):\s*(.+?)\s*$", re.M)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
CITATION_RE = re.compile(r"\[(R-\d{3})\]")
ID_RE = re.compile(r"^(R|H|L|S)-(\d{3})$")
HREF_RE = re.compile(r'href="(https://[^"]+)"')
QUIZ_RE = re.compile(r"^(\d+)/(\d+)$")
PLACEHOLDER_RE = re.compile(r"\b(TODO|FIXME|TBD)\b|\bplaceholder\b")
INJECTION_RE = re.compile(
    r"ignore previous|system prompt|developer prompt|<\|im_start\|>|"
    r"you are now|exfiltrate|send to|rm -rf|\bcurl\b|\bwget\b|"
    r"fetch\(|XMLHttpRequest|javascript:|onerror=",
    re.I,
)
EVENT_RE = re.compile(r"\son[a-z]+\s*=", re.I)
FORBIDDEN_HTML = (
    "<script src", "<link", "@import", "fetch(", "XMLHttpRequest", "eval(",
    "document.write", "<iframe", "<form", "javascript:", "srcdoc", "innerHTML",
)
CSP_TOKENS = ("default-src 'none'", "connect-src 'none'", "script-src 'unsafe-inline'")
SHORTENERS = ("bit.ly", "tinyurl.com", "t.co", "goo.gl", "is.gd")
ALLOWED_STATUS = ("verified", "needs-review", "quarantined")
ALLOWED_TYPES = (
    "official-docs", "spec", "rfc", "paper", "source-code", "institutional", "book", "other",
)
GOAL_FIELDS = (
    "Topic", "Goal", "Scope", "Out of Scope", "Language", "Level",
    "Minutes per Session", "Allowed Domains", "Created",
)
SOURCE_FIELDS = (
    "Title", "URL", "Type", "Version", "Domain", "Tool", "Accessed", "Claims", "Excerpt", "Status",
)
SESSION_FIELDS = ("Objective", "Outcome", "Next")
SESSION_STATUS = ("completed", "review", "blocked")


@dataclass
class Issue:
    code: str
    message: str
    location: str = ""


@dataclass
class Report:
    errors: list[Issue] = field(default_factory=list)
    warnings: list[Issue] = field(default_factory=list)
    strict: bool = False

    def error(self, code: str, message: str, location: str = "") -> None:
        self.errors.append(Issue(code, message, location))

    def warning(self, code: str, message: str, location: str = "") -> None:
        self.warnings.append(Issue(code, message, location))

    @property
    def ok(self) -> bool:
        return not self.errors and not (self.strict and self.warnings)

    def to_dict(self, path: str = "") -> dict:
        return {
            "path": path,
            "status": "PASS" if self.ok else "FAIL",
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
        }


def parse_attributes(fragment: str) -> dict[str, str]:
    attributes: dict[str, str] = {}
    for match in ATTR_RE.finditer(fragment):
        attributes[match.group(1)] = match.group(2).strip("\"'")
    return attributes


def markers_of(text: str, kind: str) -> list[dict]:
    records = []
    for match in MARKER_RE.finditer(text):
        if match.group(1) == kind:
            records.append({
                "attributes": parse_attributes(match.group(2)),
                "start": match.start(),
                "end": match.end(),
            })
    return records


def parse_fields(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for match in FIELD_RE.finditer(text):
        key = match.group(1).strip()
        if key not in result:
            result[key] = match.group(2).strip()
    return result


def bounded_body(text: str, record: dict) -> str:
    following = [match.start() for match in MARKER_RE.finditer(text) if match.start() > record["start"]]
    end = min(following) if following else len(text)
    return text[record["end"]:end]


def check_artifact(text: str, kind: str, location: str, report: Report) -> None:
    markers = ARTIFACT_RE.findall(text)
    if len(markers) != 1:
        report.error("artifact-marker", f"Expected one teach:artifact marker in {location}.", location)
        return
    attributes = parse_attributes(markers[0])
    if attributes.get("type") != kind or attributes.get("version") != "1":
        report.error("artifact-marker", f"Artifact marker must be type={kind} version=1.", location)


def check_sequence(records: list[dict], prefix: str, code: str, report: Report) -> list[str]:
    ids: list[str] = []
    for index, record in enumerate(records, start=1):
        identifier = record["attributes"].get("id", "")
        if not ID_RE.fullmatch(identifier) or not identifier.startswith(prefix) or int(identifier[2:]) != index:
            report.error(code, f"Expected {prefix}-{index:03d}, found {identifier}.", identifier or code)
        ids.append(identifier)
    return ids


def scan_text(text: str, location: str, report: Report) -> None:
    if PLACEHOLDER_RE.search(text):
        report.error("placeholder", f"Unfinished content in {location}.", location)
    if INJECTION_RE.search(text):
        report.error("injection-pattern", f"Instruction-like content in {location}.", location)


def domain_allowed(host: str, allowed: list[str]) -> bool:
    return any(host == domain or host.endswith("." + domain) for domain in allowed)


def validate_goals(text: str, report: Report) -> tuple[str, list[str]]:
    check_artifact(text, "goals", "GOALS.md", report)
    fields = parse_fields(text)
    for name in GOAL_FIELDS:
        if not fields.get(name):
            report.error("missing-goal-field", f"GOALS.md needs {name}.", name)
    scan_text(text, "GOALS.md", report)
    language = fields.get("Language", "")
    allowed = [value.strip().lower() for value in fields.get("Allowed Domains", "").split(",") if value.strip()]
    if not DATE_RE.fullmatch(fields.get("Created", "")):
        report.error("invalid-date", "Created must use YYYY-MM-DD.", "Created")
    return language, allowed


def validate_resources(text: str, allowed: list[str], report: Report) -> list[dict]:
    check_artifact(text, "resources", "RESOURCES.md", report)
    scan_text(text, "RESOURCES.md", report)
    records = markers_of(text, "source")
    check_sequence(records, "R", "source-sequence", report)
    sources: list[dict] = []
    for record in records:
        body = bounded_body(text, record)
        fields = parse_fields(body)
        identifier = record["attributes"].get("id", "")
        for name in SOURCE_FIELDS:
            if not fields.get(name):
                report.error("missing-source-field", f"Source {identifier} needs {name}.", identifier)
        url = fields.get("URL", "")
        if not url.startswith("https://"):
            report.error("insecure-url", f"Source {identifier} must use HTTPS.", identifier)
        host = urlparse(url).hostname or ""
        if host in SHORTENERS:
            report.error("shortener-url", f"Source {identifier} must use a canonical URL.", identifier)
        if host and host != fields.get("Domain", ""):
            report.error("domain-mismatch", f"Source {identifier} domain does not match its URL.", identifier)
        if not domain_allowed(host, allowed):
            report.error("disallowed-domain", f"Source {identifier} domain is not allowed.", identifier)
        if not DATE_RE.fullmatch(fields.get("Accessed", "")):
            report.error("invalid-date", f"Source {identifier} needs a valid access date.", identifier)
        status = fields.get("Status", "")
        if status not in ALLOWED_STATUS:
            report.error("invalid-source-status", f"Invalid source status: {status}.", identifier)
        if fields.get("Type", "") not in ALLOWED_TYPES:
            report.error("invalid-source-type", f"Invalid source type: {fields.get('Type', '')}.", identifier)
        if status != record["attributes"].get("status", ""):
            report.error("status-mismatch", f"Source {identifier} marker and Status field disagree.", identifier)
        if INJECTION_RE.search(body):
            report.error("injection-pattern", f"Source {identifier} contains instruction-like text.", identifier)
        sources.append({"id": identifier, "url": url, "status": status, "attributes": record["attributes"]})

    history = markers_of(text, "history")
    check_sequence(history, "H", "history-sequence", report)
    history_ids: set[str] = set()
    for record in history:
        identifier = record["attributes"].get("id", "")
        history_ids.add(identifier)
        fields = parse_fields(bounded_body(text, record))
        source = record["attributes"].get("source", "")
        if source not in {item["id"] for item in sources}:
            report.error("history-source", f"History {identifier} references an unknown source.", identifier)
        if not DATE_RE.fullmatch(record["attributes"].get("date", "")):
            report.error("invalid-date", f"History {identifier} needs a valid date.", identifier)
        if not record["attributes"].get("tool"):
            report.error("missing-history-field", f"History {identifier} needs a tool.", identifier)
        if record["attributes"].get("result", "") not in ALLOWED_STATUS:
            report.error("invalid-history-result", f"History {identifier} has an invalid result.", identifier)
        for name in ("Evidence", "Result"):
            if not fields.get(name):
                report.error("missing-history-field", f"History {identifier} needs {name}.", identifier)

    for source in sources:
        if source["status"] == "verified" and source["id"] not in {
            record["attributes"].get("source", "") for record in history
        }:
            report.warning("missing-history", f"Source {source['id']} has no verification history.", source["id"])
    return sources


def validate_lessons(text: str, root: Path, sources: list[dict], report: Report) -> list[dict]:
    check_artifact(text, "lessons", "LESSONS.md", report)
    scan_text(text, "LESSONS.md", report)
    records = markers_of(text, "lesson")
    check_sequence(records, "L", "lesson-sequence", report)
    lessons: list[dict] = []
    known_sources = {source["id"] for source in sources}
    for record in records:
        attributes = record["attributes"]
        identifier = attributes.get("id", "")
        fields = parse_fields(bounded_body(text, record))
        if not fields.get("Summary"):
            report.error("missing-lesson-field", f"Lesson {identifier} needs Summary.", identifier)
        relative = attributes.get("file", "")
        if not relative or not (root / relative).is_file():
            report.error("missing-lesson-file", f"Lesson {identifier} file is missing.", identifier)
        minutes = attributes.get("minutes", "")
        quiz = attributes.get("quiz", "")
        audio = attributes.get("audio", "")
        if not minutes.isdigit() or int(minutes) < 1:
            report.error("invalid-minutes", f"Lesson {identifier} needs positive minutes.", identifier)
        if not quiz.isdigit() or int(quiz) < 3:
            report.error("invalid-quiz", f"Lesson {identifier} needs at least three questions.", identifier)
        if audio not in ("true", "false"):
            report.error("invalid-audio", f"Lesson {identifier} audio must be true or false.", identifier)
        if audio == "false" and not fields.get("Audio Reason"):
            report.error("missing-audio-reason", f"Lesson {identifier} needs an audio reason.", identifier)
        referenced = [value.strip() for value in attributes.get("sources", "").split(",") if value.strip()]
        for source_id in referenced:
            if source_id not in known_sources:
                report.error("citation-unresolved", f"Lesson {identifier} cites unknown {source_id}.", identifier)
        lessons.append({
            "id": identifier, "attributes": attributes, "sources": set(referenced),
            "minutes": minutes, "quiz": quiz, "audio": audio,
        })
    return lessons


def validate_progress(text: str, lessons: list[dict], report: Report) -> None:
    check_artifact(text, "progress", "PROGRESS.md", report)
    scan_text(text, "PROGRESS.md", report)
    records = markers_of(text, "session")
    check_sequence(records, "S", "session-sequence", report)
    known = {lesson["id"] for lesson in lessons}
    for record in records:
        attributes = record["attributes"]
        identifier = attributes.get("id", "")
        fields = parse_fields(bounded_body(text, record))
        for name in SESSION_FIELDS:
            if not fields.get(name):
                report.error("missing-session-field", f"Session {identifier} needs {name}.", identifier)
        if not DATE_RE.fullmatch(attributes.get("date", "")):
            report.error("invalid-date", f"Session {identifier} needs a valid date.", identifier)
        if attributes.get("lesson", "") not in known:
            report.error("session-lesson", f"Session {identifier} references an unknown lesson.", identifier)
        match = QUIZ_RE.fullmatch(attributes.get("quiz", ""))
        if not match or int(match.group(1)) > int(match.group(2)):
            report.error("invalid-session-quiz", f"Session {identifier} quiz must be A/B with A at most B.", identifier)
        if attributes.get("status", "") not in SESSION_STATUS:
            report.error("invalid-session-status", f"Session {identifier} has an invalid status.", identifier)


def validate_html(lesson: dict, root: Path, language: str, sources: list[dict], report: Report) -> None:
    relative = lesson["attributes"].get("file", "")
    path = root / relative
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    markers = markers_of(text, "lesson-html")
    if len(markers) != 1:
        report.error("lesson-html-marker", f"Exactly one lesson marker is required in {relative}.", relative)
        return
    attributes = markers[0]["attributes"]
    if attributes.get("id") != lesson["id"]:
        report.error("lesson-id-mismatch", f"HTML marker does not match {lesson['id']}.", relative)
    html_lang = re.search(r"<html[^>]*\blang=\"([^\"]+)\"", text)
    if attributes.get("lang") != language or not html_lang or html_lang.group(1) != language:
        report.error("language-mismatch", f"Lesson language must be {language}.", relative)
    if attributes.get("sources", "") != ",".join(sorted(lesson["sources"])):
        report.error("source-list-mismatch", f"HTML marker sources do not match the index for {lesson['id']}.", relative)
    if attributes.get("quiz") != lesson["quiz"] or attributes.get("audio") != lesson["audio"]:
        report.error("lesson-attribute-mismatch", f"HTML marker quiz or audio differs from the index for {lesson['id']}.", relative)

    cited = set(CITATION_RE.findall(text))
    known = {source["id"] for source in sources}
    if not cited.issubset(known) or cited != lesson["sources"]:
        report.error("citation-unresolved", f"Citations in {relative} do not match registered sources.", relative)
    source_by_id = {source["id"]: source for source in sources}
    for identifier in cited & known:
        if source_by_id[identifier]["status"] == "quarantined":
            report.error("quarantined-citation", f"Lesson {relative} cites quarantined {identifier}.", relative)
        if source_by_id[identifier]["status"] == "needs-review":
            report.warning("needs-review-source", f"Lesson {relative} cites {identifier} pending review.", relative)
    for href in HREF_RE.findall(text):
        if href not in {source["url"] for source in sources if source["id"] in cited}:
            report.error("unverified-link", f"Lesson {relative} links to an unregistered URL.", relative)

    if not all(token in text for token in CSP_TOKENS):
        report.error("unsafe-html", f"Lesson {relative} needs a restrictive CSP.", relative)
    if any(token in text for token in FORBIDDEN_HTML) or EVENT_RE.search(text):
        report.error("unsafe-html", f"Lesson {relative} contains forbidden HTML or script.", relative)
    if text.count('class="question"') != int(lesson["quiz"] or 0):
        report.error("quiz-count", f"Lesson {relative} question count differs from its marker.", relative)
    if lesson["audio"] == "true":
        if "speechSynthesis" not in text or 'id="transcript"' not in text:
            report.error("audio-missing", f"Lesson {relative} needs speechSynthesis and a transcript.", relative)
    elif "speechSynthesis" in text:
        report.error("audio-mismatch", f"Lesson {relative} declares audio=false but has narration.", relative)
    if PLACEHOLDER_RE.search(text):
        report.error("placeholder", f"Lesson {relative} contains unfinished content.", relative)


def validate_state(root: Path, report: Report | None = None, strict: bool = False) -> Report:
    report = report if report is not None else Report()
    report.strict = strict
    root = Path(root)
    if not root.is_dir():
        report.error("missing-state-dir", f"Study directory not found: {root}.", str(root))
        return report
    for name in REQUIRED_FILES:
        path = root / name
        if not path.is_file():
            report.error("missing-state-file", f"Required state file is missing: {name}.", name)
        elif not path.read_text(encoding="utf-8").strip():
            report.error("empty-state-file", f"Required state file is empty: {name}.", name)
    if report.errors:
        return report

    texts = {name: (root / name).read_text(encoding="utf-8") for name in REQUIRED_FILES}
    language, allowed = validate_goals(texts["GOALS.md"], report)
    sources = validate_resources(texts["RESOURCES.md"], allowed, report)
    lessons = validate_lessons(texts["LESSONS.md"], root, sources, report)
    validate_progress(texts["PROGRESS.md"], lessons, report)
    for lesson in lessons:
        validate_html(lesson, root, language, sources, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_state.py",
        description="Validate a persistent study directory produced by the teach skill.",
    )
    parser.add_argument("dir", nargs="?", default=".", help="Study directory.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    return parser


def print_report(path: str, report: Report) -> None:
    print(f"{'PASS' if report.ok else 'FAIL'}: {path}")
    for issue in report.errors:
        location = f" ({issue.location})" if issue.location else ""
        print(f"[ERROR] {issue.code}: {issue.message}{location}")
    for issue in report.warnings:
        location = f" ({issue.location})" if issue.location else ""
        print(f"[WARN] {issue.code}: {issue.message}{location}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_state(Path(args.dir), strict=args.strict)
    if args.json:
        print(json.dumps(report.to_dict(args.dir), indent=2))
    else:
        print_report(args.dir, report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
