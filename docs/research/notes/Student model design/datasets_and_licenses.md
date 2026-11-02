# Public student-practice datasets: access, fields, size, licenses

Prepared 2026-11-02 for Toishi. Facts only: nothing here ranks or recommends a dataset. Sources: dataset pages, READMEs, Hugging Face (HF), Dataverse and Kaggle metadata, DataShop public pages, papers. No large file was downloaded. Quoted text is verbatim from the URL named. UNVERIFIED marks anything I could not confirm on a primary page. Kaggle pages need a login, and my web-search quota ran out before the last gaps closed. Counts differ between sources because of preprocessing; variants are shown with their source.

Legend: T = timestamps (abs = absolute dates), D = response or step duration, H = hints, K = knowledge-component (KC) tags, X = item text.

## 1. Summary table

| Dataset | Owner; access | Size | Fields | License / terms |
|---|---|---|---|---|
| KDD Cup 2010 (5 sets) | PSLC DataShop (CMU); free login | 8.9M / 20.0M train steps (Algebra / Bridge 2008-09) | T abs, D, H, K multi, no X | No licence text; DataShop Terms |
| ASSISTments 2009-10 | WPI; Drive link | 346,860 rows, 4,217 students | no T; D; H; K; no X | Data ToU: no sharing |
| ASSISTments 2012-13 (+affect) | WPI; Drive link | 2.5M to 6.1M rows | T abs; D; H; K; affect | Data ToU |
| ASSISTments 2015 | WPI; Drive link | 708,631 rows, 19,917 students | skill, correct only | Data ToU |
| ASSISTments 2017 | WPI; request form | 942,816 rows | T; D; K | "The access to the dataset is free"; ToU |
| WPI-ASSISTments 2004-07 | DataShop project 19; public | 0.58M to 1.45M transactions per year | DataShop format | DataShop Terms |
| FoundationalASSIST (2026) | WPI; HF manual gate | 1,722,169 rows, 5,000 students | T; H; K; X; no D | cc-by-nc-4.0 plus gate checkboxes |
| OLI Engineering Statics | CMU OLI; DataShop project 48, private | Fall 2011 (DS 507): 361,092 transactions | T abs; D; H; 3 KC models; no X | DataShop Terms |
| DataShop physics, chemistry, calculus, circuits | various; Andes physics public, most others private | 18k to 346k transactions per set | DataShop format | DataShop Terms |
| EdNet | Riiid; direct links | 131.4M rows, 784,309 students | T (shifted); D; K multi; no X | CC BY-NC 4.0 |
| Junyi 2020 | Junyi Foundation; Kaggle | 16.2M attempts, 72,630 students | T (rounded); D; H; K; no X | CC BY-NC-SA 4.0 |
| Junyi 2015 | DataShop project 244; public | 25.9M interactions (XES3G5M Table 1) | T; K | DataShop Terms |
| Eedi NeurIPS 2020 | Eedi; project page | 15.9M answers, 118,971 students | T to the minute; K tree; no D | CC BY-NC-ND 4.0 |
| Eedi Kaggle 2024 | Eedi; Kaggle | UNVERIFIED | UNVERIFIED | UNVERIFIED |
| XES3G5M | TAL; Google Drive | 5.55M rows, 18,066 students | T ms; K multi; X; no D | MIT |
| Duolingo HLR | Duolingo; Dataverse, open | about 12.9M traces | T; session aggregates | CC BY-NC 4.0 |
| SLAM 2018 | Duolingo; Dataverse, open | over 2M tokens, 6,000 students | days; time (s) | CC BY-NC 4.0 |
| anki-revlogs-10k (+ -raw, -id, FSRS-Anki-20k) | open-spaced-repetition; HF auto gate | 727.7M reviews, 10,000 collections | day_offset; rating; duration | custom "other" licence |
| srs-benchmark outputs | same org; GitHub | per-user fitted parameters | n/a | no licence file found |
| MaiMemo | MaiMemo; Dataverse | 220M logs | delta_t; recall | CC BY-NC 4.0 |
| HarvardX person-course | Harvard/MIT; Dataverse | aggregate | not item level | Dataverse Community Norms |

## 2. Terms that apply to several sources

