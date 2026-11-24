# Quiz and audio

## Quiz

Each lesson has at least three questions with immediate feedback.

- Ask about the central idea and about a distinction the text makes explicit.
- Every wrong option receives short feedback explaining the mistake.
- Use only claims supported by `R-NNN`.
- Count correct answers at the end and record the result in `S-NNN` as `A/B`.
- Mistakes become the next session's priority in `review` mode.
- For advanced learners, include one case question with a verified edge condition.

## Audio with Web Speech API

The HTML uses `window.speechSynthesis` and `SpeechSynthesisUtterance`, with no audio files and no remote services.

- Set `utterance.lang = document.documentElement.lang`.
- Read the text from the visible transcript; never invent content just for narration.
- Provide play and stop buttons, with `aria-live` for status.
- Keep the transcript in `<details>` open by default when the language is new to the user.
- If `speechSynthesis` is missing, disable the buttons and state that the transcript is available.

## When to use audio

Use `audio=true` for languages, pronunciation, conceptual narration, read-aloud review, and subjects where auditory repetition helps. Use `audio=false` for predominantly visual lessons, dense formulas, or when the user's browser has no voices for the language; record the reason in `LESSONS.md`.

The transcript always accompanies narration, including when the audio is generated in the browser.
