# State format

All files live at the root of the study directory indicated by `--dir` (default: current directory). IDs are sequential per type, three digits, and never reused.

## GOALS.md

```markdown
<!-- teach:artifact type=goals version=1 -->
- Topic: Async Rust
- Goal: Understand async/await and Tokio to write small services
- Scope: Futures fundamentals, runtime, and cancellation
- Out of Scope: production deployment and clustering
- Language: en
- Level: intermediate
- Minutes per Session: 8
- Allowed Domains: doc.rust-lang.org,tokio.rs
- Created: 2026-11-24

<!-- teach:section id=goal -->
One-sentence objective.

<!-- teach:section id=scope -->
What is included and what stays out.

<!-- teach:section id=roadmap -->
1. Futures and polling
2. async/await
3. Cancellation
```

## RESOURCES.md

```markdown
<!-- teach:artifact type=resources version=1 -->

<!-- teach:source id=R-001 status=verified type=official-docs version=1.2 accessed=2026-11-24 -->
### R-001: Source title
- Title: Title as found
- URL: https://doc.rust-lang.org/stable/book/
- Type: official-docs
- Version: stable edition
- Domain: doc.rust-lang.org
- Tool: webfetch
- Accessed: 2026-11-24
- Claims: async uses Futures; Futures are lazy until polled.
- Excerpt: "Futures are lazy and do nothing unless polled."
- Status: verified

<!-- teach:history id=H-001 source=R-001 date=2026-11-24 tool=webfetch result=verified -->
### H-001: Initial verification
- Evidence: chapter on Futures read at the registered URL.
- Result: verified
```

The history section stays at the end of the file and grows only by appending.

## LESSONS.md

```markdown
<!-- teach:artifact type=lessons version=1 -->

<!-- teach:lesson id=L-001 file=lessons/001-futures.html level=intermediate minutes=8 sources=R-001 quiz=3 audio=true -->
### L-001: Lazy Futures
- Summary: what the lesson covers.
- Audio Reason: narration helps with pronunciation of the terms.
```

## PROGRESS.md

```markdown
<!-- teach:artifact type=progress version=1 -->

<!-- teach:session id=S-001 date=2026-11-24 lesson=L-001 quiz=2/3 status=completed -->
### S-001: First session
- Objective: understand why Futures are lazy.
- Outcome: two of three correct; review polling next session.
- Sources: R-001
- Next: review polling before async/await.
```

## HTML lesson

Each `lessons/NNN-topic.html` file contains this marker before `<html>` or inside `<head>`:

```html
<!-- teach:lesson-html id=L-001 lang=en sources=R-001 quiz=3 audio=true -->
```

The validator checks unique IDs, history sequence, existence of the lesson file, citation resolution, allowed domains, language, and HTML safety.
