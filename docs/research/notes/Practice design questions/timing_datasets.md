# Public math practice logs with per-attempt solve times

Scope: datasets checked on 2026-11-02 for measuring how solve time changes with practice (per student, per skill, multi-step problems). Facts and descriptive statistics only, no modeling. Files were downloaded only from the official, openly reachable source of each dataset; anything behind a login, sign-up form, signed agreement or Kaggle key was recorded and skipped. Every file was read with `python -I` from a scratch directory, never from inside a data directory. Statistics cover all rows unless a section says it used a sample. No rows are reproduced here; ids are the datasets' own anonymized ids.

Data root: `/home/claude/data/<short-name>/`. Already present before this pass and not re-downloaded: `statics2011`, `ednet` (KT1 + `questions.csv`), `xes3g5m`, `assist09`, `eedi`, `maimemo`.

Terms reminder for all downloaded sets: none of them may be redistributed or committed to the Toishi repository. All are non-commercial. ASSISTments additionally asks that outcomes be made openly available, and Junyi's CC BY-NC-SA adds share-alike. Check these terms before shipping any table derived from them.

## Summary table

| Dataset (dir) | Status | Unit, rows | Students | Duration column(s), unit | Median | Zero / missing | Order by | Skill tags | Multi-step structure | Terms |
|---|---|---|---|---|---|---|---|---|---|---|
| ASSISTments 2009-10 skill builder (`assist0910_sb`) | downloaded | problem log, 346,860 (corrected file) | 4,217 | `ms_first_response`, `overlap_time` (ms) | 18.3 s / 23.2 s | 0.09% / 0% and 0.05% / 0% | `order_id` only (no timestamps) | `skill_id` on 81.6% of rows | scaffold sub-problems (`original=0`), 20.6% of rows | ASSISTments site terms |
| ASSISTments 2012-13 (`assist1213`) | downloaded | problem log, 6,123,270 | 46,674 | `ms_first_response` (ms); `end_time - start_time`; per-action ms offsets in `actions` | 22.3 s; 26.9 s | 0% / 0%; 727 negative | `start_time` | `skill_id` on 44.3% of rows | scaffolds 5.0% of rows; every attempt/hint timed in `actions` | ASSISTments site terms |
| ASSISTments 2019-20 school year (`assist1920`) | downloaded | problem log, 20,752,836; actions, 95,866,415 | 277,512 | `time_on_task` (s); action timestamps in `slogs` | 36.3 s | 0% / 1.86% | `start_time` (parse as UTC); action `timestamp` | Common Core codes (`pdets.skills`) on 33.4% of rows | action log per problem (attempts, help); no scaffold rows | ASSISTments Data Terms of Use (2020) |
| ASSISTments online experiments 2019-21 (`assist_exp2021`) | downloaded | problem log, 771,386; actions, 3,708,299 | 45,372 | `time_on_task`, `first_response_or_request_time` (s) | 40.3 s; 31.6 s | 0% / 3.0%; 0% / 4.2% | `start_time`; action `timestamp` | none | scaffold rows 6.8%; `problem_part` 1-4 | ASSISTments Data Terms of Use (2020) |
| Junyi Academy 2018-19 (`junyi2019`) | downloaded | attempt, 16,217,311 | 72,758 | `total_sec_taken` (s, capped at 1,800) | 21 s | 0.22% / 0% | `timestamp_TW` (15-min buckets), then `problem_number` | exercise `ucid` + 4-level hierarchy | none (single problems) | CC BY-NC-SA 4.0 |
| EdNet-KT2 (`ednet_kt2`) — TOEIC, not math | downloaded | action, 56,360,602 | 297,444 | derived: bundle enter→submit, enter→each respond (ms) | 24.6 s; 20.9 s (5,000-user sample) | 0% / 0% (sample) | `timestamp` (ms, shifted) | `tags`, `part` via `ednet/questions.csv` | bundles of 1-5 questions | CC BY-NC 4.0 |
| KDD Cup 2010 (Algebra I 2005-06, 2006-07; Bridge to Algebra 2006-07; 2008-09 challenge sets) | needs login | step | — | `Step Duration (sec)` and 4 step timestamps | — | challenge sets: durations all 0 (FAQ) | step times | KC models | steps within problems | DataShop terms |
| ASSISTments 2017 competition | needs sign-up + terms | action | — | `timeTaken` (s), `startTime`/`endTime` (UNIX s) | — | — | timestamps | `skill` | scaffolds | competition terms |
| Junyi Academy 2015 (DataShop 1198) | needs login | attempt | — | `time_taken` (s), `time_taken_attempts` (s per attempt) | — | — | `time_done` (µs) | exercise | per-attempt times | DataShop terms; non-commercial |
| EdNet-KT3 / KT4 | not downloaded (no new solve times) | action | — | lecture/explanation enter→quit | — | — | — | — | — | CC BY-NC 4.0 |
| ASSISTments 2020-21 school year (OSF 7cgav) | open, not downloaded (3.6 GB) | same as 2019-20 | — | `time_on_task` (s) | — | — | — | — | — | ASSISTments Data Terms of Use (2020) |
| Other DataShop math sets, MATHia | needs login / none public | — | — | — | — | — | — | — | — | DataShop terms |
| Eedi NeurIPS 2020, NeurIPS 2022 | needs login; no duration column | answer / event | — | timestamps only (2020: to the minute) | — | — | — | constructs | — | competition terms |
| EDM Cup 2023 (ASSISTments) | needs Kaggle login + rules | action | — | action timestamps | — | — | — | — | — | competition rules |

---

## 1. ASSISTments 2009-2010 skill-builder data (`assist0910_sb`) — downloaded

