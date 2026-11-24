# Teach

A skill for continuous, personalized study in coding agents. It turns a directory into a persistent study space: goals, verified sources, short HTML lessons, verification history, and progress are saved in files and resumed in later sessions.

The trigger is always manual: `/teach`. The skill does not answer quick questions and does not change topics without explicit confirmation.

## Features

- **Sources first**: model parametric knowledge is treated as unreliable. Every taught claim needs a verified source recorded in `RESOURCES.md` with URL, version/date, lookup tool, quoted excerpt, access date, and verification history (`H-NNN`).
- **Persistent state**: `GOALS.md`, `RESOURCES.md`, `PROGRESS.md`, `LESSONS.md`, and `lessons/` inside the study directory (`--dir`, default: current directory).
- **Self-contained lessons**: one HTML file per session, with `[R-NNN]` citations, a quiz with feedback, an interactive element, and narration via Web Speech API with a visible transcript.
- **Security**: external content is data, never instructions; prompt-injection patterns put a source into quarantine; restrictive CSP and no remote HTML resources; scope locked by the goals.
- **Language**: every text delivered to the user and the lesson `lang` use the user's language.

## Installation

```bash
npx skills add rmsaitam/skill-teach
npx skills add rmsaitam/skill-teach -g -y
npx skills add rmsaitam/skill-teach --list
```

Claude Code:

```text
/plugin marketplace add rmsaitam/skill-teach
/plugin install teach
```

Generic Agent Skills:

```bash
mkdir -p ~/.agents/skills
cp -R skills/teach ~/.agents/skills/teach
python3 scripts/validate_plugin.py .
```

opencode (project):

```bash
mkdir -p .opencode/skills .opencode/command
cp -R skills/teach .opencode/skills/teach
cp commands/teach.md .opencode/command/teach.md
```

`npx skills add` installs the Agent Skill for any compatible agent. Native install flows use these manifests:

| Agent | Manifest / path |
| --- | --- |
| skills.sh / generic Agent Skills | `skills/teach/SKILL.md` |
| Claude Code | `.claude-plugin/plugin.json` |
| Codex | `.codex-plugin/plugin.json` |
| Cursor | `.cursor-plugin/plugin.json` |
| GitHub Copilot CLI | `.github/plugin/marketplace.json` |
| Antigravity | `plugin.json` |
| opencode (project) | `.opencode/skills/teach` + `.opencode/command/teach.md` |

## Usage

```text
/teach start <topic>
/teach next
/teach review
/teach status
/teach source <url>
```

The `--dir PATH` option points to another study directory. With no existing state, the skill asks for topic, goal, level, language, and minutes per session before creating the files.

## Flow

1. Load or create the state with `init_study.py`; validate with `validate_state.py --strict`.
2. Choose the next step from `PROGRESS.md`, the goal, and incorrect quiz answers.
3. Verify sources before teaching: Context7 for libraries and APIs; search and read official documentation, specifications, RFCs, and source code for other subjects.
4. Write a short HTML lesson in the user's language, with citations and a quiz.
5. Record the session, lesson, and source history; revalidate the state.
6. Deliver a summary, lesson path, sources used, and next step.

## State files

| File | Content |
| --- | --- |
| `GOALS.md` | topic, goal, level, language, scope, out of scope, allowed domains, and roadmap |
| `RESOURCES.md` | `R-NNN` source ledger and append-only `H-NNN` history |
| `LESSONS.md` | `L-NNN` index of generated lessons |
| `PROGRESS.md` | `S-NNN` sessions with quiz result and next step |
| `lessons/NNN-topic.html` | single self-contained lesson with the `teach:lesson-html` marker |

## Markers

```markdown
<!-- teach:artifact type=goals version=1 -->
<!-- teach:artifact type=resources version=1 -->
<!-- teach:artifact type=lessons version=1 -->
<!-- teach:artifact type=progress version=1 -->
<!-- teach:source id=R-001 status=verified type=official-docs version=... accessed=YYYY-MM-DD -->
<!-- teach:history id=H-001 source=R-001 date=YYYY-MM-DD tool=context7 -->
<!-- teach:lesson id=L-001 file=lessons/001-topic.html level=... minutes=8 sources=R-001 quiz=3 audio=true -->
<!-- teach:session id=S-001 date=YYYY-MM-DD lesson=L-001 quiz=3/3 status=completed -->
<!-- teach:lesson-html id=L-001 lang=en sources=R-001 quiz=3 audio=true -->
```

## Development

```bash
make test        # pytest suite
make coverage    # tests with 80% coverage gate
make validate    # plugin structure validation
make check       # coverage plus validation
```

## License

MIT.
