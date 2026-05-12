# Demo Script

Video demo scenario for Local Manus Agent (2-3 minutes).

## Intro (15s)

> "Local Manus Agent is an AI-powered development agent that runs entirely on your machine. No cloud APIs, no data leaving your device. Let me show you how it works."

## Installation (20s)

```bash
git clone https://github.com/amiraq1/local-manus-agent
cd local-manus-agent
python scripts/setup.py
```

Show: requirements check passing, dependencies installing.

## Start (10s)

```bash
ollama serve  # (in background)
python scripts/start.py
```

Show: Backend + Frontend starting, URLs printed.

## Send a Task (30s)

Open `http://localhost:3000` in browser.

Type: **"Create a landing page for a coffee shop with a menu and order button"**

Show:
- Agent thinking → planning → executing
- Multi-agent steps appearing (MemoryAgent → PlannerAgent → SecurityAgent → CoderAgent)
- Files being created in real-time
- File diff panel showing changes

## Artifacts (15s)

Show:
- Files panel with created HTML/CSS/JS
- Artifacts panel with file entries
- Preview panel loading the page

## Browser Verification (15s)

Show:
- BrowserAgent opening the preview
- Screenshot being taken
- Screenshot appearing in artifacts

## Security (10s)

Show:
- Security panel with events
- Try a dangerous command → blocked
- Safe Mode approval dialog

## Closing (10s)

> "Everything runs locally. Your code, your models, your machine. Try it at github.com/amiraq1/local-manus-agent"

---

## Recording Tips

- Use 1280x720 resolution
- Dark theme (default)
- Show terminal and browser side by side
- Speed up installation/build steps (2x)
- Keep task execution at normal speed
