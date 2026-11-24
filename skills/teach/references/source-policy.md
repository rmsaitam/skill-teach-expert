# Source policy

The model is not a reliable source of knowledge. Parametric memory may be used only to formulate search questions; never to state facts in a lesson.

## Lookup order

1. Libraries, frameworks, SDKs, APIs, and command-line tools: use Context7. Resolve the exact library ID first, then query documentation with the specific question and the relevant version. Record the ID used.
2. All other subjects: search for primary sources and open them by reading the page. Prefer official documentation, specifications, RFCs, laws, academic papers, institutional manuals, and source code for the exact version.
3. If the subject is a local codebase, the source code is the primary source for what the project does; official documentation complements the why.

## Recording rules

Every accepted source receives an `R-NNN` in `RESOURCES.md` with:

- `Title`: exact title found.
- `URL`: canonical HTTPS address returned by the tool or supplied by the user.
- `Type`: `official-docs`, `spec`, `rfc`, `paper`, `source-code`, `institutional`, `book`, `other`.
- `Version`: version, edition, or publication date when available.
- `Domain`: domain of the URL.
- `Tool`: `context7`, `webfetch`, `websearch`, `local-code`, or `user`.
- `Accessed`: `YYYY-MM-DD` date of the actual lookup.
- `Claims`: short, specific claims the source supports.
- `Excerpt`: short verbatim excerpt, escaped, about 25 words at most.
- `Status`: `verified`, `needs-review`, or `quarantined`.

Each later lookup appends `H-NNN` without erasing earlier entries, including date, tool, evidence, and result. History is append-only.

## Acceptance criteria

- The source directly supports the claim; titles and search snippets are not enough.
- The domain is in `Allowed Domains` in `GOALS.md`; otherwise ask for confirmation before citing.
- URL shorteners, pages without identifiable authorship, and aggregators are not primary sources.
- Disputed claims or claims that change with version require two independent sources, one of them primary.
- No URL is invented: if the tool did not return the address, it must not appear in the ledger.
- Verbatim excerpts are short and attributed; paraphrases stay linked to the `R-NNN` that supports them.

## When to stop

If no reliable source verifies the next subtopic, do not write the content as fact. Record `needs-review`, explain the limitation, and propose another subtopic or ask the user for a source. Never fill gaps with model memory.
