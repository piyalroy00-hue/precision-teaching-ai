# Precision Teaching using Artificial Intelligence

## Phase 1 — AI-Based Assessment and Learner Modelling

Phase 1 builds an AI-based educational assessment system that answers the question:

> **"What does this student currently know?"**

It covers: student profiles, subjects/topic hierarchies, a question bank
(generated + augmented + validated), diagnostic assessments, response
recording, topic-level performance analysis, mastery estimation via
**Bayesian Knowledge Tracing (BKT)**, and a Flask-based learner dashboard.
Phase 2 adds adaptive and personalized teaching: prerequisite-aware learning
recommendations, learning sessions, adaptive practice, continuous BKT updates,
student progress tracking, an AI tutor, and evaluation tooling.

## Running the application

```powershell
cd "precision-teaching-ai"          # this project folder
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# One-time: create the schema + seed the topic hierarchy
python scripts\init_db.py

# Generate the dataset (reproducible, fixed seed = 42)
python scripts\generate_questions.py
python scripts\augment_questions.py
python scripts\validate_questions.py
python scripts\generate_students.py
python scripts\generate_responses.py
python scripts\generate_learning_resources.py
python scripts\generate_phase2_histories.py

# Run the Flask app (loads questions_final.csv into the DB automatically on first run)
python -m flask --app app.main run --host 0.0.0.0 --port 5000
```

Then open the local URL, register a student account, log in, complete the diagnostic
assessment, and view the dashboard for the resulting topic mastery profile. Open
**Learning Plan** to start a prerequisite-aware synthetic learning resource. Completing
it launches adaptive practice; every response updates the BKT state and the next plan.

### Admin access

Register a normal account, then assign its administrator role once using:

```powershell
python scripts\promote_admin.py
```

Sign in with that account to open `/admin/`. The panel shows user profile and account
status information, supports password resets, and permanently removes users with their
associated learning records. Password hashes and plaintext passwords are never shown.

## Running the tests

```powershell
pytest -v
```

67 tests covering BKT correctness/bounds, mastery-band classification,
database schema/seeding, dataset validation, question loading, auth, and the
assessment engine (scoring + BKT integration) — all passing.

## Architecture

```
app/
├── main.py            Flask application factory and startup bootstrap
├── config/settings.py  Paths, DB URL, BKT defaults, mastery bands, seed
├── database/
│   ├── db.py            SQLAlchemy engine/session/Base
│   └── seed.py           Fixed Python-Programming topic hierarchy
├── blueprints/
│   ├── auth.py          login/register/logout routes
│   └── student.py       dashboard/assessment routes
├── models/               ORM models (see ER diagram below)
├── services/
│   ├── auth_service.py       registration/login (PBKDF2 password hashing)
│   ├── question_loader.py    loads validated CSV -> questions/options tables
│   ├── assessment_service.py  fixed diagnostic set, response recording, scoring
│   └── knowledge_service.py   BKT persistence + topic mastery reporting
├── templates/
│   ├── auth/
│   ├── student/
│   └── base.html
├── ai/bkt.py            Bayesian Knowledge Tracing (first-principles)
├── ai/gap_detector.py   BKT-based learning-gap classification
├── ai/prerequisite_graph.py  replaceable in-memory prerequisite graph
├── ai/recommender.py    configurable transparent recommendation scoring
├── ai/difficulty.py     stable recent-performance difficulty selection
├── utils/security.py    PBKDF2-HMAC-SHA256 password hashing
└── __init__.py

data/{raw,generated,augmented,processed}/   dataset pipeline outputs
scripts/                  generation/augmentation/validation/synthetic-data CLIs
tests/                    pytest suite (50 tests)
```

## Phase 2 adaptive loop

The recommendation engine combines normalized knowledge gap (0.35), prerequisite
relevance (0.25), difficulty match (0.15), recent performance (0.15), and resource
freshness/completion (0.10). The weights live in `app/config/settings.py`; gap severity
is weighted most heavily because it directly measures unmet learning needs, while the
remaining signals prevent inappropriate or repeated recommendations.

Difficulty uses the last five responses and moves by at most one level (Easy, Medium,
Hard), preventing abrupt easy-to-hard oscillation. Synthetic resource data is clearly
labelled with `data_source=synthetic`; generated session and adaptive-response histories
are also clearly identified and deterministic (seed 42).

### ER diagram (description)

