# Lesson HTML template

Use this skeleton as the base. Replace only the bracketed text with verified content from the session; keep the markers, CSP, quiz attributes, transcript, and footer.

```html
<!doctype html>
<!-- teach:lesson-html id=L-001 lang=en sources=R-001 quiz=3 audio=true -->
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'">
  <title>Lesson title</title>
  <style>
    :root { color-scheme: light dark; --bg: #ffffff; --fg: #111827; --accent: #4f46e5; }
    @media (prefers-color-scheme: dark) { :root { --bg: #111827; --fg: #f9fafb; --accent: #a5b4fc; } }
    body { font-family: system-ui, sans-serif; margin: 0 auto; max-width: 46rem; padding: 1.5rem; background: var(--bg); color: var(--fg); line-height: 1.6; }
    h1 { font-size: 1.8rem; } h2 { margin-top: 2rem; font-size: 1.2rem; }
    .meta { color: var(--accent); font-weight: 600; }
    .question { border: 1px solid var(--accent); border-radius: .5rem; margin: .75rem 0; padding: .75rem 1rem; }
    button { background: var(--accent); color: var(--bg); border: 0; border-radius: .4rem; cursor: pointer; margin: .25rem .25rem .25rem 0; padding: .5rem .8rem; font: inherit; }
    button[aria-pressed="true"] { outline: 3px solid var(--fg); }
    .feedback { min-height: 1.5rem; font-weight: 600; }
    a { color: var(--accent); }
    @media print { button { display: none; } }
  </style>
</head>
<body>
  <main>
    <p class="meta">Objective: describe the central idea in one sentence. Time: 8 minutes.</p>
    <h1>Lesson title</h1>

    <h2>Central idea</h2>
    <p>Explain the idea in short paragraphs. Every factual claim ends with a citation, such as <a href="REGISTERED_URL" target="_blank" rel="noopener noreferrer">[R-001]</a>.</p>

    <details>
      <summary>Show a hint</summary>
      <p>Short text that helps without replacing the explanation.</p>
    </details>

    <h2>Narration</h2>
    <p>
      <button type="button" id="speak">Play lesson</button>
      <button type="button" id="stop">Stop</button>
    </p>
    <p id="audio-status" class="feedback" aria-live="polite"></p>
    <details id="transcript">
      <summary>Transcript</summary>
      <p>Full narration text, in the same language as the document.</p>
    </details>

    <h2>Quiz</h2>
    <ol id="quiz">
      <li class="question" data-answer="b" data-correct="Correct: explain why." data-wrong="Not yet: explain the reason.">
        <p>Question 1?</p>
        <button type="button" data-option="a">Option A</button>
        <button type="button" data-option="b">Option B</button>
      </li>
      <li class="question" data-answer="a" data-correct="Correct: explain why." data-wrong="Not yet: explain the reason.">
        <p>Question 2?</p>
        <button type="button" data-option="a">Option A</button>
        <button type="button" data-option="b">Option B</button>
      </li>
      <li class="question" data-answer="b" data-correct="Correct: explain why." data-wrong="Not yet: explain the reason.">
        <p>Question 3?</p>
        <button type="button" data-option="a">Option A</button>
        <button type="button" data-option="b">Option B</button>
      </li>
    </ol>
    <p id="score" class="feedback" aria-live="polite">0 of 3 correct.</p>

    <h2>Next step</h2>
    <p>One concrete step aligned with the Next field of the last session.</p>
  </main>
  <script>
    const questions = Array.from(document.querySelectorAll('.question'));
    const answers = new Map();

    function evaluate(question, button) {
      const chosen = button.getAttribute('data-option');
      const correct = question.getAttribute('data-answer') === chosen;
      answers.set(question, correct);
      button.parentNode.querySelectorAll('button').forEach(function (option) {
        option.setAttribute('aria-pressed', String(option === button));
      });
      const feedback = correct ? question.getAttribute('data-correct') : question.getAttribute('data-wrong');
      button.parentNode.setAttribute('data-feedback', feedback);
      const hits = Array.from(answers.values()).filter(Boolean).length;
      document.getElementById('score').textContent = 'Correct answers: ' + hits + ' of ' + questions.length + '. ' + feedback;
    }

    questions.forEach(function (question) {
      question.querySelectorAll('button').forEach(function (button) {
        button.addEventListener('click', function () { evaluate(question, button); });
      });
    });

    const status = document.getElementById('audio-status');
    const transcript = document.getElementById('transcript').textContent.trim();
    const speakButton = document.getElementById('speak');
    const stopButton = document.getElementById('stop');

    if ('speechSynthesis' in window) {
      speakButton.addEventListener('click', function () {
        const utterance = new SpeechSynthesisUtterance(transcript);
        utterance.lang = document.documentElement.lang;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(utterance);
        status.textContent = 'Narrating the lesson.';
      });
      stopButton.addEventListener('click', function () {
        window.speechSynthesis.cancel();
        status.textContent = 'Narration stopped.';
      });
    } else {
      speakButton.disabled = true;
      stopButton.disabled = true;
      status.textContent = 'Narration is unavailable in this browser; use the transcript.';
    }
  </script>
</body>
</html>
```

Replacement rules:

- The `<html>` `lang` and the marker `lang` field must be the user's language.
- Every citation uses a URL already registered in `RESOURCES.md`; never a URL found inside source text.
- The marker `quiz` equals the number of `class="question"` elements.
- If `audio=true`, keep `speechSynthesis` and the transcript; if `audio=false`, remove the narration section and record the reason in `LESSONS.md`.
- Do not add event attributes, external stylesheets, external scripts, or network calls.
