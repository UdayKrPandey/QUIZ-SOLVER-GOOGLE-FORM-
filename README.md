# LLM Quiz

A local Python automation script that uses an OpenAI-compatible LLM endpoint to answer practice questions in Google Forms through a visible Playwright-controlled Chromium browser.

The script reads supported multiple-choice and multiple-select questions, sends the question and visible options to the configured LLM, selects matching answers, and advances through form pages. It stops on the final page and does **not** click `Submit`.

## Important Security Notice

`llmquiz.py` contains a placeholder API key. Before running it, replace the placeholder with your own key locally. Do not commit or upload the edited file after adding your key. Never share your key in issues, discussions, pull requests, screenshots, or terminal logs.

The previously exposed key must be revoked or rotated immediately if it was ever committed, shared, uploaded, or exposed in a chat, screenshot, log, or public repository. Removing a key from a later commit is not sufficient because it remains in Git history.

## What It Does

- Opens a persistent, visible Chromium browser using Playwright.
- Waits for a Google Form page to be opened by the user.
- Detects visible radio-button and checkbox questions.
- Sends each question and its options to the configured LLM.
- Selects answers by matching the returned option text.
- Clicks `Next` when available.
- Stops before the final `Submit` action so the user can review answers manually.

## What It Does Not Do

- It does not guarantee correct answers.
- It does not submit the form.
- It does not bypass authentication, access controls, or anti-bot protections.
- It does not support every Google Forms question type or layout.
- It does not make the use of an LLM appropriate for graded assessments.

## Requirements

- Windows, macOS, or Linux
- Python 3.10 or newer
- A supported LLM API account and API key
- A Google account if the form requires one
- Permission to access and automate the form

The script depends on:

- `openai` for the OpenAI-compatible API client
- `playwright` for browser automation

## Installation

Create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install the Python dependencies:

```bash
pip install openai playwright
python -m playwright install chromium
```

If this project later includes a pinned dependency file, prefer installing from it:

```bash
pip install -r requirements.txt
```

## Configuration

The script uses Google's OpenAI-compatible Gemini endpoint. To configure it:

1. Open the [Google AI Studio API key page](https://aistudio.google.com/apikey).
2. Sign in and create or copy an API key.
3. Open `llmquiz.py` in a text editor.
4. Find the line beginning with `api_key=`.
5. Replace `PUT UR whatveaaa like api key` with your key, keeping the key inside the quotation marks.
6. Run the script locally.

Example shape:

```python
api_key="your-google-ai-studio-key"
```

Never commit the file after adding your real key. If you plan to contribute changes, restore the placeholder before committing or use a separate local copy. Also keep browser profiles and local state files private.

You can also adjust `LLM_MODEL_NAME`, `PROFILE_DIR`, and the OpenAI-compatible `base_url` in the same configuration area when needed. Verify current model names, endpoint format, quotas, pricing, and data-retention terms in Google's documentation.

Use the provider's current documentation to verify model names, endpoint format, quotas, pricing, and data-retention terms.

## Usage

Run the script from the project directory:

```bash
python llmquiz.py
```

Then:

1. Let the Chromium window open.
2. Open an authorized Google Form in that browser.
3. Navigate to the first practice-quiz page.
4. Leave the browser window open while the script processes the form.
5. Review every selected answer on the final page.
6. Submit the form yourself only when you are satisfied.

The browser profile is persistent. It may contain cookies, login sessions, browsing history, and other private browser data. Never publish or share the profile directory.

## Privacy and Data Handling

Question text and visible answer options are sent to the configured LLM provider. Do not use this script with confidential, personal, proprietary, or regulated information unless you have verified that the provider's terms and your organization’s policies permit it.

The local Playwright profile may also store sensitive account data. Treat it like a private credential store:

- Keep it outside the repository when possible.
- Add it to `.gitignore`.
- Do not upload archives or screenshots containing the profile.
- Use a separate browser profile for this script.
- Delete the profile when it is no longer needed.

## Accuracy and Failure Modes

LLM responses can be incorrect, incomplete, or ambiguous. The script matches returned text against visible option labels, so answers may fail when the model changes punctuation, formatting, or wording. A question can also be skipped if Google Forms changes its DOM structure or uses an unsupported control.

Always review answers manually. Never rely on this tool for exams, graded coursework, certifications, medical decisions, legal decisions, or other high-stakes work.

## Responsible Use

Use this project only with forms you are authorized to access and automate. Respect the form owner's rules, the LLM provider's terms, Google’s terms, school or workplace policies, and applicable laws. Use it for practice, testing, accessibility experiments, and other permitted workflows.

Do not use it to impersonate a user, defeat access controls, evade assessment rules, submit fraudulent responses, or overload a service.

## Troubleshooting

### Chromium does not start

Run:

```bash
python -m playwright install chromium
```

Then verify that no other process is locking the configured browser profile.

### The form is not detected

Make sure the page URL is a Google Forms page, the page has finished loading, and the form is open in the Chromium window launched by the script.

### A question is not answered

The current implementation supports visible radio-button and checkbox controls. It may not support dropdowns, grids, short-answer fields, file uploads, or custom layouts. Check the terminal output and review the question manually.

### The API request fails

Check the API key, endpoint, model name, account quota, network connection, and provider status. Do not print the key while debugging.

## Limitations

This is a local automation script, not a hosted service. It has no authentication layer, web dashboard, test suite, formal support for all Google Forms controls, or guarantee of compatibility with future Google Forms changes.

## Contributing

Keep pull requests focused and do not include:

- API keys or other secrets
- Browser profiles or session data
- Personal information from forms
- Unredacted screenshots or terminal logs
- Automated form submissions used for testing

When reporting a bug, include the Python version, operating system, Playwright version, and a redacted description of the form control. Do not include private question content or credentials.

## License

Choose and add a license before publishing. Until a license file is added, default copyright law applies and others do not automatically have permission to reuse, modify, or redistribute this code.

## Disclaimer

This software is provided as-is, without guarantees of accuracy, availability, compatibility, or fitness for a particular purpose. You are responsible for API charges, browser sessions, selected answers, submitted form responses, and compliance with all applicable policies and laws.