- **Source.** Official page: <https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010>. Files are public Google Drive links on that page: the corrected file (`1NNXHFRxcArrU0ZJSb9BIL56vmUt5FhlE`) and the original (`0B2X0QD6q79ZJUFU1cjYtdGhVNjg`). Column definitions are at <https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data>.
- **License / terms.** The data page says "The dataset is free to use." The dataset page asks users to put its precise URL in any publication and to cite Feng, Heffernan & Koedinger (2009), UMUAI 19, 243-266. The site's terms page (<https://sites.google.com/site/assistmentsdata/termsofuseforusingdata>), "WPI Institutional Review Board approved", says "WPI is required to get your written agreement to not share any personally identifiable information. You also agree to not give that data to anyone else." Its list of conditions adds: "I will not use the data to discover personally identifiable information"; delete and report any PII found; "I agree to not give this data to anyone else. I will only use this data for the purpose I provide"; acknowledge ASSISTments in publications; "My data and algorithms will be made public in my papers I publish." The datasets index adds that if you find PII "you must delete it, and cannot use that." There is no form or gate: the files are public links. I treated this as terms to follow rather than an access gate. Whether to send WPI a written agreement before publishing anything is the owner's call.
- **Files (local).** `skill_builder_data_corrected_collapsed.csv`: 64,412,812 bytes, sha256 `162ef8d2…a6e5da`, 346,860 rows × 31 columns (the first column is an unnamed row index). `skill_builder_data.csv` (original): 83,201,940 bytes, sha256 `f22e3fb7…77dbdc`, 525,534 rows × 30 columns. Both sizes match what Drive reported.
- **Which file to use.** The page says duplicated records were found in the original. Measured: the original has 346,860 distinct `order_id`s across 525,534 rows. Multi-skill problems are repeated once per skill, and some records are repeated 20 or 46 times (391 `order_id`s appear 46 times). Time and count values are identical across the copies. The corrected file has one row per problem log, with multi-skill tags collapsed as `a_b`. Its `ms_first_response` equals the original's for every `order_id`. The heavily duplicated records carry most of the original file's zero `ms_first_response` values (0.89% of rows there, versus 0.09% in the corrected file).
- **Size (corrected file).** 4,217 students; 26,688 problems; 17,725 assistments (an assistment is one item, possibly with several main problems and scaffolds); 816 templates (similar questions); 3,521 assignments; 677 problem sets (`sequence_id`); 250 classes; 75 schools. All rows are skill builders (`type = MasterySection`; mastery = 3 correct in a row).
- **Steps.** 71,402 rows (20.6%) are scaffolding sub-problems (`original = 0`). These are shown when the student answers wrong or asks to "break this problem into steps", and 2,781 assistments have them. The other 275,458 rows are main problems.
- **Time columns.**
  - `ms_first_response`: "The time in milliseconds for the student's first response." The first action can be an answer or a help request (`first_action` 0/1/2, below). Rows with `attempt_count = 0` (7,213, or 2.08%) mostly have `first_action = 2` (6,283), so for them this is the time to a help request, not to an answer.
    - Median 18,344 ms (main problems 22,050; scaffold rows 8,719); p10 4.1 s, p90 88.1 s, p99 336 s.
    - Zero 310 (0.09%), negative 7, missing 0; maximum 84,076,920 ms (23.4 h); 151 rows over 1 h, 1,286 over 10 min.
  - `overlap_time`: documented only as "the student's overlap time" (ms).
    - It is never below `ms_first_response`. It equals it in 66.6% of all rows and in 91.4% of rows with one attempt and no hints, so it behaves like total time on the problem.
    - Median 23,218 ms; p90 117 s; p99 454 s; zero 190 (0.05%), negative 10, missing 0; maximum 84,076,925 ms.
- **Ordering.** There are **no timestamps**. `order_id` is "chronological", per the column definitions. The file is not sorted by it within students (23,107 of 342,643 consecutive same-student pairs go backwards), so sort by (`user_id`, `order_id`). Gaps between practice sessions cannot be measured.
- **First attempt and correctness.**
  - `correct` is 1 if the first attempt was correct, 0 if it was incorrect or help was asked (64.5% are 1).
  - `attempt_count`: median 1, max 3,824. `hint_count`: 82.7% zero. `bottom_hint` marks rows where the student viewed the bottom-out hint.
  - `first_action`: documented only as "attempt or ask for a hint". Values: 0 = 309,271, 1 = 31,273, 2 = 6,316. Reading 2 as a scaffold request is my inference: 2 dominates the rows with no attempt.
- **Skill / KC columns.** `skill_id` and `skill_name` (ASSISTments skills; 18.4% of rows have no skill). The corrected file has 149 distinct `skill_id` strings, counting combos like `1_13`. Also `opportunity` and `opportunity_original` (practice counts per skill), `template_id`, `sequence_id`.
- **Practice depth.** Rows per student: median 23, p90 192, max 1,383. Rows per student-skill: median 4, p90 15; 43.3% of pairs have 5 or more. The same problem is seen again in 4,599 of 342,081 student-problem pairs, so repeated practice is mostly on different problems of the same skill or template.
- **Other columns.** `tutor_mode` (tutor 346,601 / test 259), `answer_type`, `hint_total`, `assignment_id`, `student_class_id`, `teacher_id`, `school_id`, `answer_id`, `answer_text`.
- **Loading snippet.**

```python
import pandas as pd
p = "/home/claude/data/assist0910_sb/skill_builder_data_corrected_collapsed.csv"
df = pd.read_csv(p, encoding="latin-1", low_memory=False).drop(columns=["Unnamed: 0"])
df = df.sort_values(["user_id", "order_id"])            # order_id is chronological; there are no timestamps
df["first_s"] = df["ms_first_response"] / 1000          # ms -> s, time to first action (answer OR help request)
df["total_s"] = df["overlap_time"] / 1000               # behaves like total time on the problem (>= first_s)
df["skills"] = df["skill_id"].astype("string").str.split("_")  # multi-skill problems collapsed as "a_b"
df["opp"] = df.groupby(["user_id", "skill_id"]).cumcount() + 1  # or use the given 'opportunity' column
steps = df[df["original"] == 0]                         # scaffolding sub-steps of multi-step problems
```

## 2. ASSISTments 2012-2013 school data with affect (`assist1213`) — downloaded

- **Source.** <https://sites.google.com/site/assistmentsdata/datasets/2012-13-school-data-with-affect> (the older `/home/2012-13-school-data-with-affect` page points there). The file is a public Google Drive link on that page (`1cU6Ft4R3hLqA7G1rIGArVfelSZvc6RxY`). Drive shows its standard "too large to scan" notice; no login is involved.
- **License / terms.** Same ASSISTments site terms as section 1. The page asks for a citation of Wang, Heffernan & Heffernan (2015) if the affect columns are used, and Feng, Heffernan & Koedinger (2009) otherwise. Problem text is not included: "If you want access to the questions it is required that you ask Professor Heffernan… He will ask you agree to abide by that request." It was not requested.
- **Files (local).** `2012-2013-data-with-predictions-4-final.zip`: 576,365,408 bytes, sha256 `7bb18f93…572445`. It holds one CSV of 3,009,494,391 bytes; `unzip -t` passed. I kept the zip and did not extract it; pandas reads it directly.
- **Size.** 6,123,270 rows, each a unique `problem_log_id`. 46,674 students; 179,999 problems; 138,555 assistments; 96,403 templates; 189,760 assignments; 112,403 problem sets; 1,331 teachers; 661 schools. Dates run 2012-09-01 to 2013-08-31.
- **Steps.** 303,533 rows (5.0%) are scaffolding sub-problems (`original = 0`). Inside each row, the `actions` field is a multi-line, YAML-like list:
  - a `start` entry with an epoch-ms stamp;
  - then each `answer`, `hint`, `scaffold`, `resume`, `url` or `survey_response` action with its ms offset from the start (answers also carry correctness and the answer text);
  - then `end`.
  In the first 200,000 rows, records hold a median of 3 actions (p90 6, max 333). The first non-start offset equals `ms_first_response` in 98.8% of them, so per-attempt timing within a problem is available. `resume` entries mean the student left and came back.
