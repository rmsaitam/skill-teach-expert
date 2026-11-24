from __future__ import annotations

import argparse
import datetime
import re
from pathlib import Path

DEFAULT_LANGUAGE = "en"
DEFAULT_MINUTES = 8
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DOMAIN_RE = re.compile(r"^[a-z0-9.-]+\.[a-z]{2,}$")

ENGLISH_TEXT = {
    "level": "beginner",
    "scope": "to be defined in the first session",
    "out_of_scope": "outside the topic",
    "scope_section": "The scope will be refined in the first session.",
    "roadmap": "1. First concept to verify.",
    "resources": "No verified sources yet. Record each source with R-NNN before teaching.\n",
    "lessons": "No lessons recorded yet. Each lesson receives an L-NNN ID.\n",
    "progress": "No sessions recorded yet. Each session receives an S-NNN ID.\n",
}

PORTUGUESE_TEXT = {
    "level": "iniciante",
    "scope": "a definir na primeira sessão",
    "out_of_scope": "fora do tema",
    "scope_section": "O escopo será refinado na primeira sessão.",
    "roadmap": "1. Primeiro conceito a verificar.",
    "resources": "Nenhuma fonte verificada ainda. Registre cada fonte com R-NNN antes de ensinar.\n",
    "lessons": "Nenhuma lição registrada ainda. Cada lição receberá um ID L-NNN.\n",
    "progress": "Nenhuma sessão registrada ainda. Cada sessão receberá um ID S-NNN.\n",
}


def clean(value: str) -> str:
    text = re.sub(r"<!--.*?-->", "", str(value), flags=re.S)
    text = re.sub(r"<[^>]*>", "", text)
    return re.sub(r"\s+", " ", text).strip()


def language_text(language: str) -> dict[str, str]:
    if str(language).lower().startswith("pt"):
        return PORTUGUESE_TEXT
    return ENGLISH_TEXT


def normalize_domains(value: str) -> list[str]:
    domains: list[str] = []
    for part in str(value).split(","):
        domain = part.strip().lower()
        if DOMAIN_RE.fullmatch(domain) and domain not in domains:
            domains.append(domain)
    return domains


def today_value(value: str | None) -> str:
    return value or datetime.date.today().isoformat()


def build_goals(
    language: str,
    topic: str,
    goal: str,
    level: str,
    minutes: int,
    scope: str,
    out_of_scope: str,
    domains: list[str],
    today: str,
) -> str:
    text = language_text(language)
    lines = [
        "<!-- teach:artifact type=goals version=1 -->",
        f"- Topic: {clean(topic)}",
        f"- Goal: {clean(goal) or clean(topic)}",
        f"- Scope: {clean(scope) or text['scope']}",
        f"- Out of Scope: {clean(out_of_scope) or text['out_of_scope']}",
        f"- Language: {clean(language)}",
        f"- Level: {clean(level) or text['level']}",
        f"- Minutes per Session: {minutes}",
        f"- Allowed Domains: {', '.join(domains)}",
        f"- Created: {today}",
        "",
        "<!-- teach:section id=goal -->",
        clean(goal) or clean(topic),
        "",
        "<!-- teach:section id=scope -->",
        clean(scope) or text["scope_section"],
        "",
        "<!-- teach:section id=roadmap -->",
        text["roadmap"],
    ]
    return "\n".join(lines) + "\n"


def build_resources(language: str) -> str:
    return (
        "<!-- teach:artifact type=resources version=1 -->\n\n"
        + language_text(language)["resources"]
    )


def build_lessons(language: str) -> str:
    return (
        "<!-- teach:artifact type=lessons version=1 -->\n\n"
        + language_text(language)["lessons"]
    )


def build_progress(language: str) -> str:
    return (
        "<!-- teach:artifact type=progress version=1 -->\n\n"
        + language_text(language)["progress"]
    )


def init_study(
    root: Path,
    language: str = DEFAULT_LANGUAGE,
    topic: str = "",
    goal: str = "",
    level: str = "",
    minutes: int = DEFAULT_MINUTES,
    scope: str = "",
    out_of_scope: str = "",
    allowed_domains: str = "",
    today: str | None = None,
) -> list[Path]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    (root / "lessons").mkdir(exist_ok=True)
    date = today_value(today)
    files = {
        root / "GOALS.md": build_goals(
            language, topic, goal, level, minutes, scope, out_of_scope,
            normalize_domains(allowed_domains), date,
        ),
        root / "RESOURCES.md": build_resources(language),
        root / "LESSONS.md": build_lessons(language),
        root / "PROGRESS.md": build_progress(language),
    }
    created: list[Path] = []
    for path, content in files.items():
        if path.exists():
            continue
        path.write_text(content, encoding="utf-8")
        created.append(path)
    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="init_study.py",
        description="Create the persistent study state files in a study directory.",
    )
    parser.add_argument("dir", help="Study directory.")
    parser.add_argument(
        "--language",
        default=DEFAULT_LANGUAGE,
        help="Language of all lessons and generated state prose.",
    )
    parser.add_argument("--topic", required=True, help="Main study topic.")
    parser.add_argument("--goal", default="", help="Concrete learning goal.")
    parser.add_argument("--level", default="", help="Learner level (defaults by language).")
    parser.add_argument("--minutes", type=int, default=DEFAULT_MINUTES, help="Minutes per session.")
    parser.add_argument("--scope", default="", help="Topics included in the study.")
    parser.add_argument("--out-of-scope", default="", help="Topics excluded from the study.")
    parser.add_argument("--allowed-domains", default="", help="Comma-separated trusted domains.")
    parser.add_argument("--today", default=None, help="Creation date in YYYY-MM-DD.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.today and not DATE_RE.fullmatch(args.today):
        print("ERROR: --today must use YYYY-MM-DD.")
        return 2
    if args.minutes < 1:
        print("ERROR: --minutes must be positive.")
        return 2
    created = init_study(
        Path(args.dir),
        language=args.language,
        topic=args.topic,
        goal=args.goal,
        level=args.level,
        minutes=args.minutes,
        scope=args.scope,
        out_of_scope=args.out_of_scope,
        allowed_domains=args.allowed_domains,
        today=args.today,
    )
    if created:
        for path in created:
            print(f"created: {path.name}")
    else:
        print("no files created")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
