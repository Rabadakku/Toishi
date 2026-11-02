# Diagnosing errors from typed answers, without asking the student: source notes

Scope: what primary sources report about finding which part of a problem a student got wrong from the answer and the pattern of answers. Sources are reported, not judged; no design is recommended. Compiled 2026-11-02.

Tags: **[FT]** full text read; **[F]** page fetched with WebFetch (a helper model summarised it, so figures and quotes are second-hand); **[A]** abstract or bibliographic record only. UNVERIFIED marks anything I could not confirm. Numbers are as the source gives them.

Not repeated here (see these notes):
- `/docs/research/notes/Toishi gaps research/error_diagnosis_tagging.md`: MalruleLib, Birenbaum et al. RR-92-58 instability, Voon et al. 2017 integral errors, LLM tagging, small-data DINA/AFM.
- `/docs/research/notes/Toishi full evidence review/diagnosis_feedback_mistakes.md`: BUGGY/DEBUGGY overview, Brown & VanLehn 1980 (21 of 89 bugs), MalAlgoPy, Anderson et al. 1995, Cognitive Tutor trial, Eedi catalogue and arXiv 2510.11502 (MAP@25 0.178-0.271), MalAlgoQA, ASSISTments wrong answers (odds ratio 1.07), EMNLP 2025 localisation, Van der Kleij et al. 2015, Attali & van der Kleij 2017.

---

## A. Bug libraries and procedural error models

### A1. Brown & Burton 1978, BUGGY [A]
**Citation and link:** Brown, J. S., & Burton, R. R. (1978). Diagnostic models for procedural bugs in basic mathematical skills. *Cognitive Science*, 2(2), 155-192. https://doi.org/10.1207/s15516709cog0202_4
**What was studied:** A system that models a student's arithmetic bugs with procedural networks, plus a bug-diagnosis game and automatic diagnostic-test generation.
**Method:** Not retrievable (Wiley full text blocked; abstract via Crossref).
**Key results:** The abstract cites "the success of this system in diagnosing 1300 school students from a data base of 20.000 test items"; no accuracy figure.
**Stated limitations:** None in the abstract.

### A2. VanLehn 1987, impasse-driven learning [F]
**Citation and link:** VanLehn, K. (1987). *Towards a theory of impasse-driven learning* (Tech. Rep. PCG-1). Carnegie-Mellon University. https://apps.dtic.mil/sti/pdfs/ADA186643.pdf
**What was studied:** Repair Theory and how impasses create bugs; reviews bug counts and stability.
**Method:** Theory and review citing VanLehn (1982) and Resnick & Omanson (1987); page numbers inferred from OCR.
**Key results:** Subtraction: "76 different kinds of bugs" from "thousands of students". Fraction addition 68 bugs; signed numbers 57. Always-Borrow-Left: 6 of "375 students with bugs". Retested "two days later, they often have the same bug"; some showed it "six months apart". Stable subtraction bugs: "49% of the third graders ... vs. 27% of the fourth graders" (13% fifth); bug-free 19%, 39%, 60%. Resnick & Omanson: "60% of the students reverted to using their buggy procedures" about four weeks later.
**Stated limitations:** Repair Theory (RT1) struggles with stable, multi-impasse bugs; its extension (RT2) "is, for the most part, speculation"; no quantitative coverage score.

### A3. VanLehn 1990, Sierra as pseudo-student [F]
**Citation and link:** VanLehn, K. (1990). *Two pseudo-students: Applications of machine learning to formative evaluation* (Tech. Rep. PCG-24). Carnegie Mellon University. https://apps.dtic.mil/sti/pdfs/ADA222365.pdf
**What was studied:** Sierra (the Repair Theory program) simulating students taught subtraction from two textbooks.
**Method:** Sierra's bug profiles compared with student data; detail deferred to VanLehn (1990a), *Mind Bugs*, not obtained.
**Key results:** "1,147 young students (ages 6 to 9)"; Sierra "learned 63 distinct procedures" and "modeled between 52% and 85% of the student's bugs", depending on how profiles are compared.
**Stated limitations:** No total observed-bug count, generated-bug count or stability data.

### A4. Payne & Squibb 1990, algebra mal-rules [A]
**Citation and link:** Payne, S. J., & Squibb, H. R. (1990). Algebra mal-rules and cognitive accounts of error. *Cognitive Science*, 14(3). https://doi.org/10.1207/s15516709cog1403_4
**What was studied:** Elementary algebra errors diagnosed with Sleeman's mal-rules.
**Method:** Study in "three separate schools"; sample sizes not in the abstract.
**Key results:** Mal-rule frequency is "severely skewed, there are many infrequent mal-rules and few frequent ones"; mal-rules are "very unstable"; explanatory power differs by school; diagnosis is "more successful with more skilled students"; slips and mistakes cannot be cleanly separated.
**Stated limitations:** None in the abstract; coverage percentages UNVERIFIED.