- **Time columns.**
  - `ms_first_response` (ms): median 22,331 (main problems 23,283; scaffolds 9,764); p10 5.1 s, p90 117.7 s, p99 377.5 s. Zero 0, negative 13, missing 0; max 345,055,238 ms (about 4 days); 240 rows over 1 h.
  - `overlap_time` (ms) equals `ms_first_response` in 99.6% of rows (never below it). In this release it is therefore not a total-time measure, unlike in 2009-10.
  - `start_time` and `end_time` are datetime strings with second or sub-second precision. `end_time - start_time` has a median of 26.9 s, p90 148.7 s and p99 565.8 s, with 32,947 rows (0.54%) over 1 h. It has 727 negative values (0.01%) and extremes of about −274 to +302 days, so it needs cleaning.
- **Ordering.** Sort by (`user_id`, `start_time`, `problem_log_id`). File order is not chronological within students: 2.54M of 6.08M consecutive same-student pairs go backwards.
- **First attempt and correctness.**
  - `correct`: 1 = correct on the first attempt; 0 = saw the answer, used up partial credit, or answered wrong first. 5,323 rows hold fractional partial credit, and the page recommends treating anything below 1 as incorrect.
  - Also `first_action` (0 = 5,782,418, 1 = 305,009, 2 = 35,843; same reading as in section 1), `attempt_count` (median 1, max 29), `hint_count` (86.2% zero), `bottom_hint`.
- **Skill / KC columns.** `skill_id` and `skill` (265 ids / 198 names). Only 44.3% of rows have a skill (3,411,457 missing). Also `template_id`, `sequence_id`, and the problem-set type `type` (LinearSection 3.35M, MasterySection = skill builder 1.87M, random-order sections 0.90M).
- **Practice depth.** Problem logs per student: median 49, p90 345, max 5,562. Rows per student-skill (tagged rows): median 4, p90 16; 44.0% of pairs have 5 or more. The same problem is seen again in 206,622 of 5,894,902 student-problem pairs.
- **Other columns.** Four affect-detector confidences, `problem_type`, `tutor_mode`, `answer_id`, `answer_text`, `assignment_id`, `student_class_id`, `teacher_id`, `school_id`, `position`, `base_sequence_id`.
- **Loading snippet.** A full load of these 16 columns needs roughly 3 GB of RAM; use `chunksize=` if tight.

```python
import pandas as pd
z = "/home/claude/data/assist1213/2012-2013-data-with-predictions-4-final.zip"
cols = ["problem_log_id", "user_id", "problem_id", "assistment_id", "skill_id", "skill", "template_id", "original",
        "start_time", "end_time", "ms_first_response", "overlap_time", "correct", "attempt_count", "hint_count", "first_action"]
df = pd.read_csv(z, compression="zip", usecols=cols)  # 6.1M rows; add "actions" for per-attempt ms offsets
for c in ["start_time", "end_time"]:
    df[c] = pd.to_datetime(df[c], format="mixed")
df = df.sort_values(["user_id", "start_time", "problem_log_id"])
df["first_s"] = df["ms_first_response"] / 1000                        # time to first action
df["wall_s"] = (df["end_time"] - df["start_time"]).dt.total_seconds()  # problem open->close; has negatives and huge outliers
df["correct_first"] = (df["correct"] == 1).astype(int)                # 'correct' holds partial credit for a few rows
```

## 3. ASSISTments 2019-2020 school year (`assist1920`) — downloaded

- **Source.** OSF "ASSISTments 2019-2020 School Year Dataset", <https://osf.io/q7zc5/>, DOI 10.17605/OSF.IO/Q7ZC5. Downloaded `2019-2020_school_year.zip` (<https://osf.io/download/7sftn/>), `ASSISTments Dataset Description.pdf` (saved as `ASSISTments_Dataset_Description.pdf`) and `license.txt`. The project also offers `pre_shutdown.zip` and `post_shutdown.zip`, which split the same year at the 2020-03-13 school closures; they were not downloaded. Per the wiki, the data was used for Prihar et al. (2021), "Student Engagement During Remote Learning", LAK21 companion proceedings.
- **License / terms.** `license.txt` holds the ASSISTments Data Terms of Use (Effective October 30, 2020), byte-identical to section 4's copy, where the points are listed. OSF lists the license as "Other". Cite ASSISTments and the dataset DOI. The data may not be redistributed.
- **Files (local).** Zip of 1,265,698,754 bytes (sha256 `844555110c1e…a82f89`). It holds 10 CSVs, 9,963,633,307 bytes uncompressed: `plogs.csv` 1.96 GB, `slogs.csv` 7.64 GB, `alogs.csv` 190 MB, `tlogs.csv` 115 MB, and the detail tables `adets`, `sdets`, `pdets`, `cdets`, `tdets`, `ddets`. Kept zipped; read members with `zipfile`. A full read of `slogs` takes roughly 25 minutes here.
- **Size.**
  - `plogs` (one row per student × problem, scaffolds excluded): 20,752,836 rows; 277,512 students; 134,655 problems; 197,022 assignments; 2,505,225 assignment logs (`log_id` = one student doing one assignment). 508 rows repeat a (`log_id`, `problem_id`) pair.
  - `slogs` (one row per action): 95,866,415 rows.
  - `pdets`: 134,655 rows but only 134,264 distinct `problem_id`s, despite the documented one entry per problem. De-duplicate before joining.
  - `adets`: 197,022 assignments, of which 184,313 are problem sets and 12,709 skill builders. 938,503 `plogs` rows come from skill builders and 19.8M from problem sets.
  - Dates: problem start times run 2019-09-02 to 2020-10-29. Only assignments started before July 2020 are included, but their later problems are kept.
