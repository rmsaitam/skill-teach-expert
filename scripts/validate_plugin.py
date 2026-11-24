from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

PLUGIN_NAME = "teach"
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?$")
BRAND_COLOR_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")
FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
LINK_RE = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")

SKILL_PATH = f"skills/{PLUGIN_NAME}/SKILL.md"
SKILL_DIR = f"skills/{PLUGIN_NAME}"

REQUIRED_FILES = (
    "plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".codex-plugin/plugin.json",
    ".cursor-plugin/plugin.json",
    ".cursor-plugin/marketplace.json",
    ".agents/plugins/marketplace.json",
    ".github/plugin/marketplace.json",
    ".github/workflows/ci.yml",
    "agents/openai.yaml",
    "assets/icon.svg",
    "assets/logo.svg",
    "commands/teach.md",
    SKILL_PATH,
    f"{SKILL_DIR}/references/source-policy.md",
    f"{SKILL_DIR}/references/authority-and-injection.md",
    f"{SKILL_DIR}/references/study-state.md",
    f"{SKILL_DIR}/references/lesson-authoring.md",
    f"{SKILL_DIR}/references/html-template.md",
    f"{SKILL_DIR}/references/quiz-and-audio.md",
    f"{SKILL_DIR}/references/adaptation-and-language.md",
    f"{SKILL_DIR}/references/validation-checklist.md",
    f"{SKILL_DIR}/scripts/init_study.py",
    f"{SKILL_DIR}/scripts/validate_state.py",
    "scripts/validate_plugin.py",
    "tests/conftest.py",
    "tests/test_init_study.py",
    "tests/test_validate_state.py",
    "tests/test_validate_plugin.py",
    "tests/fixtures/valid-study/GOALS.md",
    "tests/fixtures/valid-study/RESOURCES.md",
    "tests/fixtures/valid-study/LESSONS.md",
    "tests/fixtures/valid-study/PROGRESS.md",
    "tests/fixtures/valid-study/lessons/001-futures.html",
    "README.md",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
    ".gitignore",
)

SCAN_SUFFIXES = {".md", ".json", ".yaml", ".yml", ".toml"}
EXCLUDED_PARTS = {".git", ".pytest_cache", "__pycache__", ".venv", "tests", "fixtures"}

REQUIRED_SKILL_TOKENS = (
    "RESOURCES.md",
    "PROGRESS.md",
    "GOALS.md",
    "LESSONS.md",
    "init_study.py",
    "validate_state.py",
    "--dir",
    "Context7",
    "prompt-injection",
    "quarantined",
    "Allowed Domains",
    "Web Speech API",
    "speechSynthesis",
    "CSP",
    "quiz",
    "R-NNN",
    "H-NNN",
    "L-NNN",
    "S-NNN",
    "user's language",
)

COMMAND_TOKENS = {
    "teach.md": (
        PLUGIN_NAME,
        "init_study.py",
        "validate_state.py",
        "RESOURCES.md",
        "PROGRESS.md",
        "Context7",
        "prompt-injection",
        "Web Speech API",
        "--dir",
        "quiz",
        "quarantine",
    ),
}


class DuplicateKeyError(ValueError):
    pass


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

    def to_dict(self) -> dict:
        return {
            "status": "PASS" if self.ok else "FAIL",
            "errors": [issue.__dict__ for issue in self.errors],
            "warnings": [issue.__dict__ for issue in self.warnings],
        }