### A5. Lee & Corter 2011, Bayesian networks for subtraction bugs [F]
**Citation and link:** Lee, J., & Corter, J. E. (2011). Diagnosis of subtraction bugs using Bayesian networks. *Applied Psychological Measurement*, 35(1), 27-47. https://doi.org/10.1177/0146621610377079
**What was studied:** Inferring four subtraction bugs from item responses.
**Method:** VanLehn's (1981) data, 520 grade 3-5 examinees, 14 items. Four networks cross binary evidence versus the commonest wrong answers per item (simulated multiple choice) with bugs only versus bugs plus subskills. "Truth" was coded from the same open responses; 80/20 split.
**Key results:** Overall correct classification on test data: binary evidence 81-88% (bugs only) and 83-90% (with subskills); specific wrong answers 94-98% and 97-99%. Overall kappa 0.53-0.61 (binary, bugs only) versus 0.89-0.95 (specific answers, bugs only).
**Stated limitations:** No external validity measure; labels and evidence share the same wrong answers; four bugs against VanLehn's "more than 200". Fetched split sizes (512 + 129) do not sum to 520.

### A6. Birenbaum, Kelly & Tatsuoka 1992/1993, rule space in algebra [F]
**Citation and link:** Birenbaum, M., Kelly, A. E., & Tatsuoka, K. K. (1992). *Diagnosing knowledge states in algebra using the rule space model* (ETS RR-92-57-ONR). https://ets.org/research/policy_research_reports/publications/report/1992/ihlc.html. Journal version: *Journal for Research in Mathematics Education*, 24(5), 442-459 (1993).
**What was studied:** Rule-space sorting of students by solution method for linear equations, and diagnosis of knowledge states.
**Method:** 231 eighth and ninth graders; 32 open-ended items.
**Key results:** The page gives no attribute count, state count or classification rate. The companion RR-92-58 (bugs unstable) is in the first note above.
**Stated limitations:** None retrieved.

---

## B. Constraint-based modelling (errors detected from the answer state)

### B1. Ohlsson 2016 [F]
**Citation and link:** Ohlsson, S. (2016). Constraint-based modeling: From cognitive theory to computer tutoring, and back again. *International Journal of Artificial Intelligence in Education*, 26, 457-473. https://link.springer.com/article/10.1007/s40593-015-0075-7
**What was studied:** How constraint-based modelling (CBM) finds errors without a bug library.
**Method:** Theoretical review.
**Key results:** A constraint is a pair <Cr, Cs> (relevance, satisfaction); a relevant constraint whose satisfaction pattern fails marks an error and names its nature, with no buggy models or error studies needed. No sample sizes, effect sizes or constraint counts; one number: positive feedback in SQL-Tutor (Mitrovic et al., 2013) cut "time to mastery" in half.
**Stated limitations:** No test of constraint-base completeness; constraint origin is an "open question"; CBM is "limited in its focus on learning from errors"; a footnote says later studies found bugs not always stable.

### B2. Mitrovic, Koedinger & Martin 2003 [F]
**Citation and link:** Mitrovic, A., Koedinger, K. R., & Martin, B. (2003). A comparative analysis of cognitive tutoring and constraint-based modeling. *User Modeling 2003* (LNCS), 313-322. https://doi.org/10.1007/3-540-44963-9_42 (text read at https://www.public.asu.edu/~kvanlehn/ITScourse2009/Readings/Mitrovic%20Koedinger%20Martin%202003.pdf)
**What was studied:** Error detection in KERMIT (CBM) versus a model-tracing rebuild, KERMIT-MT.
**Method:** Qualitative comparison; no learner study.
**Key results:** CBM judges the state, not the path; Table 2 lists "Bugs represented" as "No". CBM treats a solution as correct unless a constraint is violated; model tracing treats an unmatched step as incorrect. KERMIT has "more than 90 constraints"; KERMIT-MT has 25 production rules, written "in about 20 hours"; 23 KERMIT constraints matched them.
**Stated limitations:** CBM "typically" cannot give strategic advice and generally cannot solve problems.

### B3. Mitrovic et al. 2006, three deployed tutors [F]
**Citation and link:** Mitrovic, A., & ICTG team (2006). Large-scale deployment of three intelligent web-based database tutors. *Journal of Computing and Information Technology*, 14(4), 275-281. https://www.public.asu.edu/~kvanlehn/ITScourse2009/Readings/Mitrovic%202006.pdf
**What was studied:** SQL-Tutor, ER-Tutor and NORMIT at Canterbury and on DatabasePlace.
**Method:** Descriptive; NORMIT learning curves, Canterbury ("less than 50") versus DatabasePlace ("almost two thousand").
**Key results:** Constraints: SQL-Tutor about 700, ER-Tutor 135, NORMIT over 80. Initial error probability 0.19 versus 0.17 ("not significant"); curve fits R² = 0.8589 and 0.9316. Local studies "increase students' knowledge significantly", with no N or effect sizes.
**Stated limitations:** No limitations section; two tutors need stored ideal solutions; the paper does not say which error types constraints can detect.