- **Steps.** `plogs` holds main problems only; tutoring is recorded as actions. `slogs` action counts:

  | Action | Count |
  |---|---|
  | `problem_started` | 20,761,746 |
  | `problem_finished` | 20,406,502 |
  | `continue_selected` | 18,192,586 |
  | `correct_response` | 15,291,169 |
  | `wrong_response` | 7,163,805 |
  | `open_response` | 5,045,591 |
  | `answer_requested` | 2,546,833 |
  | `assignment_started` | 2,497,719 |
  | `assignment_finished` | 2,129,728 |
  | `assignment_resumed` | 1,446,211 |
  | `tutoring_requested` | 384,525 |

  `work_submitted` is documented but never occurs. Hints, scaffolds and explanations are not distinguished: all are `tutoring_requested`. The per-problem action sequence therefore times every attempt and help request, but there are no scaffold sub-problem rows.
- **Time columns.**
  - `plogs.time_on_task`: "An estimate of the number of seconds the student spent solving the problem based on an aggregation of student_log information."
    - Median 36.3 s (19.6 s when the first answer was correct, 64.0 s when not); p10 6.1, p25 13.3, p75 105.4, p90 280.8, p99 1,622.7 s; max 23,377 s (6.5 h).
    - Missing 1.86% (mostly unfinished problems: 83.2% of not-completed rows lack it); zero 0; negative 0. 1.64% are under 1 s, 4.05% over 10 min and 0.02% over 1 h.
  - Check against `slogs`: in the first 3,000,000 `slogs` rows, 621,698 problem instances matched `plogs`. For them, `time_on_task` was within 1 s of `problem_started → problem_finished` for 96.97%, shorter for 3.02%, and never longer. In the same sample, started-to-finished had a median of 48.2 s but a p99 of 100,863 s. So `time_on_task` removes the long away gaps seen in the raw action timestamps; I did not check exactly how it is computed.
  - Time to first action: from `slogs`, `problem_started →` the first `correct_response`, `wrong_response`, `open_response`, `tutoring_requested` or `answer_requested`. Median 39.2 s and p90 289.5 s in the sample, with no negatives. It exceeds `time_on_task` by more than 1 s for 2.5% of problems.
  - `alogs.time_on_task` sums the problem times per assignment. `sdets` and `adets` carry per-student and per-assignment mean time on task.
- **Timestamps.** `start_time` (plogs) and `timestamp` (slogs) are strings with microseconds and an explicit UTC offset, and **the format switches partway through each file**.
  - In `plogs`, rows 0 to 5,999,999 carry `-04:00` or `-05:00`, matching US Eastern daylight and standard time, and every row from 6,000,000 on carries `+00:00`. Overall that is 14.75M UTC rows, 2.74M at `-04:00` and 3.26M at `-05:00`.
  - `slogs` switches to `+00:00` after its first 9,000,000 rows.
  - Absolute times agree when parsed with `utc=True`; naive parsing would mix UTC with local clock time. For local time of day, convert to US Eastern; that this is the intended zone is an inference from the offsets.
- **Ordering.** Sort `plogs` by (`student_id`, `start_time`). The file is nearly in order: 165,846 of 20,475,324 consecutive same-student pairs go backwards, with no exact ties. Sort `slogs` by `timestamp` within `log_id`, after parsing it with `utc=True`; sorting the raw strings would break across the offset switch.
- **First attempt and correctness.**
  - `correct` is True or False for whether "the student's first answer to the problem was correct". It is **missing for 25.8% of rows**: incomplete problems without a teacher grade, and ungraded open responses. Counts: 10,555,682 True, 4,832,846 False, 5,364,308 missing.
  - Also `attempt_count` (median 1, mean 1.33, max 724), `answer_before_tutoring`, `fraction_of_hints_used`, `answer_given` (12.2% True) and `problem_completed` (1.7% False).
- **Skill / KC columns.** `pdets.skills` is a list of Common Core standard codes (363 distinct). Only 34.5% of problems are tagged, covering 33.4% of `plogs` rows, and 4.0% of problems carry more than one code. `pdets` also has `problem_type` (algebraic expression, number, ungraded open response, multiple choice, …), `content_source` (e.g. Illustrative Mathematics, Engage NY, Eureka, Open Up, ASSISTments skill builders) and `tutoring_types`.
- **Practice depth.** Problem logs per student: median 29, p90 194, max 3,288. Rows per student-skill (first listed code): median 4, p90 16; 42.3% of 975,207 pairs have 5 or more. The same problem is seen again in 267,424 of 20,446,759 student-problem pairs.
- **Other tables.** `alogs` (assignment start, completion, mean correctness), `sdets` (per-student prior counts and means), `tlogs` (teacher report views and grading actions), and `cdets`, `tdets`, `ddets` (class, teacher, district: US state, opportunity-zone status).
- **Loading snippet.** The 10 columns below take about 100 MB per million rows, roughly 2 GB in all. Merging the skill lists into every row would take about 5 GB, so map them per analysis instead.

```python
import ast, zipfile
import pandas as pd
zf = zipfile.ZipFile("/home/claude/data/assist1920/2019-2020_school_year.zip")
cols = ["log_id", "student_id", "assignment_id", "problem_id", "start_time", "time_on_task", "attempt_count", "correct", "answer_given", "problem_completed"]
parts = []
for ch in pd.read_csv(zf.open("plogs.csv"), usecols=cols, chunksize=2_000_000):   # 20.8M rows in total
    ch["start_time"] = pd.to_datetime(ch["start_time"], utc=True, format="mixed")  # offsets differ by row: parse as UTC
    ch["correct"] = ch["correct"].map({True: 1.0, False: 0.0})                     # NaN = not graded (25.8% of rows)
    parts.append(ch)
plogs = pd.concat(parts, ignore_index=True).sort_values(["student_id", "start_time"])  # time_on_task: seconds
pdets = pd.read_csv(zf.open("pdets.csv"), usecols=["problem_id", "skills", "problem_type"]).drop_duplicates("problem_id")
pdets["skills"] = pdets["skills"].fillna("[]").map(ast.literal_eval)  # Common Core codes; [] = untagged
```

## 4. ASSISTments online experiments 2019-2021 (`assist_exp2021`) — downloaded

- **Source.** OSF project "Exploring Common Trends in Online Educational Experiments Data", <https://osf.io/59shv/>. It is the data for Prihar, Syed, Ostrow, Shaw, Sales & Heffernan (2022), EDM. Downloaded: `experiment_dataset_2021-09-23.zip` (<https://osf.io/download/wp438/>), its description PDF, `license.txt`, `experiment_descriptions.csv` and `experiment_conditions.csv`. The derived `processed_experiment_data.csv` and the paper were not downloaded.
- **License / terms.** `license.txt` holds the "ASSISTments Data Terms of Use, Effective October 30, 2020", identical to the one in section 3:
  - cite ASSISTments and the dataset;
  - "You will not use or reference ASSISTments data for any commercial purpose";
  - "You will make any and all outcomes available to the public using free and open access practices";
  - no de-anonymization attempts;
  - "You will not redistribute ASSISTments data. You may distribute code that processes or manipulates the data, but you may not redistribute the data itself. If working with collaborators, all team members must access the dataset from its original source";
  - if users can be identified, email research@assistments.org, delete the data, and halt or redact publication;
  - indemnify WPI and The ASSISTments Foundation.
  Use is accepted on download; there is no gate.
