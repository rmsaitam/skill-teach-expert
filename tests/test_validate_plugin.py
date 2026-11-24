import json

import pytest

import validate_plugin as vp


def load_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def replace_in(path, old, new):
    text = path.read_text(encoding="utf-8")
    assert old in text
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def codes(report):
    return {issue.code for issue in report.errors}


def test_repository_validates_cleanly(root):
    report = vp.validate_plugin(root)

    assert report.ok
    assert report.errors == []
    assert vp.expected_version(root, report) == "0.1.0"


def test_missing_required_file(plugin_root):
    (plugin_root / "skills" / "teach" / "scripts" / "validate_state.py").unlink()

    assert "missing-required-file" in codes(vp.validate_plugin(plugin_root))


def test_empty_required_file(plugin_root):
    (plugin_root / "README.md").write_text("", encoding="utf-8")

    assert "empty-file" in codes(vp.validate_plugin(plugin_root))


def test_duplicate_json_key(plugin_root):
    path = plugin_root / "plugin.json"
    path.write_text(
        '{\n  "$schema": "https://antigravity.google/schemas/v1/plugin.json",\n'
        '  "name": "teach",\n  "name": "teach",\n'
        '  "description": "A study plugin with verified sources."\n}\n',
        encoding="utf-8",
    )

    assert "duplicate-json-key" in codes(vp.validate_plugin(plugin_root))


def test_version_mismatch_across_manifests(plugin_root):
    path = plugin_root / ".cursor-plugin" / "plugin.json"
    data = load_json(path)
    data["version"] = "0.2.0"
    write_json(path, data)

    assert "version-mismatch" in codes(vp.validate_plugin(plugin_root))


def test_invalid_semver(plugin_root):
    path = plugin_root / ".claude-plugin" / "plugin.json"
    data = load_json(path)
    data["version"] = "one"
    write_json(path, data)

    assert "invalid-version" in codes(vp.validate_plugin(plugin_root))


def test_root_manifest_rejects_extra_key(plugin_root):
    path = plugin_root / "plugin.json"
    data = load_json(path)
    data["version"] = "0.1.0"
    write_json(path, data)

    assert "root-manifest-extra-key" in codes(vp.validate_plugin(plugin_root))


def test_root_manifest_requires_schema(plugin_root):
    path = plugin_root / "plugin.json"
    data = load_json(path)
    data["$schema"] = "https://example.com/schema.json"
    write_json(path, data)

    assert "root-manifest-schema" in codes(vp.validate_plugin(plugin_root))


def test_claude_manifest_requires_owner(plugin_root):
    path = plugin_root / ".claude-plugin" / "marketplace.json"
    data = load_json(path)
    del data["owner"]
    write_json(path, data)

    assert "missing-owner" in codes(vp.validate_plugin(plugin_root))


def test_codex_manifest_requires_capabilities(plugin_root):
    path = plugin_root / ".codex-plugin" / "plugin.json"
    data = load_json(path)
    data["interface"]["capabilities"] = []
    write_json(path, data)

    assert "codex-capabilities" in codes(vp.validate_plugin(plugin_root))


def test_cursor_manifest_requires_commands(plugin_root):
    path = plugin_root / ".cursor-plugin" / "plugin.json"
    data = load_json(path)
    del data["commands"]
    write_json(path, data)

    assert "cursor-commands" in codes(vp.validate_plugin(plugin_root))


def test_copilot_marketplace_version_must_match(plugin_root):
    path = plugin_root / ".github" / "plugin" / "marketplace.json"
    data = load_json(path)
    data["plugins"][0]["version"] = "0.2.0"
    write_json(path, data)

    assert "version-mismatch" in codes(vp.validate_plugin(plugin_root))


def test_agents_marketplace_requires_available_policy(plugin_root):
    path = plugin_root / ".agents" / "plugins" / "marketplace.json"
    data = load_json(path)
    data["plugins"][0]["policy"]["installation"] = "DISABLED"
    write_json(path, data)

    assert "agents-policy" in codes(vp.validate_plugin(plugin_root))


def test_skill_requires_frontmatter(plugin_root):
    path = plugin_root / "skills" / "teach" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.split("---", 2)[2], encoding="utf-8")

    assert "missing-frontmatter" in codes(vp.validate_plugin(plugin_root))


def test_skill_name_must_match(plugin_root):
    replace_in(
        plugin_root / "skills" / "teach" / "SKILL.md",
        "name: teach",
        "name: wrong-name",
    )

    assert "wrong-name" in codes(vp.validate_plugin(plugin_root))


def test_skill_description_must_be_substantive(plugin_root):
    path = plugin_root / "skills" / "teach" / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    start = text.index("description: '")
    end = text.index("'\n", start)
    path.write_text(text[:start] + "description: 'Too short.'" + text[end:], encoding="utf-8")

    assert "weak-description" in codes(vp.validate_plugin(plugin_root))


