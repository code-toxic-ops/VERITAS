# VERITAS

Paste a suspicious message, job offer, scholarship notice or link. VERITAS doesn't just say
"safe" or "dangerous". It shows **which exact phrases and link features raised a flag, why they
matter, and what to do next.**

> VERITAS uses learned classifiers and explainable warning signals. It cannot guarantee that a message is a scam, or that a message with no warnings is safe. The interface shows a categorical risk posture, not a numerical score.

## Run it

You need Python 3.9+ and Node 18+.

**1. Backend (FastAPI)**

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

**2. Frontend (React + Vite)** in a second terminal

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```

Vite proxies `/api` to the backend, so there is nothing else to configure.

**Single-server deploy (handy for the demo):**

```bash
cd frontend && npm install && npm run build   # creates frontend/dist
cd ../backend && uvicorn app.main:app --port 8000
```

When `frontend/dist` exists, FastAPI serves the website and the API from one URL.
Set `CORS_ORIGINS` (comma separated) if the frontend is hosted on another origin.

**Tests:** `cd backend && python -m pytest`

## How it works

1. The user submits a message and/or a link.
2. **Text rules** (`backend/app/rules.py`) look for warning signs and record the exact matched phrase.
3. **URL checks** (`backend/app/url_analysis.py`) inspect the link *text only*. No link is ever opened or resolved.
4. **Learned models** (`backend/app/ml/`) classify message patterns as genuine, scam or spam and assess URLs for malicious patterns.
5. **Evidence layer** keeps readable rules, phrase highlights, model cues and practical next steps. The interface displays a risk category rather than a numerical score.

### Detection architecture

The trained message classifier combines word n-grams, character n-grams and transparent signal features. The URL classifier combines structural features with character n-grams. The rule findings below remain explanatory evidence and are not the sole decision-maker.

The previous rule weights remain in the evidence layer to help explain why a phrase or URL structure was flagged. They are not validated fraud probabilities and are not displayed as a score in the interface. The learned message model combines word n-grams, character n-grams and rule/meta features; the URL model combines numeric URL features with character n-grams.

### Evidence vs. assumption

Every finding is labelled. *Found in the message / link* points at something visible in what was
submitted. *Needs verification* (the unverified company claim) is something VERITAS cannot
confirm and the user must check.

### Design decisions worth mentioning to judges

- **Explainable, not a black box.** Rule signals and model-influential phrases help explain the assessment.
- **Safe URL handling.** No fetching, so there is no SSRF risk and no link is visited for the user.
- **Warning sentences are not flagged.** "Never share your OTP" is genuine advice, so negated
  sentences are ignored for credential and document requests.
- **Domain matching, not substring matching.** `t.co` is matched as a domain, so it doesn't flag
  `microsoft.com`.
- **Privacy.** Text is analysed in memory; nothing is stored or logged.
- **Hindi + English** phrases for the most common patterns.

## API

`POST /api/analyze` with `{ "text": "...", "url": "..." }` (at least one; text max 5000 chars).
`GET /api/samples` returns demo scam and legitimate messages. `GET /api/health` for a liveness check.

## Project layout

```
backend/
  app/
    main.py          FastAPI app and routes
    ml/              learned classifiers, synthetic corpus and training pipeline
    signals.py       rule signals shared with the message model
    engine.py        model integration, evidence, highlights, next steps
    rules.py         text rules and weights  <- tune these
    url_analysis.py  offline URL checks
    brands.py        organisations and their real domains
    samples.py       demo scam / legit messages
  tests/             pytest suite
frontend/
  src/               React app (App, api, components, styles)
```

## Training the models

The project includes a trained starter model. If model artefacts are missing, the first analysis trains and caches the models automatically. You can retrain explicitly from `backend/` with `python train.py`. This creates starter CSV corpora in `backend/data/` and model artefacts under `backend/app/models/`. Add real, labelled CSV examples with `message,label` or `url,safe|malicious` columns using `--messages` and `--urls`, then retrain.

The included starter corpus is synthetic and template-generated. It is a working baseline, not evidence of production-grade accuracy. The included holdout is a small hand-written sanity check (18 messages and 12 URLs), not a production benchmark. Add a larger representative, independently labelled `data/holdout.json` set before making accuracy claims.

## Known limitations

- Synthetic training data is cleaner and less diverse than real-world messages. Validate with a representative, independently labelled dataset before relying on it.
- The brand list is small. Add organisations and their real domains in `brands.py`.
- The India reporting guidance (helpline 1930, cybercrime.gov.in) should be re-checked against the
  official sites before a public launch.