- **Files (local).** Zip of 83,124,379 bytes (sha256 `06d8c992…3266ea`). It holds 88 per-experiment zips, each with `exp_plogs.csv`, `exp_slogs.csv`, `exp_alogs.csv` and `priors.csv`. The snippet reads them in memory; nothing is extracted.
- **Size.** `exp_plogs`: 771,386 problem rows; 45,372 students (20,895 of them in more than one experiment); 7,403 problems; 88 experiments; 95,725 student-experiment pairs. `exp_slogs`: 3,708,299 action rows. Dates run 2019-02-04 to 2021-09-22. Problem rows per student-experiment: median 7, p90 14, max 238. Every student does one randomized assignment per experiment, labelled by `problem_condition`: Control, Treatment n, Posttest, Nonexperimental or Unknown.
- **Steps.** 52,637 rows (6.8%) are scaffold sub-problems (`scaffold_id` set). `problem_part` is 2-4 for 7,621 rows of multi-part problems. Action types in `exp_slogs`:

  | Action | Count |
  |---|---|
  | `problem_started` | 759,855 |
  | `problem_finished` | 732,105 |
  | `correct_response` | 668,432 |
  | `continue_selected` | 626,922 |
  | `wrong_response` | 396,973 |
  | `hint_requested` | 163,545 |
  | `answer_requested` | 102,291 |
  | `assignment_started` | 95,979 |
  | `assignment_finished` | 65,849 |
  | `assignment_resumed` | 60,093 |
  | `scaffolding_requested` | 34,001 |
  | `open_response` | 2,253 |
  | `explanation_requested` | 1 |

  Timestamps carry UTC offsets that mix daylight-saving and standard time, so parse them with `utc=True`.
- **Time columns.**
  - `time_on_task`: documented as "The total seconds, not including time the student was not using the ASSISTments tutor". Median 40.3 s; p10 7.7, p90 333.5, p99 186,323 s; max 25.5M s. Missing 2.99%, zero 0, negative 0.
    - **It does not behave as documented.** It tracks wall-clock `end_time - start_time`: it is at most 1 s above it in 97.8% of rows, below 90% of it in only about 0.3%, and below half of it in 0.13%.
    - Problems that span 2 sessions (`session_count = 2`, 37,613 rows) have a median of 3,473 s, and 3 or more sessions a median of 65,911 s.
    - Single-session rows (731,161) look sane: median 37.0 s, p99 1,364 s, 0.33% over 1 h.
  - `first_response_or_request_time` (s): "time … to make their first attempt to solve the problem or request tutoring". Median 31.6 s, p90 225.7 s; missing 4.21%. It is at most `time_on_task` in 99.93% of rows.
  - `start_time` and `end_time` per problem (`end_time` missing for 28,388 unfinished problems). `exp_alogs` has per-assignment start and end times, and `priors.csv` holds students' prior median first-response time and time on task.
- **Ordering.** `start_time` per problem; action `timestamp`; `assistments_reference_problem_log_id` and `assistments_reference_action_log_id` can help sort ties.
- **First attempt and correctness.**
  - `correct` is True or False for correct "on their first try with no tutoring": 471,698 True, 277,703 False, 21,985 missing.
  - Also `reported_score` (partial credit), `answer_before_tutoring`, `attempt_count`, `hints_available` / `hints_given`, `scaffold_problems_available` / `scaffold_problems_given`, `explanation_given`, `answer_given`, `first_answer` (open responses redacted).
- **Skill / KC columns.** None. Only `problem_id` and `experiment_id` (with `experiment_descriptions.csv` and `experiment_conditions.csv`). This is the main limit for per-skill speed-up work, and sequences are short.
- **Loading snippet.**

```python
import io, zipfile
import pandas as pd
outer = zipfile.ZipFile("/home/claude/data/assist_exp2021/experiment_dataset_2021-09-23.zip")
def table(name):  # exp_plogs | exp_slogs | exp_alogs | priors, concatenated over the 88 experiments
    out = []
    for inner_name in outer.namelist():
        inner = zipfile.ZipFile(io.BytesIO(outer.read(inner_name)))
        out.append(pd.read_csv(inner.open([n for n in inner.namelist() if n.endswith(name + ".csv")][0])))
    return pd.concat(out, ignore_index=True)
plogs = table("exp_plogs"); plogs["start_time"] = pd.to_datetime(plogs["start_time"], utc=True, format="mixed")
plogs = plogs.sort_values(["student_id", "start_time"])  # time_on_task, first_response_or_request_time: seconds
one_session = plogs[plogs["session_count"] == 1]         # multi-session rows include time away (see above)
```

## 5. Junyi Academy Online Learning Activity Dataset, 2018-08 to 2019-07 (`junyi2019`) — downloaded

- **Source.** Junyi Academy's own Kaggle account: <https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy>, version 9, updated 2020-05-13. It was downloaded through Kaggle's official API endpoint `https://www.kaggle.com/api/v1/datasets/download/junyiacademy/learning-activity-public-dataset-by-junyi-academy` without credentials. Kaggle's own client documentation (<https://github.com/Kaggle/kagglehub>) says "Authenticating is **only** needed to access public resources requiring user consent or private resources". This is a public dataset with no consent step, so no key was needed and nothing was worked around. The notebooks API does require a login (it returned 401) and was not used.
- **License / terms.** CC BY-NC-SA 4.0 (Kaggle metadata `CC-BY-NC-SA-4.0`). The description adds:
  - it is usable "under the following terms provided by the [policy](https://www.junyiacademy.org/about/policy). Everyone using this dataset should follow the Creative Commons BY-NC-SA 4.0 license";
  - trademarks and logos are excluded;
  - "Anyone using this dataset should not distort the information";
  - Junyi "could ask the user of the dataset to share their feedback and research results with the community".
  Requested citation: P. J. Chen, M. E. Hsieh, T. Y. Tsai, *Junyi Online Learning Dataset: A large-scale public online learning activity dataset from elementary to senior high school students*, 2020.
  The linked policy page returned HTTP 404 on 2026-11-02, as did a few likely alternatives, so the license and the description text above are what is on record.