### B4. Kodaganallur, Weitz & Rosenthal 2005 [A]
**Citation and link:** Kodaganallur, V., Weitz, R. R., & Rosenthal, D. (2005). A comparison of model-tracing and constraint-based intelligent tutoring paradigms. *IJAIED*, 15(2), 117-144. https://content.iospress.com/articles/international-journal-of-artificial-intelligence-in-education/jai15-2-03 (authors and year via Crossref)
**What was studied:** Two tutors for statistical hypothesis testing, one per paradigm.
**Method:** Abstract only.
**Key results:** Abstract (paraphrased by the fetch): CBM suits only solution-rich domains; model tracing gives more targeted remediation at higher development effort. No numbers.
**Stated limitations:** None retrieved.

### B5. University of Canterbury SQL-Tutor page [F]
**Citation and link:** Intelligent Computer Tutoring Group, SQL-Tutor project page (undated), read at a mirror: https://betterstartapproach.com/content/uoc-main-site/language-master/en/research/about-uc-research/research-groups-and-centres/intelligent-computer-tutoring-group/sql-tutor.html
**What was studied:** History and evaluation of SQL-Tutor.
**Method:** Project description.
**Key results:** "more than 600 constraints" (B3: about 700). April 1998 study: 20 students. "1946 people have downloaded the system in the period May 1999 - January 2001." No gains or effect sizes.
**Stated limitations:** None.

---

## C. CAS-based answer analysis in live systems

### C1. STACK documentation: potential response trees [F]
**Citation and link:** STACK documentation, "Potential response trees". https://docs.stack-assessment.org/en/Authoring/Potential_response_trees/
**What was studied:** How STACK (Sangwin) scores answers and gives feedback.
**Method:** Software documentation.
**Key results:** A PRT is an acyclic graph of nodes; each runs an answer test (true or false) whose branch can change the score, add feedback, set an answer note and pick the next node. Default penalty 0.1 per attempt. The only common-error example: a missing constant of integration gives partial credit, a penalty and "You have missed a constant of integration." No accuracy or learning data.
**Stated limitations:** Attempt number is unavailable to PRTs.

### C2. STACK documentation: answer tests [F]
**Citation and link:** STACK documentation, "Answer tests". https://docs.stack-assessment.org/en/Authoring/Answer_tests/
**What was studied:** The tests PRT nodes call.
**Method:** Software documentation.
**Key results:** The fetch counted 19 active answer tests plus 3 unnamed. Error-aware ones: Int flags a missing or unusual constant of integration; the differentiation test responds when the student seems to have integrated; the set test names missing or extra elements; SysEquiv lists wrongly included equations; FacForm gives detailed feedback; AlgEquiv gives minimal feedback. The listing names no test for chain, product or quotient rule errors.
**Stated limitations:** SubstEquiv handles 4 or fewer variables; AlgEquiv cannot establish some equivalences; Int cannot cope with some situations.

