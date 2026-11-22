# GapLens: CHRIST Smart Marks Coach

GapLens is a local Streamlit app that turns question-wise CIA marks into feedback. Students see
*why* they lost marks (not attempted, silly loss, time pressure, concept gap), how they compare
with the class topper (never named) and the class average, which topics to revise, and whether
their target final mark is still reachable. Faculty define papers, upload class marks, add
verified resources, review ESE answer-script presentation, and get a class heatmap with an
early-warning list. There is no login: a sidebar switch picks the role and profile.

## Install

```
pip install -r gaplens/requirements.txt
```

Python 3.11+ is supported; 3.14 was tested.

## Run

```
streamlit run gaplens/app.py
```

The first run creates `gaplens/data/gaplens.db` and seeds the demo data. In the Faculty sidebar,
**Reset demo data** wipes everything and restores it.

## Gemini (optional, free tier)

Copy `gaplens/.streamlit/secrets.toml.example` to `gaplens/.streamlit/secrets.toml` and set
`GEMINI_API_KEY` (a `GEMINI_API_KEY` environment variable also works). The key is used only for
parsing a course plan and drafting an ESE presentation review, and only when faculty click the
button. The free tier may use uploaded content to improve Google's products, so use sample or
dummy course plans and scripts. **Everything works without a key**: create subjects manually and
review scripts with the checklist.

## Demo walkthrough (viva)

Start from a fresh seed (Faculty sidebar, Reset demo data). Demo data: faculty Dr. Demo Faculty,
class MCA-A, 40 students 25MCA001 to 25MCA040, MCA231 Data Structures (CIA-1 to CIA-3 and ESE)
and MCA232 Python Programming (CIA-1 and CIA-2 only, so the goal calculator is still live).

**Student 25MCA007 (Demo Student, the default profile)**

1. **My Subjects**: both subjects are enrolled, with targets 80 (Data Structures) and 75 (Python).
2. Open **Subject Dashboard** and pick the subject in the sidebar. Tabs, left to right:
   - **Goal**: marks earned, marks still available, the average needed in the remaining exams and
     the status badge.
   - **CIA Analysis**: choose a paper; you, topper and class average per question, a mistake type
     and a specific tip per question.
   - **Weak Topics & Resources**: top 3 topics by marks lost, Verified resources first, then
     Auto-suggested search links.
   - **Progress**: topic percentage across CIA-1 to CIA-3.
   - **ESE**: result, final mark against target, and the published presentation review.
3. **Data Structures**: Goal is Achieved or Missed (everything is in). CIA-1 Q1 is a **Silly loss**
   and Q3 a **Concept gap**. Tick the silly-slip ("right method, wrong answer") box on a question
   to show it being re-classified and dropped from the weak-topic ranking. Progress shows
   **Recursion improving** from CIA-1 to CIA-2. The ESE tab shows the published review.
4. **Python Programming**: Goal is live (On track, Stretch, At risk or Out of reach). CIA-1 shows
   **time pressure**; CIA-2 Q5 is **Not attempted** (the blank answer).

**Student 25MCA012 (switch profile in the sidebar)**: the Data Structures ESE is 34, so the ESE
tab shows Fail and **Focus for supplementary exam**, built from the weakest CIA topics.

**Faculty (switch "View as" to Faculty)**

- **My Subjects**: create a subject manually (`unit | topic` per line) or from a course plan with
  Gemini; edit topics; see enrolled students and targets.
- **Papers & Marks**: define each paper's questions, max marks and topics; download the CSV
  template; upload the class CSV or edit marks in the table; enter ESE totals.
- **Resources**: add a verified link to a topic (http or https only); delete one.
- **ESE Scripts**: pick a student, upload a script, tick the presentation checklist, generate
  tips, edit the text and **Publish** (or Unpublish). Students see only published reviews.
- **Class Insights**: heatmap per paper, "Revise these in class" topic view (one paper or
  All CIAs), silly-error flag counts, and the early-warning list with reasons.

**The "real-time" talking point**: Class Insights re-reads the database on every page load. Upload
a marks CSV in Papers & Marks, open Class Insights, and the new marks show immediately.

## CSV formats

**CIA marks** (download the template from Papers & Marks): `roll_no,Q1,Q2,...`, one column per
question of the paper.

- A blank cell means *not attempted* (different from 0).
- A row that is blank in every question is skipped as "not entered".
- Scores must be between 0 and the question's max, or the whole upload is rejected with errors.
- Uploading replaces all marks for that paper. Roll numbers not in the class list still count in
  the class average and topper, anonymously.

**ESE totals**: `roll_no,ese`, with a number out of 100 (blank rows are skipped; an upload
replaces the subject's ESE totals).

## Grading rules in brief

- **Final mark** = CIA total (out of 100) x CIA weight + ESE (out of 100) x (1 - weight). Default
  weight 0.5, so CIA total / 2 + ESE / 2. Components: CIA-1 /25, CIA-2 /50, CIA-3 /25, ESE /100.
- **Pass**: ESE of at least 40 out of 100. Below 40 is a fail.
- **Goal badge**: average so far = marks earned / share of the final mark already assessed;
  required = (target - earned) / share still available. **On track** if required is at or below
  the average; **Stretch** if at most 15 points above; **At risk** if more than 15 above;
  **Out of reach** if required is over 100%. **Achieved** or **Missed** once nothing is left to
  sit; "Set — no data yet" before any marks exist.
- **Mistake type** (first match wins): Not attempted (blank), Silly error flagged (student flag),
  Silly loss (at least 70% of the class scored 60%+ of the question but the student scored under
  40%), Time pressure (paper shows time pressure, question in the last third, student below the
  class average), Concept gap (student's share 25+ points below the class average), else OK.
- **Time pressure** on a paper: at least 3 questions, last third 20+ points below the rest, and
  that drop 15+ points bigger than the class's.
- **Early warning**: CIA average below 40%, or badge At risk or Out of reach.

Every threshold lives in **`gaplens/config.py`**. Change it there and restart the app.

## Project layout

| Path | Purpose |
|---|---|
| `gaplens/app.py` | Entry point: boots and seeds the DB, sidebar, role-based navigation |
| `gaplens/config.py` | Every constant and threshold |
| `gaplens/core/db.py` | SQLite storage layer (no Streamlit) |
| `gaplens/core/analysis.py` | Pure grading, mistake-type, percentile and topic logic |
| `gaplens/core/suggestions.py` | Tip templates, ESE checklist review, search links, resource ordering |
| `gaplens/core/insights.py` | Combines db and analysis for the pages |
| `gaplens/core/marks_rules.py` | Paper validation, marks and ESE CSV parsing and templates |
| `gaplens/core/subject_rules.py` | Subject and topic input rules |
| `gaplens/core/seed.py` | Deterministic demo data and reset |
| `gaplens/core/gemini_client.py` | Optional Gemini calls (course plan, ESE script review) |
| `gaplens/ui/` | Theme and CSS, components, Plotly theme, profile, sidebar, flash, secrets |
| `gaplens/views/` | One script per page (thin, no business rules) |
| `gaplens/tests/` | pytest suite, including the seeded integration and UI smoke tests |

## Running the tests

```
cd gaplens
python -m pytest
```

The suite needs no Gemini key, no network and no existing `gaplens/data/gaplens.db`: every test
uses a temporary database.