- **users** (1) → (many) **assessments**, **responses**, **knowledge_states**
- **subjects** (1) → (many) **topics**; **subjects** (1) → (many) **assessments**
- **topics** self-references via `parent_topic_id` (e.g. "Loops" → "for Loop",
  "while Loop"); (1) → (many) **questions**; (1) → (many) **knowledge_states**
- **questions** (1) → (many) **question_options**; (1) → (many) **responses**
- **assessments** (1) → (many) **responses**
- **knowledge_states**: one row per (student, topic) pair — `UNIQUE(student_id, topic_id)`

### Concept hierarchy (Python Programming)

Variables and Data Types · Operators · Conditional Statements · Loops (for
Loop, while Loop) · Functions (Function Definition, Parameters and Arguments,
Return Values, Variable Scope) · Lists · Tuples · Dictionaries · Exception
Handling · File Handling · Recursion — 17 topic rows (11 top-level + 6
children), 15 leaf topics receive questions directly.

## Dataset

Pipeline (fixed seed = 42, fully reproducible):

1. `scripts/generate_questions.py` — 60 hand-authored base MCQ/True-False
   questions (`source=generated`), covering all 15 leaf topics across
   Easy/Medium/Hard difficulty → `data/generated/questions_generated.csv`
2. `scripts/augment_questions.py` — 7 answer-safe augmentation techniques
   (paraphrasing, code-variable renaming, code-block restyling, distractor
   shuffling, difficulty variation, context variation, and programmatically
   verified question-template variation) → 137 total rows in
   `data/augmented/questions_augmented.csv` (`source=augmented` for the 77
   new variants)
3. `scripts/validate_questions.py` — re-validates every row (required fields,
   valid difficulty/type, `marks > 0`, correct_answer present among options,
   no duplicate options) → `data/processed/questions_final.csv` (137/137
   valid) and `validation_errors.csv`
4. `scripts/generate_students.py` — 28 **SYNTHETIC** student profiles across 7
   learning-profile types (strong, average, slow, weak, topic_specific,
   improving, inconsistent) → `data/generated/synthetic_students.csv`
5. `scripts/generate_responses.py` — 3,360 **SYNTHETIC** responses (4 sessions
   × 2 questions/topic/session per student), correctness drawn probabilistically
   per learner-profile model with noise (not hard-coded) →
   `data/generated/synthetic_responses.csv`

All synthetic files carry a `data_source="synthetic"` column and are
documented as fabricated data for BKT development — never real student
records.

## Bayesian Knowledge Tracing (`app/ai/bkt.py`)

Standard 4-parameter model: `P(L0)=0.20, P(T)=0.15, P(G)=0.20, P(S)=0.10`
(overridable per call via `BKTParameters`). On each response:

1. Bayesian posterior conditioned on correctness (`_posterior_given_correct` /
   `_posterior_given_incorrect`)
2. Learning-transition applied (`_apply_learning_transition`) to get the
   mastery estimate carried into the next opportunity

Mastery probability → interpreted band: `0.00–0.39 Beginner`,
`0.40–0.69 Developing`, `0.70–0.89 Proficient`, `0.90–1.00 Mastered` (the raw
probability is always retained alongside the label in `knowledge_states`).

## Status

**Phase 1 complete.** All 12 deliverable steps implemented and verified via
automated tests and a manual end-to-end run (register → login → diagnostic
assessment → response recording → BKT update → dashboard). Phase 2 (adaptive
testing) awaits explicit instruction to begin.

## Phase 3: Generative AI tutor and evaluation

Phase 3 preserves the separation of responsibilities: BKT and the recommendation
engine select the learning target; the tutor generates instructional material only.
The default provider is a deterministic local development provider, so the application
does not require an LLM key or make network calls. Generated Python examples are parsed
without execution, and generated practice questions must have valid difficulty, unique
options, and a correct answer that matches an option.

To enable the optional OpenAI adapter, install the updated requirements and configure
`AI_TUTOR_PROVIDER=openai`, `OPENAI_API_KEY`, and optionally `OPENAI_TUTOR_MODEL` in the
deployment environment. Do not commit API keys. The local provider remains the default.

Student tutor conversations are stored only in the student's AI session. Teacher views
show aggregate and per-student learning data but never expose private conversation
content. The research protocol is in `docs/phase3_evaluation_protocol.md`; generate the
anonymized development dataset with `python scripts/generate_research_dataset.py`.