- **Files (local).** `junyi2019_kaggle_v9_archive.zip`: 1,615,467,938 bytes, sha256 `d3272a56…a3e7d9`. It holds `Log_Problem.csv` (3,020,754,300 bytes), `Info_Content.csv` (389,397) and `Info_UserData.csv` (6,363,597). Kept zipped.
- **Size.** 16,217,311 attempts (the description says 16,217,311); 72,758 students (the description says 72,630; `Info_UserData` has 72,758 rows); 1,326 exercises (`ucid`); 25,785 problems (`upid`). Every exercise is math (`subject = math`). Attempts by stage: elementary 12.54M, junior high 3.66M, senior high 22k. `Info_UserData` holds per-student demographics; they were not profiled.
- **Steps.** None. Each row is one problem; the attempts within it are only counted (`total_attempt_cnt`), not timed.
- **Time column.** `total_sec_taken`, in seconds per problem (no published definition; inferred from the name and values).
  - Median 21 s (18 s when correct, 31 s when incorrect); p10 6, p90 92, p99 357.
  - Zero 35,883 (0.22%), missing 0, negative 0.
  - Maximum exactly 1,800, and 21,735 rows (0.134%) sit at 1,800, so values appear capped at 30 minutes. Over 10 min: 0.46%.
- **Timestamp.** `timestamp_TW` is a string with a " UTC" suffix, despite the "TW" name. **Every value is rounded to a 15-minute mark** (100% of rows have minutes 00/15/30/45 and seconds 00). Range 2018-08-01 07:45 to 2019-08-01 00:00. 98.8% of attempts share their student and 15-minute bucket with another attempt (median 6 per bucket, max 223).
- **Ordering.** Time alone cannot order attempts inside a bucket. Within one student, exercise and `exercise_problem_repeat_session`, `problem_number` is unique and never runs against the timestamps (checked on a 10% student sample). It is the problem's position in that session, starting at 1 in 77.7% of sessions; 24.4% of sessions have gaps. `exercise_problem_repeat_session` counts sessions on an exercise: later sessions start at or after earlier ones in 99.4% of cases, with a median gap of 22.5 h. So sort by (`uuid`, timestamp, `ucid`, `exercise_problem_repeat_session`, `problem_number`). The order of different exercises inside one 15-minute bucket is unknown. File order is not chronological.
- **First attempt and correctness.** `is_correct` is True for 70.4% of rows. No published definition says whether it means first-attempt correct, but `total_attempt_cnt` (median 1, max 1,000) is recorded alongside it. Also `used_hint_cnt` and `is_hint_used` (22.8% used a hint). `level` takes values 0-4, read here as the proficiency level on the exercise (inferred). `is_upgrade` and `is_downgrade` are non-empty on 1.78M rows (upgrade True on 1,758,026, downgrade True on 23,267); by their names they mark level changes, but no definition is published.
- **Skill / KC columns.** `ucid` (exercise = skill unit; 1,326 used). `Info_Content` maps each exercise to `difficulty` (easy / normal / hard / unset), `learning_stage` and a 4-level curriculum hierarchy (`level1_id`..`level4_id`: 1 / 10 / 42 / 171 distinct values). The names are Chinese in `content_pretty_name`.
- **Practice depth.** Attempts per student: median 59, p90 587, max 11,813. Attempts per student-exercise: median 6, p90 18; 82.5% of 1.73M pairs have 5 or more. The same problem is seen again in 1,672,280 of 13,785,094 student-problem pairs (12.1%).
- **Loading snippet.**

```python
import zipfile
import pandas as pd
zj = zipfile.ZipFile("/home/claude/data/junyi2019/junyi2019_kaggle_v9_archive.zip")
log = pd.read_csv(zj.open("Log_Problem.csv"))           # 16.2M rows (~3 GB); use usecols=/chunksize= if RAM is tight
content = pd.read_csv(zj.open("Info_Content.csv"))      # ucid -> subject, difficulty, learning_stage, level1..4_id
log["ts"] = pd.to_datetime(log["timestamp_TW"].str.replace(" UTC", "", regex=False))  # rounded to 15 minutes
log = log.merge(content[["ucid", "subject", "difficulty", "learning_stage", "level4_id"]], on="ucid", how="left")
log = log.sort_values(["uuid", "ts", "ucid", "exercise_problem_repeat_session", "problem_number"])  # see ordering
log["sec"] = log["total_sec_taken"]                     # seconds per problem; 1,800 = cap
```

## 6. EdNet-KT2 (`ednet_kt2`) — downloaded (TOEIC English, not math)

- **Why it was downloaded.** It adds solve-time detail that KT1 lacks.
  - I read the KT1 files of the sampled users until 200,224 solving sessions had been collected; 28,230 of those sessions held more than one question. In 95.5% of the multi-question sessions every question carries the **same** `elapsed_time`, so per-question time inside a bundle is not in KT1.
  - KT2 records `enter` (bundle shown), every `respond` (an answer choice selected, with timestamp; repeated responses mean the answer was changed) and `submit`. The README says KT1's features "can be fully recovered" from KT2.
  - KT2 also records the study mode (`source`: sprint, diagnosis, adaptive_offer, review_quiz, review, my_note, tutor), which marks review practice.
- **Source.** <https://github.com/riiid/ednet>. Official download link `bit.ly/ednet-kt2` → Google Drive file `1qQQshbzyULW5RjMi7u-IhUr2dT_6uMXA`, public, no login.
- **License.** "publicly released under Creative Commons Attribution-NonCommercial 4.0 International license for research purposes" (README).
- **Files (local).** `EdNet-KT2.zip`: 555,757,666 bytes, sha256 `bb5dec57…3abff5`. It holds 297,444 per-user CSVs (`KT2/u<id>.csv`, 2,413,417,542 bytes uncompressed) plus one `__MACOSX` entry. Kept zipped. All files share the header `timestamp, action_type, item_id, source, user_answer, platform`. Total 56,360,602 action rows.
- **Time columns.** `timestamp` in Unix ms, "shifted by fixed values" for security, so gaps are real but dates are not. Derived figures from a random sample of 5,000 users (1,043,784 actions, 304,577 bundles):
  - `enter → submit` per bundle: median 24,602 ms; p10 13.2 s, p90 80.5 s, p99 274.6 s; no zero or negative values; 0.005% over 1 h. No `enter` was followed by another `enter` before its `submit`.
  - `enter → first respond` per question: median 20,885 ms.
  - 15.5% of questions were answered more than once before submit.
  - For comparison, KT1 `elapsed_time` in those 200,224 sessions has a median of 21,000 ms and 0.40% zeros.