**PSLC DataShop** (https://pslcdatashop.web.cmu.edu/Terms, effective 2012-01-16; site v11.4.0):
- "Data is for research purposes, not commercial purposes."
- "You will not make any attempts to de-anonymize the data."
- "DataShop makes no guarantees about the data in terms of quality or future availability."
- "You will not distribute data obtained from DataShop. If you are collaborating with others who require access to the data, they must establish accounts with DataShop and agree to these terms."
- Also an indemnification clause and a ban on creating datasets with information that identifies students. None of the clauses I read addresses publishing derived statistics or fitted parameters either way.
- Access (https://pslcdatashop.web.cmu.edu/help?page=access): "After creating a DataShop account, you will have access to all public datasets." For private data, "The request for access will be sent to the project's principal investigator and data provider (if one exists)."
- Projects 244, 48, 27, 167, 1040 and 544 each state: "There are no additional terms associated with this project. ... The DataShop terms of use apply."
- Citation: Koedinger, Baker, Cunningham, Skogsholm, Leber, Stamper (2010), Handbook of Educational Data Mining. The IRB/shareability help page (help?page=irb) was not read.

**ASSISTments**, old terms page (https://sites.google.com/site/assistmentsdata/termsofuseforusingdata):
- "I will not use the data to discover personally identifiable information about the individual students in the study."
- "I agree to not give this data to anyone else. I will only use this data for the purpose I provide."
- "I will acknowledge the use of the ASSISTments TestBed in any publications;"
- "My data and algorithms will be made public in my papers I publish."
- "If you want to not share your source code, then you can not use this data."

Newer page (https://www.assistmentstestbed.org/the-data/termsofusefordata): four terms: no re-identification; delete and report identifying information to nth@wpi.edu; no sharing with third parties; "You agree not to commercialize the data or use it maliciously." It notes FERPA coverage.

## 3. KDD Cup 2010 (PSLC DataShop / Carnegie Learning)

- Official site: https://pslcdatashop.web.cmu.edu/KDDCup/ . Ran 1 Apr to 8 Jun 2010; co-chairs John Stamper and Alexandru Niculescu-Mizil. Downloads page: "You must be logged in to download data" (free DataShop account); challenge tarball about 707 MB. No GitHub, HF or PyPI mirror verified.
- Five sets, not three. Development (each with a `_master.txt` holding true Correct First Attempt): Algebra I 2005-2006, Algebra I 2006-2007, Bridge to Algebra 2006-2007. Challenge: Algebra I 2008-2009, Bridge to Algebra 2008-2009.
- Split: one random problem per student per unit is held out as test and later rows are discarded, so training files are not complete logs.
- Size: Algebra 2008-09 has 8,918,055 train steps, 508,913 test, 3,310 students; Bridge 2008-09 has 20,012,499 train, 756,387 test (https://pslcdatashop.web.cmu.edu/KDDCup/workshop/papers/kdd2010ntu.pdf). pyKT: Algebra2005 809,694 interactions, 574 students, 112 KCs; Bridge2006 3,679,199 interactions, 1,146 students, 493 KCs. Wilson et al. 2016 (arXiv 1604.02336): Bridge 2006-07 has 1,146 students, 19,355 problems, 494 KCs, 88.82% correct.
- Fields: student, problem hierarchy, problem, step and view identifiers; Step Start Time, First Transaction Time, Correct Transaction Time, Step End Time (absolute, e.g. "2006-10-26 09:51:58.0"; hidden in test rows); Step Duration (sec) plus correct and error variants; Correct First Attempt, Incorrects, Hints, Corrects; KC(model) and Opportunity(model), with several KCs per step separated by "~~". Challenge sets carry extra KC models.
- Limits: no problem text, only the internal problem name and unit ("does not contain information on the content of the questions being answered aside from the skill associated with it and the internal name of the problem and its unit"). FAQ lists known noise: dev-set errors, cut-off KC names in Algebra I 2006-07, "(null~null)" KCs. Grade level is not stated on the KDD pages (UNVERIFIED); subject is Cognitive Tutor algebra.
- Terms: no licence text on the KDD pages. Stamper & Pardos (2016, https://learning-analytics.info/index.php/JLA/article/view/4463): "The dataset is freely re-distributable so long as the original data usage agreement is retained." That agreement is not defined on any page I found. Requested citation: "Stamper, J., Niculescu-Mizil, A., Ritter, S., Gordon, G.J., & Koedinger, K.R. (2010). [Data set name]. [Challenge/Development] data set from KDD Cup 2010 Educational Data Mining Challenge. Find it at http://pslcdatashop.web.cmu.edu/KDDCup/downloads.jsp". DataShop copies: DataShop Terms (section 2).
- DataShop copies: public "Data Files for KDD Cup 2010" (id 4524, project 692, files only). Private: Algebra I 2005-2006 (id 123, 2,146,238 transactions), Algebra I 2006-2007 (id 214, 5,447,808, status "bad, see note"), Bridge to Algebra 2006-2007 (id 318, 6,120,606); project 56 "KDD Cup 2010 Challenge Datasets (partial)" (PI John Stamper): Algebra I 2008-2009 (id 344, 310 students, 1,640,597) and Bridge 2008-2009 (id 345, 208 students, 786,279).
- Tools: EduData KDD Cup 2010 report; pyKT (algebra2005, bridge2006); LKT reads DataShop format.
- Papers: top teams Yu et al. (NTU), Toscher & Jahrer, Pardos & Heffernan (workshop papers on the KDD site); Wilson et al. 2016; DAS3H (Choffin et al., arXiv 1905.06873) used algebra05 and bridge06 with time windows {1/24, 1, 7, 30, +inf} days.

## 4. ASSISTments (WPI, Neil Heffernan)

- Old data site: https://sites.google.com/site/assistmentsdata/ ("This page is old. We have moved the maintenance of data sets to" https://www.etrialstestbed.org/resources/featured-studies/dataset-papers). Competition site: https://sites.google.com/view/assistmentsdatamining/dataset . No licence statement on these pages. Policy line: "All papers after 2012 should have a publicly available link to get the data, but if that is not true, email all the authors, and myself, asking for the data." Citations go to etrials@assistments.org. Terms: section 2.
- **2009-10 skill builder** (https://sites.google.com/site/assistmentsdata/home/2009-2010-assistment-data/skill-builder-data-2009-2010). Google Drive downloads, original and corrected; the page warns "Duplicated data records have been detected in the data sets" at the original links. Fields include order_id (not chronological), user_id, problem_id, correct, attempt_count, ms_first_response, overlap_time, hint_count, bottom_hint, first_action, skill_id, skill_name, opportunity. No absolute timestamps (XES3G5M Table 1: "Timestamp avail. No"); multi-skill items are duplicated rows; no problem text. Size: pyKT 346,860 rows, 4,217 students, 26,688 questions; AKT Table 1: 325,637 interactions, 4,151 students, 110 skills; Wilson et al.: 4,097 students, 112 skills. Middle-school math. Cite Feng, Heffernan & Koedinger 2009 (UMUAI 19:243-266).
- **2012-13 with affect** (https://sites.google.com/site/assistmentsdata/datasets/2012-13-school-data-with-affect). Drive download; "When you download this file and unzip it will take 3 gig of ram!!!". Third-party Kaggle mirror (3,009,494,391 bytes, license "Unknown"). Fields include user_id, problem_id, skill_id, start_time and end_time (absolute), correct (1 = first attempt; decimals = partial credit), hint_count, bottom_hint, attempt_count, ms_first_response, overlap_time, first_action, answer_text, and Average_confidence for FRUSTRATED, CONFUSED, CONCENTRATING, BORED. Problem text not public (contact etrials@assistments.org). Size: pyKT 2,541,201 interactions, 27,066 students, 45,716 questions; XES3G5M Table 1: 46,674 students, 6,123,270 interactions, 265 KCs; DAS3H after preprocessing: 24,750 users, 2,692,889 interactions. Cite Wang, Heffernan & Heffernan 2015 if affect columns are used, otherwise Feng et al. 2009.
- **2015** (https://sites.google.com/site/assistmentsdata/datasets/2015-assistments-skill-builder-data). Drive download. "This is the ASSISTment data gathered in the year of 2015"; 100 skill builders. Only skill id and correctness, no timestamps. pyKT: 708,631 rows, 19,917 students, 100 KCs; AKT: 683,801 interactions, 19,840 students. Contact "szhao at wpi dot edu"; no citation statement.
- **2017 competition.** Request through a Google Form; link emailed. Page: "The access to the dataset is free"; "you are allowed to publish paper on this dataset as long as you agree to our Terms of Use". Columns are described in an external spreadsheet I did not read. Size: 942,816 interactions (pyKT, AKT); students 686 (pyKT) vs 1,709 (AKT, XES3G5M); 3,162 questions, 102 KCs (AKT, XES3G5M). Timestamps yes; pyKT fields: question, skill, correctness, duration, submit time. Paper: Patikorn, Selent, Heffernan et al., "ASSISTments Dataset for a Data Mining Competition to Improve Personalized Learning".
- **Other releases** on the etrials page include 22Experiments, ASSISTmentsSkillbuildersFrom2016-17, TeachASSIST (2020), 89-Experiments 2021/2022, ASSIST-L@S-22 and a 33-experiment dataset (2023); sizes and fields not examined (UNVERIFIED). "Problem Bodies 2012 v2": "WPI considers this data proprietary and only gives it away with a signed license". WPI-ASSISTments 2004-05 (id 92, 912 students, 580,785 transactions), 2005-06 (id 120, 3,136 students, 685,615) and 2006-07 (id 339, 5,046 students, 1,451,003) are public on DataShop project 19.
- **FoundationalASSIST (2026).** arXiv 2602.00070 (Worden, C. Heffernan, N. Heffernan, Sonkar; AIED 2026). HF `ASSISTments/FoundationalASSIST`: gated "manual", license cc-by-nc-4.0, created 2026-02-18. 1,722,169 interactions, 5,000 students, 3,395 problems, Jan 2019 to Jul 2024, grades 6-8 Illustrative Math aligned to Common Core. Skills: the paper says 462 KCs, the card says 224. Fields: user_xid, problem_id, hint_count, answer_text (first answer only), saw_answer, discrete_score, end_time; no response-time field. Problems carry full HTML/MathML text. Card note: about 700,000 rows were missing from Interactions.csv through a Git LFS issue. Gate text: "You agree to our Responsible Use Guidelines (https://www.etrialstestbed.org/mathnet57963-guidelines)"; checkboxes include "I agree to use this dataset for non-commercial use ONLY" and "I agree that this data will be stored on secured institutional systems, will not be shared with unauthorized parties and will deleted or returned to ASSISTments when my research is complete". The card says it cannot share with researchers from "Countries of concern" ("we are not legally permitted to do so"). The guidelines page body concerns "MathNet57789" student-answer images ("You cannot commercialize these images."), so its applicability here is UNVERIFIED.
- Tools: EduData reports for 2009-10, 2015, 2017; pyKT supports 2009, 2012, 2015, 2017; LKT reads DataShop-format data. Other mirrors: third-party Kaggle copies (license "Unknown"); an IEEE DataPort copy (subscription; uploaded 2026 by Khoa Le).
- Papers: Piech et al. 2015 (DKT, ASSIST09); AKT (Ghosh et al., KDD 2020, arXiv 2007.12324) used "four benchmark datasets: ASSISTments2009, ASSISTments2015, ASSISTments2017, and Statics2011" with an exponential-decay attention over time; DAS3H used assist12.

## 5. OLI Engineering Statics (Fall 2011) on DataShop

- DataShop project 48, "OLI Engineering Statics" (https://pslcdatashop.web.cmu.edu/Project?id=48). Data Provider Norman Bier, PI blank. It appears in DataShop's private list, so access is by Request Access to the PI/data provider. Project terms: DataShop Terms only. College engineering statics (CMU 24-261 and OLI courses).
- Datasets (id; transactions; KC-model count as shown in the project table, column meaning inferred from position and from EduData's three KC columns for DS 507):
  - Fall 2007 CMU 24-261 (281; 129,521; 3); Fall 2008 (284; 145,767; 3); Fall 2010 (405; 485,596; 8); Spring 2011 (481; 147,001; 4).
  - **Fall 2011 (507; 361,092; 3)**, Aug 22 to Dec 8, 2011, status complete. Subsets: CMU 34 students (512; 64,671; 4), 74 students (513; 128,927; 14), 148 students (514; 215,412; 8). Fall 2011, 114 students (590; 169,284; 7). Fall 2012 (655; 435,155; 2). Ids 1931 and 1981 are fixed versions; 1981 adds step-KC models.
- pyKT "Statics2011": 194,947 interactions, 333 students, 1,224 questions (problem name plus step name), absolute timestamps; its pointer is https://pslcdatashop.web.cmu.edu/DatasetInfo?datasetId=507 . AKT Table 1: 333 students, 1,223 skills, 189,297 interactions.
- Fields (EduData OLI_Fall2011 report of the DataShop step export): student, problem hierarchy, problem, step and view identifiers; Step Start, First Transaction, Correct Transaction, End Time (e.g. "2011/9/21 17:35"); Step Duration (sec) with correct and error variants; First Attempt, Incorrects, Hints, Corrects, Condition; KC (F2011), KC (Single-KC), KC (Unique-step), each with Opportunity and Predicted Error Rate. No item text.
- Student and KC totals for DS 507 are UNVERIFIED (the guest DatasetInfo view has no overview statistics). No public mirror verified; the DataShop "will not distribute" term applies.

## 6. Other DataShop datasets (physics, chemistry, calculus, circuits, vocabulary)

Public (any logged-in account), all DataShop step/transaction format:
- Andes2 physics, project 27 (PI Kurt VanLehn). USNA Physics, Spring 2005 to Spring 2010: 11 datasets (ids 126, 157, 220, 233-236, 263, 302, 409, 410), 73,486 to 345,536 transactions each (largest: Fall 2006, id 126); 3 to 4 KC models for most, 9 for Fall 2008 (id 263), 8 for Spring 2009 (id 302). St. Anselm Intro Physics 2009-10 (408; 74,328; 6). Watchung Hills High School Honors/AP Physics (ids 237, 238, 303, 304, 411, 412; 22,714 to 139,282; 3). Some listed date ranges span years (USNA Physics Fall 2006: Jan 6, 2003 to Jan 8, 2007); not investigated.
- Andes3 physics, project 167 (PI Kurt VanLehn; 5 KC models each): St. Anselm Summer 2011 (541; 85,734), ASU lab Spring 2011 (575; 28,209), St. Anselm Summer 2012 (576; 149,958), OSU Honors Physics: Mechanics Fall 2011 (577; 323,912), UWPlatt Spring 2012 (578; 49,472).
- Self Explanation Electric Fields, USNA Spring 2006 (id 104; 19,749).
- IUSE Chem Tutor (Public), project 722 (PI Martina Rau): Chem 375 (id 4666, Sep to Dec 2018, 90,583 transactions). Stoichiometry simulated-student sets also listed.
- WeBWorK Engagement, project 544 (PI K. Andrew Parker): "S18 - College Algebra & Trig" (id 3090; on-going; files; 0 transactions).
- Siyavula Data, project 1094 (PI Michael Asher): "Data for 'Will They Try Again'" (id 6769; Math; files only).
- Vocabulary and cloze practice (titles only; spacing content UNVERIFIED): Pavlik Chinese and Spanish vocabulary projects (e.g. Chinese Vocabulary Spring 2006, id 107, 71,928 transactions); Memphis A&P / Statistics Cloze Practice (project 858).
- Human Learning Rate, project 709 (PI Paulo Carvalho): id 4629 "Model estimates for multiple (27) datasets" (files only), tied to Koedinger et al. 2023 PNAS, "An astonishing regularity in student learning rate" (iAFM on 27 datasets).

Private (Request Access; permission from PI/data provider):
- WeBWorK, project 1040 (PI James Wei): Rogawski Calculus (id 6574; "-old" 6564), 56,426 transactions, Sep 14, 2014 to Dec 7, 2015; 6 KC models (old: 5).
- Learnvia, project 1097 (PI Eric Keylor): Calculus 1 Jan 2026 BKT Standardized 100K (id 6864; 100,537); Spring Pilot 2026 Calculus 1 (ids 6938, 6939; 97,339 each).
- Big Bet Self-Explanation, project 1031 (PI Ken Koedinger): Big Bet Calculus Experiment, 2025 Spring (id 6449; files only; 96,906). Project 1099 (PI I-Sheng Chen): Self-Explanation Study Calculus N=92 (id 6897; 19,708).
- AutoTutor, project 453: "Calculus" (id 2914; 18,004).
- Engineering Statics Refresher, Cal State Fullerton (project 638, Norman Bier).
- Chemistry: General Chemistry 1/2 (David Yaron; projects 482, 534), OLI General Chemistry 1 (679), Chemistry Virtual Lab (61, 43), IUSE Chem Tutor non-public (317).
- Circuits and other: PhET Circuit lab study (project 302, PI Sarah Perez), Thermodynamics (project 7, files only), Robot Kinematics and Dynamics (id 1995).

Learning-rate figures reported by papers on DataShop data (not re-derived here): student-slope IQR about 0.012 to 0.047 logits on datasets 99, 104, 253, 392 and 1007, and MATHia fixed slopes of 0.16 to 0.48 logits per opportunity (EDM 2024 short paper 40, https://educationaldatamining.org/EDM2024/proceedings/2024.EDM-short-papers.40/). Lee, Lichand, Barnard, Klotz, Thille, Kim, Domingue (arXiv 2605.01690, May 2026) report learning-rate variation inflated by a median of 118% under one specification.

## 7. EdNet (Riiid)

- Owner Riiid / Santa (Korea, TOEIC preparation); repo https://github.com/riiid/ednet ; paper arXiv 1912.03072 (Choi et al., AIED 2020); contact research@riiid.co. Downloads are bit.ly links (ednet_kt1, ednet-kt2, ednet-kt3, ednet-kt4, ednet-content); the repo holds pointers, not data. English multiple choice, not math.
- Size: 131,441,538 interactions, 784,309 students, 13,169 problems, 1,021 lectures, 293 skill tags. pyKT lists 131,317,236 interactions.
- KT1 (784,309 files; 1.2 GB compressed, 5.6 GB uncompressed): timestamp (Unix ms), solving_id, question_id, user_answer, elapsed_time (ms). KT2 to KT4 (about 297,000 files each; KT4 is 1.2 GB) add actions such as erase_choice, play_video, pay. Contents: question_id, bundle_id, correct_answer, part 1-7, tags (multiple, ";"-separated), deployed_at; lectures add lecture_id, video_length. Timestamps "are modified (shifted by fixed values) due to security issues". No question text.
- Licence (README): "The dataset is publicly released under Creative Commons Attribution-NonCommercial 4.0 International license for research purposes." No LICENSE file in the repo.
- Kaggle "Riiid Answer Correctness Prediction" uses the same source under separate competition rules; terms and counts UNVERIFIED.
- Tools: pyKT, EduData (EdNet_KT1 report).

## 8. Junyi Academy

- **2020 release** (Junyi Academy Foundation, Taiwan): https://www.kaggle.com/datasets/junyiacademy/learning-activity-public-dataset-by-junyi-academy . Kaggle licence CC BY-NC-SA 4.0. Version 9, updated 2020-05-13; 1.504 GB zip. Policy page: https://www.junyiacademy.org/about/policy . Terms: "Everyone using this dataset should follow the Creative Commons BY-NC-SA 4.0 license."; "Junyi Academy under reasonable conditions could ask the user of the dataset to share their feedback and research results with the community"; "Anyone using this dataset should not distort the information." Junyi may stop providing the data; Taiwan law applies.
- Log_Problem.csv: 16,217,311 attempts by 72,630 students, 2018/08 to 2019/07. Fields: timestamp_TW (UTC+8, rounded), uuid, ucid, upid, problem_number, exercise_problem_repeat_session, is_correct, total_sec_taken, total_attempt_cnt, used_hint_cnt, is_hint_used, is_downgrade, is_upgrade, level. Info_Content.csv: ucid, content_pretty_name, content_kind, difficulty, subject (math only), learning_stage, level1-4 hierarchy. Info_UserData.csv: 72,758 users, user_grade 1-12. Math, elementary to senior high. Hashed IDs, no item text; KC is the exercise (ucid) plus hierarchy.
- **2015 release**: DataShop project 244 (public; PI Haw-Shiuan Chang). id 1198 "Junyi Academy Math Practicing Log (to Jan. 2015)" (Oct 1, 2012 to Jan 12, 2015; files only); id 1275 "Partial Samples" (359,804 transactions, 5 KC models). XES3G5M Table 1: 247,606 students, 722 exercises, 41 KCs, 25,925,922 interactions, timestamps yes; arXiv 2407.03118 says Junyi timestamps "are not as precise as for the other datasets".
- Paper: Chang, Hsu & Chen (EDM 2015), "Modeling exercise relationships in e-learning: A unified approach".

## 9. Eedi

- **NeurIPS 2020 Education Challenge** (https://eedi.com/projects/neurips-education-challenge ; paper arXiv 2007.12061, Wang et al.). Licence line: "This data is licensed under a Creative Commons Attribution-NonCommercial-NoDerivatives 4.0 International License:". The paper says the data was "shared solely for the purpose of this competition and must not be used for any other purpose", which sits uneasily with that licence line. Distributed via CodaLab; the "Download Eedi Dataset" URL was not exposed to me.
- Size: tasks 1-2: 27,613 questions, 118,971 students, 15,867,850 answers; tasks 3-4: 948 questions, 4,918 students, 1,382,727 answers. Sept 2018 to May 2020; ages about 7-18; math diagnostic multiple choice, 4 options.
- Fields: answers (DateAnswered to the nearest minute, Confidence 0-100, GroupId, QuizId, SchemeOfWorkId); students (UserId, Gender, DateOfBirth rounded to the 1st, PremiumPupil); questions (SubjectId, a tree in subject_metadata.csv, several per question). Question images for tasks 3-4 only. No question text, no response time. pyKT "NIPS34": 1,382,727 interactions, 948 questions, 57 KCs.
- **Kaggle 2024 "Eedi - Mining Misconceptions in Mathematics"**: licence and terms UNVERIFIED (Kaggle pages and API need login). Task: "Predict affinity between misconceptions and incorrect answers (distractors) in multiple-choice questions"; student responses not part of it (UNVERIFIED).
- **Eedi Misconceptions Graph v1.0 (2026)**: found only as a third-party HF mirror (`wangwangduishuidajiao/Eedi-Misconceptions-Graph`), CC BY 4.0, "Copyright (c) 2026 Eedi Ltd"; 19,294 edges, 8,117 misconceptions, 2,258 constructs; no questions or student data. Official Eedi URL UNVERIFIED.

## 10. XES3G5M (TAL Education Group)

- Repo https://github.com/ai4ed/XES3G5M ; paper NeurIPS 2023 Datasets & Benchmarks (https://papers.neurips.cc/paper_files/paper/2023/file/67fc628f17c2ad53621fb961c6bafcaf-Paper-Datasets_and_Benchmarks.pdf). Download: Google Drive (https://drive.google.com/file/d/1eFiIYyh5O2V90RA0brammGH6EpHvPDQe/view); "it means you agree to the license when you download the data."
- Size: 18,066 third-grade students (only those with over 200 interactions), 7,652 questions, 865 KCs, 5,549,635 interactions. Chinese math. Millisecond timestamps; no response-time field.
- Contents: question text, analysis, type, images, KC routes (hierarchy), embeddings; multi-KC questions ("_"-separated, expanded to KC level). Files include kc_level/train_valid_sequences.csv (fold, uid, questions, concepts, responses, timestamps, selectmasks, is_repeat), test.csv, question_level/, metadata/questions.json and kc_routes_map.json. The README says raw interaction counts cannot be reconstructed from the processed files. Student and question IDs are mapped to non-reversible identifiers.
- Licence: repo LICENSE is "MIT License Copyright (c) 2023 ai4ed". Paper section 3.1: "The dataset can be freely downloaded from https://github.com/ai4ed/XES3G5M and used with the MIT license".
- Tools and papers: pyKT; the paper benchmarks 19 deep-learning KT models.

## 11. Duolingo: half-life regression and SLAM 2018

- **HLR data**: Harvard Dataverse doi:10.7910/DVN/N8XJME, "Replication Data for: A Trainable Spaced Repetition Model for Language Learning", published 2017-12-14, v1.0; code https://github.com/duolingo/halflife-regression ("Copyright (c) 2016 Duolingo, Inc. MIT License."). File `settles.acl16.learning_traces.13m.csv.gz`, 379,004,009 bytes (README says 361 MB), unrestricted. Terms: "This work is released under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)." README: "When using this data set and/or software, please cite this publication" (Settles & Meeder, ACL 2016, pp. 1848-1858, doi 10.18653/v1/P16-1174).
- Size: "two weeks of Duolingo log data, containing 12.9 million student-word lesson and practice session traces" (README: about 13 million). Fields: p_recall, timestamp (UNIX), delta (seconds since last practice of the lexeme), user_id (anonymized), learning_language, ui_language, lexeme_id, lexeme_string, history_seen, history_correct, session_seen, session_correct. Session-aggregated, not per trial; no per-response duration or hints. Vocabulary items, not math. Paper results on the full set (90/10 split) include HLR MAE 0.128 and AUC 0.538. HLR is also in srs-benchmark.
- **SLAM 2018** (https://sharedtask.duolingo.com/2018.html ; Dataverse doi:10.7910/DVN/8SWHNO, published 2018-01-10, v4.0 of 2019-02-13): same CC BY-NC 4.0 statement. Tracks en_es, es_en, fr_en. Over 2M tokens from over 6,000 students in their first 30 days; about 83% of tokens labeled 0. Fields: user, countries, days (elapsed since start, not calendar), client, session, format, time (seconds; can be null), token, POS, morphology, dependency, label (0/1 mistake); labels only, not the student's answers. Cite Settles, Brust, Gustafson, Hagiwara, Madnani 2018 (BEA workshop).

## 12. Anki / FSRS review logs (open-spaced-repetition)

**anki-revlogs-10k** (https://huggingface.co/datasets/open-spaced-repetition/anki-revlogs-10k)
- HF metadata: gated "auto", license "other", license_name "anki-revlogs-10k", DOI 10.57967/hf/3435; created 2024-10-29, last modified 2025-08-22; 15.7 GB; 29,385 downloads. Gate text: "You need to agree to share your Hugging Face information to access this dataset." and "This repository is publicly accessible, but you have to accept the conditions to access its files and content."
- Content: random sample of 10,000 collections with 5,000+ revlog entries, mixing older and newer users. Rows: revlogs 727,738,650; cards 208,432,491; decks 2,066,838 (HF's "938M" is the sum). Files: revlogs/user_id=*/data.parquet (10,000), cards (9,934), decks (10,000), LICENSE (326 B), README.md.
- Fields. Revlogs: card_id, day_offset (days since first review), rating 1-4, state 0-3, duration (ms, 0-60000), elapsed_days (-1 for new), elapsed_seconds (-1 for new); chronological. Cards: card_id, note_id, deck_id. Decks: deck_id, parent_id, preset_id. No absolute timestamps; no card text.
- **Licence text**, read from https://huggingface.co/datasets/open-spaced-repetition/anki-revlogs-10k/blob/main/LICENSE (identical in FSRS-Anki-20k and anki-revlogs-10k-id; the 326-byte size fits CRLF line breaks):

> This data was provided to the FSRS project for use in memory research.
> University students and individuals may also use it for their own research.
> Please do not redistribute the data publicly (other than linking here).
> If you wish to use the data in other contexts, please request permission on
> https://anki.tenderapp.com.

  The text does not mention commercial use, derived statistics, fitted parameters, trained models or attribution.
- Secondhand context (not authoritative). srs-benchmark issue #353 (https://github.com/open-spaced-repetition/srs-benchmark/issues/353): Expertium asks the licence to say whether a model trained on the 10k data may be used in a personal, free or paid app; calls the licence "reportedly written by Dae" and says "Its license allows use for memory research only."; notes the repo has no licence file. L-M-Sherlock said he thought nobody uses the models directly. No maintainer gave a clear answer on personal, free-app, paid-app, commercial or redistribution use. The issue author is building an offline educational study app and wants to redistribute the RWKV checkpoint `RWKV_trained_on_5000_10000.pth`. Anki forum "Proposal: open dataset for content-aware schedulers" (giacomoran, Oct 23, 2025), paraphrased: AnkiWeb's privacy policy allows use of review histories for research but does not cover card content; the AnkiWeb page itself was not retrieved. A third-party repo (`huynhanhkhiem-dms/anchor-identifiability-spaced-repetition`) publishes only aggregate summaries of the data under MIT.

**Related datasets (all HF, open-spaced-repetition)**
- `anki-revlogs-10k-raw`: gated auto, created 2025-08-22, 8.46 GB, one `revlogs.7z` of protobuf `.revlog` files with more detail than the parquet set.
- `anki-revlogs-10k-id`: gated auto, created 2026-08-26, 21.4 GB. Keeps original signed 64-bit Anki IDs and adds `review_time` (epoch ms). Card: "Please follow the access and use restrictions of the source dataset."
- `FSRS-Anki-20k`: gated auto, license name "fsrs-anki-20k", DOI 10.57967/hf/3079, created 2024-02-24, last modified 2024-11-05; about 20,000 collections with 5,000+ revlog entries; about 99 GB listed. Fields: card_id, review_th, elapsed_days, elapsed_seconds, rating, state 0-4, duration. Deprecated in favour of the 10k set (per awesome-fsrs and its card). Same LICENSE text.
- `fsrs-dataset`: MIT, not gated, 2023, csv; README is front matter only. `srs-benchmark-raw`: not gated, 19 raw-prediction JSONL files, 139 GB, no licence in card.
- GitHub `anki-revlogs-dataset-builder`: code under "GNU AGPL, version 3 or later". awesome-fsrs (CC0) lists these sets and states no dataset licences.

**srs-benchmark** (https://github.com/open-spaced-repetition/srs-benchmark)
- No LICENSE file found (raw LICENSE 404; pyproject has no licence field). Repo licence: none found (UNVERIFIED).
- README: 9,999 collections (10,000 with same-day reviews); about 727M reviews; 349,923,850 reviews used in evaluation; metrics Log Loss, RMSE(bins), AUC. Log loss without same-day reviews: RWKV-Instant 0.2773; GRU 0.3328 (503 params); FSRS-7 0.3401 (34 params); FSRS-6 0.3460 (21 params; RMSE(bins) 0.0653; AUC 0.7034); FSRS-5 0.3561; FSRS-4.5 0.3625; AVG 0.3945; HLR 0.4694 (3 params). FSRS-7 default parameters are listed in the README.
- Published per-user outputs (JSONL, one line per user: `{"metrics":{...},"user":1,"size":10620,"parameters":{"0":[21 floats]}}`): `result/FSRS-6-short.jsonl` (3,438,264 bytes), `FSRS-6-recency`, `HLR` (3 params per user), `FSRS-4.5`, `AVG`, `RWKV-P` (HEAD 200); `result-20k/FSRS-5.jsonl` (19 params per user). Not found (404): FSRS-6, FSRS-5, FSRS-7, FSRS-rs, GRU-P, LSTM `.jsonl`. A Zenodo paper (10.5281/zenodo.22727105) is cited for the SBD model.

## 13. MaiMemo and other review logs

- **MaiMemo** (Harvard Dataverse doi:10.7910/DVN/VAGUL0), "Replication Data for: A Stochastic Shortest Path Algorithm for Optimizing Spaced Repetition Scheduling" (Ye, Su, Cao, KDD 2022; Su et al., IEEE TKDE 2023, doi 10.1109/TKDE.2023.3251721). v2.0 (2025-09-03). Terms: "This work is released under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0)." Code https://github.com/maimemo/SSP-MMC-Plus is MIT. 220 million memory-behavior logs; main file `opensource_dataset_raw.tsv.7z` (1,708,611,032 bytes). Columns: u, w, i, d, t_history, r_history, delta_t, r, p_recall, total_cnt. Vocabulary learning.
- AnkiHub, "Comparing memory models on a 4B reviews dataset" (community.ankihub.net): availability and licence UNVERIFIED. KARL and Mnemosyne logs: not researched.

## 14. College-level calculus, physics, circuits, MOOCs

- Timestamped college-level sets are on DataShop (sections 5-6).
- HarvardX Person-Course AY2013 De-Identified v3.0 (Dataverse doi:10.7910/DVN/26147): "each record represents one individual's activity in one edX course", so aggregate, not item level. File `HXPC13_DI_v3_11-13-2019.tab` (39,454,481 bytes). Terms: "Users of the dataset agree to abide by the Dataverse Community Norms, specifically: Maintaining anonymity of human subjects..."
- Not found: public item-level, timestamped MITx 6.002x or 8.MReV data. Pardos et al. (EDM 2013) fitted BKT to edX data; public availability UNVERIFIED. Nothing public found for Möbius, STACK or WeBWorK logs outside DataShop; the WeBWorK OPL is a problem library, not logs. MOOCCubeX and the EDM data-set awards page were not checked.

## 15. Preprocessing tools

- **pyKT** (`pykt-toolkit`): PyPI 0.0.38 (2022-10-16), MIT classifier; arXiv 2206.11460 (NeurIPS 2022 D&B). Docs (https://pykt-toolkit.readthedocs.io/en/latest/datasets.html) list ASSISTments2009/2012/2015/2017, Algebra2005, Bridge2006, Statics2011, NIPS34, EdNet, POJ. Ships no data.
- **EduData** (bigdata-ustc): PyPI 0.0.18 (2021-08-20). Docs cover ASSISTments 2009-10/2015/2017, EdNet KT1, junyi, math2015, OLI_Fall2011, KDD Cup 2010, Math23k, pisa2015math. Copyright 2021 bigdata-ustc; PyPI licence field empty, so licence UNVERIFIED. **EduKTM** 0.0.10 (2022-05-18), licence field empty.
- **pyBKT** 1.4.3 (2026-08-05), MIT. **LKT** (CRAN) 1.7.0 (2024-07-01), GPL-3, Pavlik & Eglington, uses LiblineaR; "The LKT model relies on data being in the DataShop format, but only some columns are needed" (needs Anon.Student.Id and Outcome CORRECT/INCORRECT).

## 16. Could not find or verify

- Kaggle Eedi 2024 licence, fields and size; Kaggle Riiid competition terms (Kaggle pages and API need login); the official Eedi Misconceptions Graph URL (only a third-party mirror found).
- The "original data usage agreement" for KDD Cup 2010; grade level of the KDD sets; DataShop overview statistics (students, KCs) for OLI Statics and other sets (the guest view hides them); the DataShop IRB/shareability help page (help?page=irb) was not read.
- ASSISTments 2017 column spec; count mismatches across pyKT, AKT, XES3G5M and DAS3H for 2009-10, 2012-13, 2015 and 2017; sizes and fields of the newer etrials releases; whether the "Responsible Use Guidelines" page applies to FoundationalASSIST.
- srs-benchmark repo licence (none found). Whether the anki-revlogs-10k licence permits publishing derived parameters, models or statistics: the licence text is silent, and only secondhand discussion exists (issue #353). AnkiWeb privacy policy text not retrieved.
- AnkiHub 4B-review dataset; KARL; Mnemosyne; MOOCCubeX; public item-level college physics, circuits or calculus MOOC data outside DataShop.
- Which datasets the forgetting-aware KT papers DKT-Forgetting, HawkesKT, LPKT and MEMORIZE used (only DAS3H and AKT were checked); spacing content of the Pavlik and Memphis DataShop sets (titles only).
- Third-party GitHub, HF or PyPI mirrors of the KDD Cup, ASSISTments, EdNet, Junyi and Eedi data were not searched systematically; only the mirrors named above were seen.