def test_skill_requires_mit_license(plugin_root):
    replace_in(plugin_root / "skills" / "teach" / "SKILL.md", "license: MIT", "license: GPL")

    assert "missing-license" in codes(vp.validate_plugin(plugin_root))


def test_skill_version_must_match(plugin_root):
    replace_in(plugin_root / "skills" / "teach" / "SKILL.md", 'version: "0.1.0"', 'version: "0.2.0"')

    assert "skill-version-mismatch" in codes(vp.validate_plugin(plugin_root))


def test_skill_references_must_exist(plugin_root):
    replace_in(
        plugin_root / "skills" / "teach" / "SKILL.md",
        "[Source policy](references/source-policy.md)",
        "[Source policy](references/missing-doc.md)",
    )

    assert "missing-reference" in codes(vp.validate_plugin(plugin_root))


def test_skill_requires_study_content(plugin_root):
    path = plugin_root / "skills" / "teach" / "SKILL.md"
    text = path.read_text(encoding="utf-8").replace("speechSynthesis", "audioEngine")
    path.write_text(text, encoding="utf-8")

    assert "missing-skill-content" in codes(vp.validate_plugin(plugin_root))


def test_markdown_link_cannot_escape_root(plugin_root):
    replace_in(
        plugin_root / "skills" / "teach" / "SKILL.md",
        "[Source policy](references/source-policy.md)",
        "[Política de fontes](../../../etc/passwd)",
    )

    assert "path-escape" in codes(vp.validate_plugin(plugin_root))


def test_openai_yaml_requires_default_prompt(plugin_root):
    path = plugin_root / "agents" / "openai.yaml"
    path.write_text("interface:\n  display_name: Teach\n", encoding="utf-8")

    codes_found = codes(vp.validate_plugin(plugin_root))
    assert "missing-default-prompt" in codes_found
    assert "missing-skill-reference" in codes_found


def test_assets_must_be_valid_svg(plugin_root):
    (plugin_root / "assets" / "icon.svg").write_text("<div></div>", encoding="utf-8")

    assert "invalid-svg" in codes(vp.validate_plugin(plugin_root))


def test_commands_require_frontmatter(plugin_root):
    (plugin_root / "commands" / "teach.md").write_text("# Teach\n", encoding="utf-8")

    assert "command-frontmatter" in codes(vp.validate_plugin(plugin_root))


def test_commands_require_study_content(plugin_root):
    replace_in(plugin_root / "commands" / "teach.md", "Web Speech API", "interface de voz")

    assert "missing-command-content" in codes(vp.validate_plugin(plugin_root))


def test_readme_requires_study_tokens(plugin_root):
    (plugin_root / "README.md").write_text("# Teach\n\nInstale com cp.\n", encoding="utf-8")

    assert "docs-content" in codes(vp.validate_plugin(plugin_root))


def test_license_must_be_mit(plugin_root):
    (plugin_root / "LICENSE").write_text("All rights reserved.\n", encoding="utf-8")

    assert "license-content" in codes(vp.validate_plugin(plugin_root))


def test_makefile_requires_targets(plugin_root):
    (plugin_root / "Makefile").write_text("test:\n\ttrue\n", encoding="utf-8")

    assert "makefile-content" in codes(vp.validate_plugin(plugin_root))


def test_ci_requires_validation_steps(plugin_root):
    (plugin_root / ".github" / "workflows" / "ci.yml").write_text("name: CI\n", encoding="utf-8")

    assert "ci-content" in codes(vp.validate_plugin(plugin_root))


def test_gitignore_requires_secret_ignore(plugin_root):
    (plugin_root / ".gitignore").write_text(".coverage\n.env\n", encoding="utf-8")

    assert "gitignore-content" not in codes(vp.validate_plugin(plugin_root))


def test_gitignore_forbids_ignoring_pyproject(plugin_root):
    path = plugin_root / ".gitignore"
    path.write_text(path.read_text(encoding="utf-8") + "\npyproject.toml\n", encoding="utf-8")

    assert "gitignore-content" in codes(vp.validate_plugin(plugin_root))


def test_placeholder_scan(plugin_root):
    path = plugin_root / "README.md"
    path.write_text(path.read_text(encoding="utf-8") + "\nTODO escrever mais.\n", encoding="utf-8")

    assert "placeholder" in codes(vp.validate_plugin(plugin_root))


def test_json_cli_output(root, capsys):
    code = vp.main([str(root), "--json"])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "PASS"


def test_cli_fails_on_broken_plugin(plugin_root, capsys):
    (plugin_root / "LICENSE").write_text("wrong\n", encoding="utf-8")

    assert vp.main([str(plugin_root)]) == 1
    assert "[ERROR]" in capsys.readouterr().out