- **Ordering.** Sort each user file by `timestamp` (stable).
- **Correctness.** Not stored. Compare the last `respond` per question before `submit` with `correct_answer` in `/home/claude/data/ednet/questions.csv`.
- **Skill / KC columns.** `questions.csv` gives `bundle_id`, `part` (TOEIC part 1-7) and `tags` (`;`-separated).
- **Steps.** Bundles: questions that share a passage or audio clip and are submitted together. In `questions.csv`, 8,006 of 9,534 bundles hold 1 question; the rest hold 2 (95), 3 (885), 4 (422) or 5 (126).
- **Loading snippet.**

```python
import zipfile
import pandas as pd
zk = zipfile.ZipFile("/home/claude/data/ednet_kt2/EdNet-KT2.zip")
users = [n for n in zk.namelist() if n.startswith("KT2/u") and n.endswith(".csv")]   # 297,444 per-user files
q = pd.read_csv("/home/claude/data/ednet/questions.csv")  # question_id -> bundle_id, correct_answer, part, tags
def load(name):
    d = pd.read_csv(zk.open(name)).sort_values("timestamp", kind="stable")
    d["user_id"] = name[4:-4]
    return d                                              # enter/submit carry bundle ids, respond carries question ids
acts = pd.concat([load(n) for n in users[:1000]], ignore_index=True)  # timestamps: ms (shifted by a fixed offset)
```

## 7. KDD Cup 2010 Educational Data Mining Challenge — needs login