def unique_object(pairs: list[tuple[str, object]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(key)
        result[key] = value
    return result


def load_json(path: Path, report: Report) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_object)
    except DuplicateKeyError as exc:
        report.error("duplicate-json-key", f"Duplicate JSON key: {exc}.", str(path))
    except (json.JSONDecodeError, OSError) as exc:
        report.error("invalid-json", f"Cannot parse JSON: {exc}.", str(path))
    return None


def expected_version(root: Path, report: Report) -> str:
    path = root / ".claude-plugin" / "plugin.json"
    data = load_json(path, report)
    if data is None:
        return ""
    version = str(data.get("version", ""))
    if not SEMVER_RE.match(version):
        report.error("invalid-version", f"Invalid semantic version: {version}.", str(path))
    return version


def check_required_files(root: Path, report: Report) -> None:
    for name in REQUIRED_FILES:
        path = root / name
        if not path.is_file():
            report.error("missing-required-file", f"Required file is missing: {name}.", name)
        elif not path.read_text(encoding="utf-8").strip():
            report.error("empty-file", f"Required file is empty: {name}.", name)


def check_name(data: dict, report: Report, location: str) -> None:
    if data.get("name") != PLUGIN_NAME:
        report.error("plugin-name", f"Expected plugin name {PLUGIN_NAME}.", location)


def check_description(data: dict, report: Report, location: str, minimum: int = 30) -> None:
    if len(str(data.get("description", ""))) < minimum:
        report.error("weak-description", f"Description is too short in {location}.", location)


def check_version(data: dict, version: str, report: Report, location: str) -> None:
    if str(data.get("version", "")) != version:
        report.error("version-mismatch", f"Version does not match {version}.", location)


def check_root_manifest(root: Path, report: Report) -> None:
    path = root / "plugin.json"
    data = load_json(path, report)
    if data is None:
        return
    if "antigravity.google" not in str(data.get("$schema", "")):
        report.error("root-manifest-schema", "Root manifest must use the Antigravity schema.", str(path))
    if data.get("name") != PLUGIN_NAME:
        report.error("root-manifest-name", "Root manifest name is wrong.", str(path))
    allowed = {"$schema", "name", "description"}
    extra = set(data) - allowed
    if extra:
        report.error("root-manifest-extra-key", f"Unexpected root manifest keys: {sorted(extra)}.", str(path))
    check_description(data, report, str(path))


def check_claude(root: Path, report: Report, version: str) -> None:
    path = root / ".claude-plugin" / "plugin.json"
    data = load_json(path, report)
    if data is None:
        return
    check_name(data, report, str(path))
    check_version(data, version, report, str(path))
    check_description(data, report, str(path))
    if not data.get("author", {}).get("name"):
        report.error("missing-author", "Claude plugin manifest needs an author.", str(path))
    if data.get("license") != "MIT":
        report.error("missing-license", "Claude plugin manifest must declare MIT.", str(path))

    marketplace = root / ".claude-plugin" / "marketplace.json"
    data = load_json(marketplace, report)
    if data is None:
        return
    if "anthropic.com" not in str(data.get("$schema", "")):
        report.error("claude-marketplace-schema", "Claude marketplace needs the Anthropic schema.", str(marketplace))
    if not data.get("owner", {}).get("name"):
        report.error("missing-owner", "Claude marketplace needs an owner.", str(marketplace))
    plugins = data.get("plugins", [])
    if not plugins or plugins[0].get("name") != PLUGIN_NAME:
        report.error("marketplace-plugin-name", "Claude marketplace must list the plugin.", str(marketplace))


def check_interface(data: dict, report: Report, location: str) -> dict:
    interface = data.get("interface", {})
    if not isinstance(interface, dict):
        report.error("codex-interface", "Interface must be an object.", location)
        return {}
    for key in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
        if not interface.get(key):
            report.error(f"codex-{key}", f"Interface field is missing: {key}.", location)
    capabilities = interface.get("capabilities", [])
    if not isinstance(capabilities, list) or not capabilities:
        report.error("codex-capabilities", "Interface capabilities must be a non-empty list.", location)
    default_prompt = interface.get("defaultPrompt", [])
    if not isinstance(default_prompt, list) or not default_prompt or not all(
        isinstance(prompt, str) and prompt.strip() for prompt in default_prompt
    ):
        report.error("codex-default-prompt", "Interface needs a non-empty defaultPrompt list.", location)
    if not BRAND_COLOR_RE.match(str(interface.get("brandColor", ""))):
        report.error("codex-brand-color", "Interface brandColor must be a hex color.", location)
    if not isinstance(interface.get("screenshots"), list):
        report.error("codex-screenshots", "Interface screenshots must be a list.", location)
    return interface


def check_codex(root: Path, report: Report, version: str) -> None:
    path = root / ".codex-plugin" / "plugin.json"
    data = load_json(path, report)
    if data is None:
        return
    check_name(data, report, str(path))
    check_version(data, version, report, str(path))
    check_description(data, report, str(path))
    if data.get("skills") != "./skills/":
        report.error("codex-skills", "Codex manifest must expose ./skills/.", str(path))
    interface = check_interface(data, report, str(path))
    for key in ("composerIcon", "logo"):
        relative = str(interface.get(key, "")).lstrip("./")
        if not (root / relative).is_file():
            report.error("codex-asset", f"Codex interface asset is missing: {key}.", str(path))


def check_cursor(root: Path, report: Report, version: str) -> None:
    path = root / ".cursor-plugin" / "plugin.json"
    data = load_json(path, report)
    if data is None:
        return
    check_name(data, report, str(path))
    check_version(data, version, report, str(path))
    check_description(data, report, str(path))
    if data.get("skills") != "./skills/":
        report.error("cursor-skills", "Cursor manifest must expose ./skills/.", str(path))
    if data.get("commands") != "./commands/":
        report.error("cursor-commands", "Cursor manifest must expose ./commands/.", str(path))
    logo = str(data.get("logo", "")).lstrip("./")
    if not (root / logo).is_file():
        report.error("cursor-logo", "Cursor manifest logo is missing.", str(path))

    marketplace = root / ".cursor-plugin" / "marketplace.json"
    data = load_json(marketplace, report)
    if data is None:
        return
    if not data.get("owner", {}).get("name"):
        report.error("missing-owner", "Cursor marketplace needs an owner.", str(marketplace))
    plugins = data.get("plugins", [])
    if not plugins or plugins[0].get("name") != PLUGIN_NAME or plugins[0].get("source") != ".":
        report.error("marketplace-plugin-name", "Cursor marketplace entry is invalid.", str(marketplace))


def check_copilot(root: Path, report: Report, version: str) -> None:
    path = root / ".github" / "plugin" / "marketplace.json"
    data = load_json(path, report)
    if data is None:
        return
    if not data.get("owner", {}).get("name"):
        report.error("missing-owner", "Copilot marketplace needs an owner.", str(path))
    check_version(data.get("metadata", {}), version, report, str(path))
    plugins = data.get("plugins", [])
    if not plugins:
        report.error("marketplace-plugin-name", "Copilot marketplace has no plugin entry.", str(path))
        return
    check_version(plugins[0], version, report, str(path))
    if plugins[0].get("name") != PLUGIN_NAME:
        report.error("marketplace-plugin-name", "Copilot marketplace plugin name is wrong.", str(path))
    check_description(plugins[0], report, str(path))


def check_codex_marketplace(root: Path, report: Report) -> None:
    path = root / ".agents" / "plugins" / "marketplace.json"
    data = load_json(path, report)
    if data is None:
        return
    if not data.get("interface", {}).get("displayName"):
        report.error("agents-display-name", "Codex marketplace needs a display name.", str(path))
    plugins = data.get("plugins", [])
    if not plugins:
        report.error("marketplace-plugin-name", "Codex marketplace has no plugin entry.", str(path))
        return
    entry = plugins[0]
    if entry.get("name") != PLUGIN_NAME:
        report.error("marketplace-plugin-name", "Codex marketplace plugin name is wrong.", str(path))
    if entry.get("source", {}).get("source") != "local" or entry.get("source", {}).get("path") != "./":
        report.error("agents-source", "Codex marketplace source must be local ./", str(path))
    policy = entry.get("policy", {})
    if policy.get("installation") != "AVAILABLE" or policy.get("authentication") != "ON_INSTALL":
        report.error("agents-policy", "Codex marketplace policy is invalid.", str(path))


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        entry = re.match(r"^([A-Za-z][A-Za-z -]*):\s*(.+)$", line.strip())
        if entry:
            result[entry.group(1).strip()] = entry.group(2).strip().strip("'\"")
    return result


def check_relative_path(root: Path, target: Path, report: Report, location: str) -> bool:
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        report.error("path-escape", f"Path escapes the plugin root: {location}.", location)
        return False
    return True


def check_skill(root: Path, report: Report, version: str) -> None:
    path = root / SKILL_PATH
    text = path.read_text(encoding="utf-8")
    if not FRONTMATTER_RE.match(text):
        report.error("missing-frontmatter", "SKILL.md needs YAML frontmatter.", SKILL_PATH)
        return

    frontmatter = parse_frontmatter(text)
    if frontmatter.get("name") != PLUGIN_NAME:
        report.error("wrong-name", "SKILL.md name is wrong.", SKILL_PATH)
    if len(frontmatter.get("description", "")) < 80:
        report.error("weak-description", "SKILL.md description is too short.", SKILL_PATH)
    if frontmatter.get("license") != "MIT":
        report.error("missing-license", "SKILL.md must declare MIT.", SKILL_PATH)
    if frontmatter.get("version") != version:
        report.error("skill-version-mismatch", f"SKILL.md version must be {version}.", SKILL_PATH)
    if not frontmatter.get("author"):
        report.error("missing-author", "SKILL.md needs an author.", SKILL_PATH)

    skill_dir = root / SKILL_DIR
    for link in LINK_RE.findall(text):
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("/"):
            continue
        target = (skill_dir / link.split("#", 1)[0]).resolve()
        if not check_relative_path(root, target, report, link):
            continue
        if not target.exists():
            report.error("missing-reference", f"Local link target is missing: {link}.", link)

    for token in REQUIRED_SKILL_TOKENS:
        if token not in text:
            report.error("missing-skill-content", f"SKILL.md must mention {token}.", token)


def check_openai_yaml(root: Path, report: Report) -> None:
    path = root / "agents" / "openai.yaml"
    text = path.read_text(encoding="utf-8")
    for key in ("display_name", "short_description", "default_prompt"):
        if key not in text:
            report.error(f"missing-{key.replace('_', '-')}", f"agents/openai.yaml needs {key}.", str(path))
    if f"${PLUGIN_NAME}" not in text:
        report.error("missing-skill-reference", "agents/openai.yaml must reference the skill.", str(path))


def check_svg(root: Path, name: str, report: Report) -> None:
    path = root / name
    try:
        element = ET.parse(path).getroot()
    except ET.ParseError as exc:
        report.error("invalid-svg", f"Cannot parse {name}: {exc}.", name)
        return
    if not element.tag.endswith("svg"):
        report.error("invalid-svg", f"{name} root element must be svg.", name)


def check_commands(root: Path, report: Report) -> None:
    for name, tokens in COMMAND_TOKENS.items():
        path = root / "commands" / name
        text = path.read_text(encoding="utf-8")
        if not FRONTMATTER_RE.match(text):
            report.error("command-frontmatter", f"{name} needs YAML frontmatter.", name)
            continue
        frontmatter = parse_frontmatter(text)
        if len(frontmatter.get("description", "")) < 20:
            report.error("command-description", f"{name} needs a substantive description.", name)
        if not frontmatter.get("argument-hint"):
            report.error("command-hint", f"{name} needs an argument-hint.", name)
        for token in tokens:
            if token not in text:
                report.error("missing-command-content", f"{name} must mention {token}.", name)


def check_docs(root: Path, report: Report) -> None:
    readme = (root / "README.md").read_text(encoding="utf-8")
    for token in (
        "Teach", "/teach", "RESOURCES.md", "PROGRESS.md", "GOALS.md", "LESSONS.md",
        "HTML", "quiz", "Web Speech API", "prompt-injection", "MIT",
        "init_study.py", "validate_state.py", "validate_plugin.py",
    ):
        if token not in readme:
            report.error("docs-content", f"README must mention {token}.", "README.md")

    license_text = (root / "LICENSE").read_text(encoding="utf-8")
    if not license_text.startswith("MIT License") or "Copyright (c) 2026" not in license_text:
        report.error("license-content", "LICENSE must be MIT with a 2026 copyright.", "LICENSE")

    makefile = (root / "Makefile").read_text(encoding="utf-8")
    for target in ("test:", "coverage:", "validate:"):
        if target not in makefile:
            report.error("makefile-content", f"Makefile needs target {target}.", "Makefile")

    ci = (root / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    for token in ("pytest", "validate_plugin.py", "coverage"):
        if token not in ci:
            report.error("ci-content", f"CI must mention {token}.", "ci.yml")

    gitignore = (root / ".gitignore").read_text(encoding="utf-8")
    for token in (".coverage", ".env"):
        if token not in gitignore:
            report.error("gitignore-content", f".gitignore must ignore {token}.", ".gitignore")
    for line in gitignore.splitlines():
        if line.strip() == "pyproject.toml":
            report.error("gitignore-content", "pyproject.toml must be versioned, not ignored.", ".gitignore")

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    if "fail_under = 80" not in pyproject:
        report.error("pyproject-content", "pyproject.toml must enforce an 80% coverage gate.", "pyproject.toml")


def scan_placeholders(root: Path, report: Report) -> None:
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in SCAN_SUFFIXES:
            continue
        if any(part in EXCLUDED_PARTS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        stripped = re.sub(r"```.*?```", "", text, flags=re.S)
        stripped = re.sub(r"`[^`]*`", "", stripped)
        if re.search(r"\b(TODO|FIXME|TBD)\b|\bplaceholder\b", stripped):
            report.error("placeholder", f"Placeholder found in {path.name}.", str(path))


def validate_plugin(root: Path, report: Report | None = None, strict: bool = False) -> Report:
    report = report if report is not None else Report()
    report.strict = strict
    root = Path(root)
    version = expected_version(root, report)
    check_required_files(root, report)
    check_root_manifest(root, report)
    check_claude(root, report, version)
    check_codex(root, report, version)
    check_cursor(root, report, version)
    check_copilot(root, report, version)
    check_codex_marketplace(root, report)
    check_skill(root, report, version)
    check_openai_yaml(root, report)
    check_svg(root, "assets/icon.svg", report)
    check_svg(root, "assets/logo.svg", report)
    check_commands(root, report)
    check_docs(root, report)
    scan_placeholders(root, report)
    return report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="validate_plugin.py",
        description="Validate the teach plugin structure and manifests.",
    )
    parser.add_argument("root", nargs="?", default=".", help="Plugin root directory.")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable output.")
    return parser


def print_report(report: Report) -> None:
    print("PASS: plugin structure" if report.ok else "FAIL: plugin structure")
    for issue in report.errors:
        location = f" ({issue.location})" if issue.location else ""
        print(f"[ERROR] {issue.code}: {issue.message}{location}")
    for issue in report.warnings:
        location = f" ({issue.location})" if issue.location else ""
        print(f"[WARN] {issue.code}: {issue.message}{location}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = validate_plugin(Path(args.root), Report(), strict=args.strict)
    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print_report(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
