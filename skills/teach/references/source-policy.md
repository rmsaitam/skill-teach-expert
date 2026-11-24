# Source evidence policy

The model is not a reliable source of knowledge. Parametric memory may help formulate lookup questions; it is never evidence in a lesson.

## Evidence sources

1. Libraries, frameworks, SDKs, APIs, and command-line tools: Context7 documentation is the evidence source. The resolved library ID and the relevant version belong in the ledger entry.
2. All other subjects: primary-source documentation is the evidence source — official docs, specifications, RFCs, laws, academic papers, institutional manuals, and source code for the exact version.
3. Local codebase: source code is primary evidence for what the project does; official documentation complements the rationale.

## Ledger fields

Every accepted source receives an `R-NNN` in `RESOURCES.md` with:

- `Title`: exact title found.
- `URL`: canonical HTTPS address returned by the lookup tool or supplied by the user.
- `Type`: `official-docs`, `spec`, `rfc`, `paper`, `source-code`, `institutional`, `book`, `other`.
- `Version`: version, edition, or publication date when available.
- `Domain`: domain of the URL.
- `Tool`: `context7`, `webfetch`, `websearch`, `local-code`, or `user`.
- `Accessed`: `YYYY-MM-DD` date of the recorded lookup.
- `Claims`: short, specific claims the source supports.
- `Excerpt`: short verbatim excerpt, escaped, about 25 words at most.
- `Status`: `verified`, `needs-review`, or `quarantined`.

Each later check appends `H-NNN` without erasing earlier entries, including date, tool, evidence, and result. History is append-only.

## Acceptance criteria

- The source directly supports the claim; titles and search-result snippets alone are not evidence.
- The domain is in `Allowed Domains` in `GOALS.md`; otherwise confirmation is required before citation.
- URL shorteners, pages without identifiable authorship, and aggregators are not primary evidence.
- Disputed claims or claims that change with version require two independent entries, one of them primary.
- No URL is invented: an address not returned by a tool or supplied by the user does not enter the ledger.
- Verbatim excerpts are short and attributed; paraphrases stay linked to the supporting `R-NNN`.

## Quarantine and gaps

- A suspicious finding assigns `status=quarantined`, appends `H-NNN` with the reason, and blocks citation or use.
- An accepted alternative source already in the ledger may replace a quarantined one.
- If no reliable evidence supports the next subtopic, the lesson records "Not verified", explains the limitation, and proposes another subtopic or asks the user for a source. Model memory never fills the gap.