### C3. Jones 2019, STACK conference slides [FT]
**Citation and link:** Jones, I. (2019). *Finding the potential response trees in the potential response forest* [slides], STACK Conference 2019. https://webhomes.maths.ed.ac.uk/~csangwin/2019-STACK/2019-Jones.pdf
**What was studied:** Mining STACK responses for common differentiation errors worth coding into PRTs.
**Method:** Pilot online test, MAF001 Foundation module, N = 93, 30 constructed-response differentiation questions.
**Key results:** Mean score (%, SD) by rule: single function 87.23 (11.55); sum 91.40 (10.23); second derivative 67.20 (6.56); product 64.94 (9.20); quotient 46.02 (13.82); chain 67.96 (11.21). A table of 20 question-misconception pairs ranges from 90.9% (Q14, d²f/dx² = df/dx, as OCR'd) to 6.1% (Q5); product-as-f′g′ appears at 71.4, 42.9, 39.4, 26.7 and 13.7% (Q20, 18, 17, 19, 16); (x+y)² = x²+y² at 41.2 and 20%.
**Stated limitations:** None stated. The percentage denominator is UNVERIFIED; no accuracy or learning evaluation of STACK feedback.

### C4. WeBWorK AnswerHints [F]
**Citation and link:** WeBWorK wiki, "AnswerHints". https://webwork.maa.org/wiki/AnswerHints
**What was studied:** A macro that attaches messages to specific wrong answers.
**Method:** Documentation with one example.
**Key results:** Added as a post-filter on the answer checker; matches by answer value, and one message can cover a list. Example: for f(3u) with f(t) = 2t, the answer 6t triggers "Are you using the correct variable?". It does not replace an evaluator message unless `replaceMessage=>1`. Checker-function and regex matching exist but the page does not describe them.
**Stated limitations:** Hints fire only for listed answers; no accuracy or effect data.

### C5. Möbius (Maple T.A.) Maple-graded and adaptive questions [F]
**Citation and link:** Digital Education (Möbius) help: https://www.digitaled.com/support/help/admin/Content/INST-AUTHORING/QUESTION-TYPES/Author-Maple-graded-question.htm and .../Author-adaptive-question.htm
**What was studied:** How Maple code grades responses and how adaptive questions branch.
**Method:** Vendor documentation.
**Key results:** Grading code runs with `$RESPONSE` and `$ANSWER` substituted and returns a Boolean or a float from 0.0 to 1.0; the default `evalb(($ANSWER) – ($RESPONSE) = 0);` accepts equivalent answers. No dedicated detector for specific wrong forms, and the page does not say code can emit feedback. Adaptive questions show sections one at a time; whether a wrong answer carries forward is not stated.
**Stated limitations:** Partial credit must be floating point; adaptive questions allow only auto-graded components.

### C6. Fernandez et al. 2024, DiVERT [FT]
**Citation and link:** Fernandez, N., Scarlatos, A., Feng, W., Woodhead, S., & Lan, A. (2024). DiVERT: Distractor generation with variational errors represented as text for math multiple-choice questions. *EMNLP 2024*, paper 512. https://aclanthology.org/2024.emnlp-main.512
**What was studied:** Generating wrong answers with a text label for the error behind each.
**Method:** Eedi data, 1,434 questions (ages 10-13, 41 subtopics), split about 72%-16%-12% by question; a 7B open model versus GPT-4o prompting; 5-fold cross-validation; two math teachers rated 180 errors.
**Key results:** Prop@10: DiVERT 63.24±3.37, GPT-4o kNN 60.19±3.87, GPT-4o zero-shot 50.00±1.96 (GPT-4o kNN is higher on Exact@3: 21.28 versus 13.37). Error quality, DiVERT versus human: no significant difference (p = 0.36); both beat GPT-4o (p < 0.01). The paper says earlier symbolic rule-based generators (Tomás & Leal 2013; Prakash et al. 2023) "have limited generalizability beyond template-based questions".
**Stated limitations:** Distractors do not always match the generated error; needs human-labelled errors; one dataset; distractors not human-rated.

---

## D. Calculus and precalculus error catalogs, and answer-pattern diagnosis

### D1. Orton 1983, differentiation [F]
**Citation and link:** Orton, A. (1983). Students' understanding of differentiation. *Educational Studies in Mathematics*, 14(3), 235-250. https://doi.org/10.1007/BF00410540
**What was studied:** Understanding of differentiation and rate of change.
**Method:** Clinical interviews; sample size not on the page.
**Key results:** The abstract mentions "detailed data" on understanding and "common errors and misconceptions"; no counts retrieved. A structural/executive/arbitrary breakdown for this paper is UNVERIFIED.
**Stated limitations:** None retrieved.

### D2. Siyepu 2015, derivatives of trigonometric functions [F]
**Citation and link:** Siyepu, S. (2015). Analysis of errors in derivatives of trigonometric functions. *International Journal of STEM Education*. https://doi.org/10.1186/s40594-015-0029-5
**What was studied:** Written errors in differentiating trigonometric functions.
**Method:** Qualitative case study; 30 first-year Chemical Engineering extended-programme students (South Africa), three tasks; errors grouped as conceptual, procedural, interpretation, linear extrapolation.
**Key results:** Task 2 counts (of 30): 16 failed to simplify √(sin 7x + ln 5x); 12 mishandled multiplying trigonometric fractions; 9 did not change a sign; 8 did not apply trigonometric identities; 4 used the product rule instead of the chain rule for y = tan³√(cot 7x). Task 3: 8 did not know ln e = 1; 14 fused two functions (count truncated). No category totals.
**Stated limitations:** The fetch ended before the limitations (last 3,170 of 103,170 characters unread); single institution.

### D3. South African Journal of Science article on differentiation rules [F]
**Citation and link:** "Students' ability to correctly apply differentiation rules to structurally different functions", *South African Journal of Science* (authors not in the fetched text; 2018 inferred from the DOI). https://sajs.co.za/article/view/5008
**What was studied:** First-year derivative skills at the University of KwaZulu-Natal across five item categories.
**Method:** Online quiz (number of students not given), then 8 interviews.
**Key results:** No percentages. Most students handled xⁿ, e^(kx), [g(x)]ⁿ and the chain rule on e^(4x). Difficulties: seeing that several rules apply, repeated chain rule, rule order.
**Stated limitations:** None stated.

### D4. Booth et al. 2014, persistent algebra errors [A]
**Citation and link:** Booth, J. L., Barbieri, C., Eyer, F., & Paré-Blagoev, E. J. (2014). Persistent and pernicious errors in algebraic problem solving. *Journal of Problem Solving*, 7(1), Article 3. https://doi.org/10.7771/1932-6246.1161
**What was studied:** Which Algebra I errors, seen across the year, best predict standardized-test difficulty.
**Method:** Error analysis of problem-solving work; the PDF was not fetched, so N and coding are UNVERIFIED.
**Key results:** Abstract: error types become "more prominent with different content and at different times in the year"; no frequencies.
**Stated limitations:** None retrieved.

### D5. Steinle & Stacey 2004, decimal comparison test [FT]
**Citation and link:** Steinle, V., & Stacey, K. (2004). A longitudinal study of students' understanding of decimal notation: An overview and refined results. MERGA 2004 proceedings. https://merga.net.au/wp-content/uploads/DOCS/common/Uploaded%20files/Annual%20Conference%20Proceedings/2004%20Annual%20Conference%20Proceedings/RP652004%20Steinle%20Stacey.pdf
**What was studied:** Diagnosing decimal misconceptions from the pattern of answers on one test, and how long they last.
**Method:** Twelve Melbourne schools, 1995-99; over 3000 students (Grades 4-10), nearly 10 000 tests, 8.3 months apart on average. DCT2 has 30 decimal pairs; the response pattern gives coarse codes A, L, S, U and 12 fine codes.
**Key results:** In 3531 tests (1997), score pairs (5,5), (0,5) and (5,0) on the Type 1/Type 2 items were commonest; the other 33 pairs held 28%. Grade 8: 40% of S3 students retested as S3; about one in six S3 or L1 students gave the same result more than two years later; regression affected one in five. Longitudinal prevalence of L1: 62% (n = 333 primary), 12% (n = 682 secondary).
**Stated limitations:** Comparison items only; correct rule-following inflates expertise; reverse thinking was seen in interviews but rarely on the test; repeat testing alone added about 10% experts.

---

## E. Misconception data (Eedi and related competitions)

### E1. Wang et al. 2020, NeurIPS 2020 Education Challenge guide [FT]
**Citation and link:** Wang, Z., Lamb, A., Saveliev, E., et al. (2020). Instructions and guide for diagnostic questions: The NeurIPS 2020 Education Challenge. arXiv:2007.12061. https://arxiv.org/abs/2007.12061
**What was studied:** Competition design and data from Eedi's four-option diagnostic questions.
**Method:** Answer records; tasks 1-2 split 80/10/10 by record, tasks 3-4 by student.
**Key results:** "over 20 million examples of students' answers". Training sets: tasks 1-2, 27613 questions, 118971 students, 15867850 answers; tasks 3-4, 948 questions, 4918 students, 1382727 answers. Wrong options should "highlight a common misconception, but these misconceptions are not labelled or linked between questions": the release has no misconception labels.
**Stated limitations:** Crowd-sourced question quality varies.

### E2. Wang et al. 2021, NeurIPS 2020 challenge results [FT]
**Citation and link:** Wang, Z., Lamb, A., Saveliev, E., et al. (2021). Results and insights from diagnostic questions: The NeurIPS 2020 Education Challenge. arXiv:2104.04034. https://arxiv.org/abs/2104.04034
**What was studied:** Results of four Eedi prediction tasks, including which option a student picks (task 2).
**Method:** Accuracy on held-out answers.
**Key results:** "3,696 submissions from 382 teams". Task 1 (right or wrong) winner 77.29%. Task 2 (which of four options) winner 68.03%, using an order-aware cognitive diagnosis model. Baselines not captured; chance for four options is 25% by arithmetic.
**Stated limitations:** Not read.

### E3. Kaggle 2024 "Eedi - Mining Misconceptions in Mathematics": organiser and participant pages [F]
**Citation and link:** Kaggle page https://www.kaggle.com/competitions/eedi-mining-misconceptions-in-mathematics (fetch returned metadata only); Eedi blog https://eedi.com/blog/from-data-to-discovery-lessons-learned-from-hosting-ai-competitions-in-edtech; participant write-up https://github.com/DaoyuanLi2816/Kaggle-Eedi-Mining-Misconceptions-in-Mathematics-Silver-Medal
**What was studied:** Matching wrong options to a misconception list (MAP@25). Dataset counts are in the second note above, via arXiv 2510.11502.
**Method:** Organiser and participant accounts.
**Key results:** Blog: "Deadline: 5th December 2024", "Prize: $55,000", "tens of thousands of multiple-choice questions"; no scores. Write-up (one participant, unofficial): private leaderboard 0.50 ("silver medal, top 5%"); retriever held-out MAP@25 0.4238, Recall@1 0.3017, @10 0.6906, @25 0.8126.
**Stated limitations:** Eedi calls tagging "challenging for humans" and is unsure a model can do it.

### E4. Crossley et al., MIME dataset and the MAP competition [FT]
**Citation and link:** Crossley, S. A., Rittle-Johnson, B., Adler, R., et al. Automated approaches for scoring math misunderstandings in student self-explanations. AIME-Con (ACL Anthology 2026.aimecon-main.33). https://aclanthology.org/2026.aimecon-main.33.pdf
**What was studied:** Kaggle "MAP - Charting Student Math Misunderstandings" and its MIME dataset.
**Method:** 15 Eedi multiple-choice questions (grades 4-8; one correct, three wrong options); experts labelled each explanation correct, misunderstanding or neither, plus misunderstanding type; MAP@3.
**Key results:** 52,463 explanations (38,095 original, 14,368 synthetic); over 1,850 teams, 39,760 entries; $55,000 prizes; top MAP@3 "slightly above 0.948" against a "benchmark of 0.80".
**Stated limitations:** Noisy, ambiguous labels ("neither" hardest); imbalance across misunderstanding types; compute limits.

### E5. The Learning Agency case study of MAP [F]
**Citation and link:** The Learning Agency, case study of the math misconceptions competition. https://the-learning-agency.com/the-cutting-ed/article/case-study-math-misconceptions-competition
**What was studied:** Participation, scores and methods in MAP.
**Method:** Case study; no tables.
**Key results:** "over 1,850 teams", "over 39,760 entries"; top models "above 0.948"; "benchmark of 0.75" (E4 says 0.80); top 1,000 "above 0.941". Training, public and private sets "all shared the same 15 questions". Top teams used 32B and 72B LLM ensembles.
**Stated limitations:** Teams could limit predictions to misconceptions seen per question, which may not transfer; heavy compute ("up to 190 minutes" for one ensemble part).

---

## F. Cognitive diagnosis models, adaptive diagnosis, knowledge spaces

### F1. Cheng 2009, CD-CAT item selection [A]
**Citation and link:** Cheng, Y. (2009). When cognitive diagnosis meets computerized adaptive testing: CD-CAT. *Psychometrika*, 74, 619-632. https://doi.org/10.1007/s11336-009-9123-2
**What was studied:** Item selection for adaptive tests built on diagnostic models.
**Method:** Abstract only: two new heuristics against random selection and two earlier ones (Kullback-Leibler, Shannon entropy).
**Key results:** No numbers in the abstract; Kaplan et al. (F5) credit the PWKL index to this paper.
**Stated limitations:** None retrieved.

### F2. de la Torre 2011, G-DINA [A]
**Citation and link:** de la Torre, J. (2011). The generalized DINA model framework. *Psychometrika*, 76(2), 179-199. https://doi.org/10.1007/s11336-011-9207-7
**What was studied:** A general diagnostic model with relaxed assumptions.
**Method:** Abstract only: item-by-item estimation and Wald-test comparison; real and simulated data.
**Key results:** In saturated form equivalent to other general models; "several commonly used" models are special cases. No numbers.
**Stated limitations:** None retrieved.

### F3. de la Torre 2008, Q-matrix validation for DINA [A]
**Citation and link:** de la Torre, J. (2008). An empirically based method of Q-matrix validation for the DINA model. *Journal of Educational Measurement*, 45(4), 343-362. https://doi.org/10.1111/j.1745-3984.2008.00069.x
**What was studied:** Checking an expert-built Q-matrix (item-to-skill map) against data.
**Method:** Abstract only: an algorithm; real and simulated data.
**Key results:** Most fit analyses "assume that a Q matrix is correct"; the method can combine data with expert knowledge. No accuracy figures.
**Stated limitations:** None retrieved.

### F4. de la Torre & Chiu 2016, general Q-matrix validation [A]
**Citation and link:** de la Torre, J., & Chiu, C.-Y. (2016). A general method of empirical Q-matrix validation. *Psychometrika*, 81(2), 253-273. https://doi.org/10.1007/s11336-015-9467-8
**What was studied:** A discrimination index to find and replace misspecified Q-matrix entries.
**Method:** Abstract only: proofs, simulation, fraction-subtraction illustration.
**Key results:** Feasibility shown by simulation; no figures.
**Stated limitations:** None retrieved.

### F5. Kaplan, de la Torre & Barrada 2015, CD-CAT item selection [FT]
**Citation and link:** Kaplan, M., de la Torre, J., & Barrada, J. R. (2015). New item selection methods for cognitive diagnosis computerized adaptive testing. *Applied Psychological Measurement*, 39(3), 167-188. https://doi.org/10.1177/0146621614554650
**What was studied:** Two new indices (MPWKL, GDI) against PWKL, for accuracy and test length.
**Method:** Simulation under G-DINA, 5 attributes, 6 profiles x 1,000 examinees; four item-quality levels; fixed lengths of 10, 20, 40 items or a posterior stopping threshold.
**Key results:** At 40 items, correct attribute-vector classification was "almost 1.00" for all indices. At 10 items (DINA, high-discrimination low-variance items): 0.89 (MPWKL, GDI) versus 0.75 (PWKL). Higher discrimination gave higher accuracy.
**Stated limitations:** Pool held every possible q-vector; item parameters known; fixed 5 attributes; one generating model per data set; exposure control not studied.

### F6. Madison & Bradshaw 2015, Q-matrix design [A]
**Citation and link:** Madison, M. J., & Bradshaw, L. P. (2015). The effects of Q-matrix design on classification accuracy in the log-linear cognitive diagnosis model. *Educational and Psychological Measurement*, 75, 491-511. https://doi.org/10.1177/0013164414539162
**What was studied:** How item-to-skill design affects classification accuracy.
**Method:** Simulation; abstract only.
**Key results:** "classification accuracy, reliability, and convergence rates improve when the Q-matrix contains isolated information from each measured attribute".
**Stated limitations:** None retrieved.

### F7. Cosyn et al. 2013, ALEKS assessment [FT]
**Citation and link:** Cosyn, E., Doble, C., Falmagne, J.-C., et al. (2013). Assessing mathematical knowledge in a learning space. In *Knowledge Spaces: Applications in Education* (pp. 27-50). Springer. https://doi.org/10.1007/978-3-642-35329-1_2
**What was studied:** Validity and reliability of ALEKS assessments for grades 3-6 mathematics.
**Method:** A random "extra problem", ignored by the adaptive update, is predicted from the inferred knowledge state; data June 2009 to December 2012.
**Key results:** 300 items, 125,786 assessments: median point-biserial correlation rises from .19 before any question to an asymptote of .46 (quartiles .35, .55). Tetrachoric median .68 (grouped .80); phi median .43 (grouped .58). Median careless-error rate 19%.
**Stated limitations:** Reliability is confounded with validity; correlations under .2 flag problem items or misplacement.

### F8. Cosyn et al. 2021, ALEKS and its data [FT]
**Citation and link:** Cosyn, E., Uzun, H., Doble, C., & Matayoshi, J. (2021). A practical perspective on knowledge space theory: ALEKS and its data. *Journal of Mathematical Psychology*, 101, 102512. https://doi.org/10.1016/j.jmp.2021.102512 (read as a preprint)
**What was studied:** How well ALEKS initial assessments predict an unseen extra problem.
**Method:** AUROC, point-biserial and accuracy against extra-problem responses ("I don't know" counted incorrect). Assessments are capped at 30 questions (up to 29 adaptive); College Placement has about 10^23 states.
**Key results:** College Placement (N = 2,775,432): AUROC 0.889, point-biserial 0.671, accuracy 0.814. Sixth-Grade Math (N = 162,900): 0.875, 0.634, 0.801. College Algebra (N = 174,073): 0.863, 0.602, 0.808. In 2,688,472 full-length College Placement assessments, measures barely changed after question 10.
**Stated limitations:** Probabilities estimate knowing an item, not answering it correctly; careless errors blur the proxy; accuracy depends on the correct rate.

---

## G. Effects of diagnosis-based feedback

### G1. Sleeman et al. 1989, remediation in algebra [A]
**Citation and link:** Sleeman, D., Kelly, A. E., Martinak, R., Ward, R. D., & Moore, J. L. (1989). Studies of diagnosis and remediation with high school algebra students. *Cognitive Science*, 13(4), 551-568. https://doi.org/10.1207/s15516709cog1304_3
**What was studied:** Error-specific (model-based) remediation versus reteaching.
**Method:** Three studies with human tutors; sample sizes not in the abstract (UNVERIFIED).
**Key results:** Abstract: "MBR and reteaching are both more effective than no tutoring; however, MBR is not clearly more effective than reteaching." It cites Swan (1983), who found a conflict approach beat reteaching, and Bunderson & Olsen (1983), who found no difference.
**Stated limitations:** Human tutors only; results discussed in terms of error stability.

### G2. Wisniewski, Zierer & Hattie 2020, feedback meta-analysis [FT]
**Citation and link:** Wisniewski, B., Zierer, K., & Hattie, J. (2020). The power of feedback revisited: A meta-analysis of educational feedback research. *Frontiers in Psychology*, 10, 3087. https://doi.org/10.3389/fpsyg.2019.03087
**What was studied:** Feedback effects on learning, by feedback type.
**Method:** Random-effects meta-analysis, 435 studies, k = 994 effects, N > 61,000.
**Key results:** All effects d = 0.55 (CI 0.48-0.62; 17% negative); without 35 extreme values d = 0.48. Reinforcement or punishment d = 0.24 (k = 39); corrective feedback ("right or wrong" plus the correct answer) d = 0.46 (k = 238); high-information feedback d = 0.99 (k = 42; CI 0.82-1.15). No subgroup isolates error-specific feedback.
**Stated limitations:** Heterogeneity I² = 86.47%; many small high-effect studies.

### G3. Shute 2008, formative feedback review [FT]
**Citation and link:** Shute, V. J. (2008). Focus on formative feedback. *Review of Educational Research*, 78(1), 153-189. https://doi.org/10.3102/0034654307313795
**What was studied:** Feedback types, timing and learner interactions.
**Method:** Narrative review, not a meta-analysis; Table 1 ranks feedback types from none to "informative tutoring".
**Key results:** Cites Kulhavy et al. (1985): complexity was inversely related to error correction and efficiency; a review of 15 studies found complexity unrelated to effects; and G1. Says error analyses may match feedback to typical errors but "may not, in fact, be necessary".
**Stated limitations:** Guidelines omit "equivocal findings"; references are representative, not exhaustive.

### G4. Narciss et al. 2014, feedback strategies in fractions [A]
**Citation and link:** Narciss, S., Sosnovsky, S., Schnaubert, L., et al. (2014). Exploring feedback and student characteristics relevant for personalizing feedback strategies. *Computers & Education*, 71, 56-76. https://doi.org/10.1016/j.compedu.2013.09.011
**What was studied:** Procedural versus conceptual and concise versus elaborated feedback.
**Method:** 124 sixth and seventh graders; fraction error-correction tasks in ActiveMath; portal abstract only.
**Key results:** Boys gained significantly less than girls under all conditions; skipping was more frequent after conceptual feedback. No error-specific versus generic condition; no effect sizes.
**Stated limitations:** None retrieved.

### G5. EEF evaluation of Eedi diagnostic questions [F]
**Citation and link:** Education Endowment Foundation, Eedi project page. https://educationendowmentfoundation.org.uk/projects-and-evaluation/projects/diagnostic-questions
**What was studied:** Eedi homework quizzes (two 10-question diagnostic assignments per topic, three weeks apart), Key Stage 4.
**Method:** 175 schools; allocation method and pupil numbers not stated.
**Key results:** No attainment result (COVID closures; 2020 GCSEs cancelled). Teacher workload down 28 minutes per week. Year 10 averaged 25 quizzes (about 80 expected), Year 11 four (about 52).
**Stated limitations:** Primary outcome lost; low dosage; no further trial planned.

---

## Could not find or verify

- Burton (1982) DEBUGGY and the Brown & Burton (1978) full text: no diagnosis accuracy or percent diagnosed beyond the abstract.
- VanLehn's *Mind Bugs* (1990a): Sierra's 52%-85% is a one-line summary in a 1990 report.
- Payne & Squibb (1990) and Sleeman et al. (1989) full text: coverage, sample sizes, remediation effect sizes.
- Limits: no error-frequency study found. Orton (1983) counts were not retrieved. Clark et al. (1997, *Journal of Mathematical Behavior* 16, 345-364, https://doi.org/10.1016/S0732-3123(97)90012-2) failed to load; a UNISA thesis cites it only in passing. Siyepu (2013, https://doi.org/10.1016/j.jmathb.2013.05.001) was not read.
- STACK: no published accuracy, usage or learning-effect data. The search budget ended after the documentation, Jones's slides and an Edinburgh thesis abstract (Alarfaj 2024) that reports none. The Numbas adaptive-marking page failed to load.
- Rule-based wrong-answer generators (Tomás & Leal 2013; Prakash et al. 2023) are known only from DiVERT; McNichols et al. (arXiv 2404.02124) was downloaded, not read. No system found that applies calculus error rules to generate expected wrong answers.
- Kaggle 2024: winning score, team count and label distribution not found.
- Cheng (2009) numbers; Chen, Liu, Xu & Ying (2015, JASA; search titles only); the abstract-level diagnostic-model papers.
- No randomized test of error-specific versus generic feedback in calculus or precalculus; the nearest is Sleeman et al. (algebra, human tutors).
- Not obtained: Birenbaum et al. 1993 abstract; Booth et al. 2014 PDF; Kodaganallur et al.'s critique and reply (IJAIED 16(3)); Mitrovic & Ohlsson (1999).
- [F] items and the quotes inside them were summarised by a helper model and not checked against PDFs.
