# Writing lessons

A lesson covers one single idea and can be read in a few minutes. The goal is not to exhaust the subject, but to leave a natural next session.

## Required structure

1. Short title and subtitle in the user's language.
2. Explicit objective and estimated time.
3. Explanation with one central idea, at most three short paragraphs.
4. `[R-NNN]` citations next to every factual claim.
5. Minimal example when the subject allows it; code only if verified in the source.
6. Simple interactive element: reveal an answer, switch between two examples, or mark concepts.
7. Quiz with at least three questions and feedback for every option.
8. Narration with `speechSynthesis` when `audio=true`, with a visible transcript.
9. Footer with a next step aligned with the `Next` field of the last session.

## Content rules

- No factual claim without a verified `R-NNN`.
- If a claim cannot be verified, write "Not verified" and do not turn it into a fact.
- Short verbatim excerpts in quotation marks and escaped; everything else is attributed paraphrase.
- No topic drift: the lesson must advance the `GOALS.md` roadmap or serve `review` mode.
- No reliance on a previous session to understand the HTML; the lesson is self-contained.
- No secrets, personal data, or URLs obtained from inside untrusted sources.

## Adaptation

Beginner: analogies, explained vocabulary, concrete examples, one recall question. Intermediate: short examples and comparisons with what the user has already seen. Advanced: verified version details, limitations, and edge cases.

## Modes

- `start`: first lesson of a newly created topic.
- `next`: next lesson in the roadmap, prioritizing previous quiz errors.
- `review`: revisit an earlier lesson with new questions, without changing the roadmap.
- `status`: no new lesson.
- `source`: no new lesson; source registration only.