- **Official page.** <https://pslcdatashop.web.cmu.edu/KDDCup/downloads.jsp>: "Note: You must be logged in to download data. Log in or create an account." DataShop's public list also has "Data Files for KDD Cup 2010" (dataset 4524), which needs a login too. Not downloaded. Unofficial mirrors exist but were not used: DataShop's terms require every user to hold their own account.
- **Terms.** Cite Stamper, Niculescu-Mizil, Ritter, Gordon & Koedinger (2010), *[data set name]*, development or challenge data set from KDD Cup 2010 (downloads page). DataShop Terms of Use (<https://pslcdatashop.web.cmu.edu/Terms>):
  - "Data is for research purposes, not commercial purposes";
  - no de-anonymization;
  - "You will not distribute data obtained from DataShop. If you are collaborating with others who require access to the data, they must establish accounts with DataShop and agree to these terms";
  - indemnification.
- **Contents (from <https://pslcdatashop.web.cmu.edu/KDDCup/rules_data_format.jsp>).** Carnegie Learning Cognitive Tutor data: Algebra I 2005-2006, Algebra I 2006-2007 and Bridge to Algebra 2006-2007 (development sets, with `_master.txt` labels), plus Algebra I 2008-2009 and Bridge to Algebra 2008-2009 (challenge sets). Each row is one student-step. Columns:
  - `Anon Student Id`, `Problem Hierarchy` (unit, section), `Problem Name`, `Problem View` (times this problem was seen), `Step Name`;
  - `Step Start Time`, `First Transaction Time`, `Correct Transaction Time`, `Step End Time`;
  - `Step Duration (sec)` ("calculated by adding all of the durations for transactions that were attributed to the step"; null if the start time is null), `Correct Step Duration (sec)`, `Error Step Duration (sec)`;
  - `Correct First Attempt` (1/0), `Incorrects`, `Hints`, `Corrects`;
  - `KC(model)` and `Opportunity(model)`, `~~`-separated. The challenge sets have extra KC models: SubSkills, KTracedSkills, Rules.
- **Known noise (FAQ, <https://pslcdatashop.web.cmu.edu/KDDCup/FAQ/>).**
  - In the challenge training files "almost every line has the same start and end time. The step duration is also equal to 0… this is the case for all challenge data set training files". **Only the three development sets have usable durations.**
  - Rows are ordered within a problem by the first correct transaction time, else the step end time. Steps can interleave.
  - There are duplicate keys (2,331 in Algebra 2008-09 train, 137 in Bridge 2008-09 train). Some KC names are truncated in Algebra I 2006-2007.
  - The challenge training files hold 8,918,055 (Algebra 2008-09) and 20,012,499 (Bridge 2008-09) keys.

## 8. ASSISTments 2017 Data Mining Competition (longitudinal) — needs sign-up and terms

- **Official page.** <https://sites.google.com/view/assistmentsdatamining/dataset>: "You can sign up to gain access to the dataset here [Google Form]. The link to your dataset will be sent to your email… you are allowed to publish paper on this dataset as long as you agree to our Terms of Use." The terms link points to `www.assistmentstestbed.org`, whose name does not resolve from this workspace. Not downloaded, because access requires the sign-up.
- **Contents (public column sheet, <https://docs.google.com/spreadsheets/d/1QVUStXiRerWbH1X0P11rJ5IsuU2Xutu60D1SjpmTMlk>).** Middle-school ASSISTments click-stream data, 2004-2007, at one row per action.
  - Ids and labels: `ITEST_id` (student), `actionId`, `skill`, `problemId`, `assistmentId`, `assignmentId`.
  - Times: `startTime` and `endTime` (UNIX seconds); `timeTaken` ("Time spent on the current step").
  - Outcomes: `correct`, `original`, `scaffold`, `hint`, `hintCount`, `hintTotal`, `bottomHint`, `attemptCount`, `problemType`.
  - About 40 engineered features (e.g. `totalFrTimeOnSkill`, `timeSinceSkill`, `frTimeTakenOnScaffolding`), affect predictions, and student-level averages.

## 9. Junyi Academy Math Practicing Log 2015 (DataShop 1198) — needs login

- **Official page.** <https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=1198>, plus dataset 1275, "Partial Samples". Its Files tab shows "Log in to start analyzing data"; DataShop downloads need an account. Not downloaded.
- **Terms.** DataShop terms (section 7). The EduData description (<https://edudata.readthedocs.io/en/dev/build/blitz/junyi/junyi.html>) adds "Any form of commercial usage is not allowed!" and a citation: Chang, Hsu & Chen, "Modeling Exercise Relationships in E-Learning: A Unified Approach", EDM 2015.
- **Contents (per that description).**
  - `junyi_ProblemLog_original.csv`: `time_done` (Unix µs), `time_taken` (s), `time_taken_attempts` (s per attempt, `&`-joined), `hint_time_taken_list`, `count_attempts`, `count_hints`, `correct`, `hint_used`, `earned_proficiency`, `problem_number`, `topic_mode`, `review_mode`, `suggested`.
  - `junyi_Exercise_table.csv`: per-exercise `seconds_per_fast_problem` (an expert-set "fast" threshold) and a prerequisite graph.
  - A 9.1 GB PSLC-format transaction file.
  - Its summary shows a negative minimum `time_taken` (about −5.05e8), so cleaning would be needed.
- Of the two Junyi releases, only this one times each attempt within a problem, and it is gated. Per-attempt timing is openly available elsewhere: ASSISTments 2012-13 `actions`, the 2019-20 `slogs` and the experiments' `exp_slogs`.

## 10. EdNet-KT3 and KT4 — not downloaded (no new solve times)

KT3 (`bit.ly/ednet-kt3` → Drive, `EdNet-KT3.zip`, 727 MB) adds `enter` and `quit` actions for explanations and lectures to KT2. The README suggests using them to measure "the time each student have spent studying a given material". These are study times, not solve times. KT4 adds `erase_choice`, `undo_erase_choice`, play/pause, payment and coupon actions. Same CC BY-NC 4.0 license.

## 11. ASSISTments 2020-2021 school year (OSF 7cgav) — open, not downloaded

<https://osf.io/7cgav/> has the same 10-table format and description PDF (identical size) as section 3, plus a `license.txt` the same size as the 2020 terms. It comes as four zips: `aug_to_oct` 1,414,789,623 bytes, `nov_to_jan` 1,080,844,988, `feb_to_apr` 898,253,436 and `may_to_june` 198,856,869, about 3.59 GB in total. Not downloaded to save disk space (about 11 GB free when checked). It can be fetched with `https://osf.io/download/<id>/` (ids `gny98`, `f6rcj`, `nrd4k`, `qevpu`) if a second year is wanted.

## 12. Other DataShop public math datasets and MATHia — need login

DataShop's public list (<https://pslcdatashop.web.cmu.edu/index.jsp?datasets=public>, 215 datasets, browsable without login) includes these math or close-to-math sets. DataShop transaction exports normally carry per-transaction times and durations; that was not verified for each set. All need an account to download, under the terms in section 7:

| Dataset | DataShop id |
|---|---|
| Geometry Area (1996-97) | 76 (and variants) |
| Geometry Angles - Fox Chapel 1998 | 122 |
| Assistments Math 2004-2005 | 92 |
| Assistments Math 2005-2006 | 120 |
| Assistments Math 2006-2007 | 339 |
| Fraction Addition and Multiplication | 1190 |
| Fraction Addition and Multiplication, Blocked vs. Interleaved | 1706 |
| Mathan - Fostering the Intelligent Novice | 706, 1007 |
| S18 - College Algebra & Trig | 3090 |
| Erroneous Examples (decimals; 2011-2019 studies) | several |
| Perceptual Fluency in Geometry | 315, 460 |
| Digital Games for Improving Number Sense | 445 |
| Statistics Cloze Practice | several |
| Data for "Will They Try Again" | 6769 |

No MATHia dataset is in the public list, and I found no open MATHia download elsewhere.

## 13. Eedi competitions — need login, and no duration column

- **NeurIPS 2020 Education Challenge.** Data is on CodaLab (<https://competitions.codalab.org/competitions/25449>, linked from <https://www.eedi.com/data-and-competitions>). The guide (<https://arxiv.org/abs/2007.12061>) says "DateAnswered: Time and date that the question was answered, to the nearest minute." Minute resolution gives no usable solve time. Not downloaded.
- **NeurIPS 2022 CausalML Challenge.** <https://codalab.lisn.upsaclay.fr/competitions/5626>: "You must be logged in to participate in competitions." The guide (<https://arxiv.org/abs/2208.12610>) shows quiz event rows (`Checkin`, `CheckinRetry`, `Lesson`, `Checkout`, `CheckoutRetry`) with a `Timestamp` printed to the second and a `ConstructId`. Per-question time could only be inferred from gaps between events, which include lessons. Not downloaded.
- Eedi's other public sets (misconception graph, which is already in `eedi`; tutoring dialogues on Hugging Face) have no timing.

## 14. Others checked

- **EDM Cup 2023 (ASSISTments click-stream).** Hosted only as a Kaggle competition (<https://www.kaggle.com/competitions/edm-cup-2023>, linked from <https://educationaldatamining.org/edm2023/?p=820>). Competition data needs a Kaggle login and acceptance of the rules. Not downloaded.
- **"Will They Try Again?" RCT data (OSF ftzgh, <https://osf.io/ftzgh/>; also DataShop 6769).** Grades 8-12, math and physical sciences. It has one `created_at` timestamp per attempt (second resolution, UTC), `template_id` and `correctness`, but no duration column, and the OSF node states no license. Not downloaded.
- **ASSISTments 2015 skill-builder data.** The page (<https://sites.google.com/site/assistmentsdata/datasets/2015-assistments-skill-builder-data>) describes only "student responses on 100 skill builders" and lists no time fields. Not downloaded. The absence of time columns was not checked in the file itself.
- **Math Garden / Prowise Learn (Oefenweb).** Their adaptive arithmetic practice logs response times, but an OSF title search for "Math Garden", "Rekentuin" and "Prowise" returned no projects, and I found no open download.
- **Anki review logs (`open-spaced-repetition/anki-revlogs-10k`, Hugging Face).** These have per-review durations but are not math. The dataset is gated (login plus accepting conditions; license "other"). Not downloaded.
- **OSF n34dr ("Does assistance inflate evidence of learning?")** holds analysis files built on ASSISTments 2012-13 (section 2), no new raw data. **OSF ma2pq** holds recommendation logs. Neither was downloaded.
- **Zenodo 20576432 ("Gameplay Log Dataset for Adaptive Mathematics Learning", CC BY 4.0, 2026).** A 19.7 KB package from "a limited trial of a first-grade elementary mathematics educational game prototype". Too small to be useful; not downloaded. Zenodo keyword searches turned up no other math practice logs with timing.

## What the time columns mean, side by side

| Dataset | "Time to first action" | "Total time on problem/step" | Idle time handled? |
|---|---|---|---|
| ASSISTments 2009-10 | `ms_first_response` (counts hint or scaffold requests as the first action) | `overlap_time` | No; outliers up to 23 h |
| ASSISTments 2012-13 | `ms_first_response`, or the first offset in `actions` | `end_time - start_time` (`overlap_time` ≈ first response here) | No; `resume` actions flag returns |
| ASSISTments 2019-20 | from `slogs` (problem_started → first response or help) | `time_on_task` | Partly: never above action-log wall time and shorter for 3.0% (long gaps removed); max 6.5 h, p99 1,623 s |
| ASSISTments experiments | `first_response_or_request_time` | `time_on_task` | Documented yes, observed no; use `session_count == 1` |
| Junyi 2019 | — | `total_sec_taken` | Capped at 1,800 s |
| EdNet-KT2 | `enter → first respond` | `enter → submit` | No cap; 0.005% over 1 h (sample) |
| KDD Cup 2010 (gated) | `First Transaction Time - Step Start Time` | `Step Duration (sec)` | Not checked |
