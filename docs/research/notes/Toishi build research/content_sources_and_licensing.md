# Content sources and licensing for an offline FSRS problem bank (College Algebra through Chem, plus C++)

Method note: License pages and policies were checked on primary sites where they loaded. The main repositories (OPL, renderer, PG, OpenStax osbooks bundles, CLP 1-4, APEX PreTeXt, Hefferon, FCLA, ULA, ILA, OpenIntro Statistics, Exercism) were shallow-cloned on 2026-11-01, and their LICENSE files, markup and problem counts were read directly from the source. Counts marked "counted from clone" come from scripts run over those clones (grep and XML parsing), not from publisher claims. The shared web-search budget ran out partway through, and several Japanese university sites and gnu.org refused automated fetches. The Gaps sections say where this left questions open.

## 1. Best openly licensed problem sources per course, with answers or solutions

### Takeaway
For every math course except Statistics, the core bank can come from four sources. The WeBWorK OPL gives randomized problems with computed answers. OpenStax gives section exercises in XML with odd-numbered solutions. CLP gives about 2,370 calculus problems, almost all with a hint, answer and full solution. Hefferon, ULA and FCLA cover linear algebra. Statistics adds OpenIntro. Calculus-based physics relies on OpenStax University Physics. Chemistry has essentially one large open source: OpenStax Chemistry 2e, with about 1,736 exercises, half of them with solutions. C++ should start with the Exercism C++ track (MIT, with tests and reference solutions). One important correction to the starting assumptions: OpenStax relicensed College Algebra/Precalc, University Physics, Chemistry 2e and Introductory Statistics from CC BY 4.0 to CC BY-NC-SA 4.0 in March 2026.

### Cited Findings

**WeBWorK Open Problem Library (OPL), all math courses and some physics**
- License: "Unless otherwise indicated, all contributions to the WeBWorK Open Problem Library are licensed under the Creative Commons Attribution-NonCommercial-ShareAlike 3.0 Unported License." Copyright stays with the authors, and contributors may choose alternative OSI licenses — [OPL_LICENSE in repo](https://github.com/openwebwork/webwork-open-problem-library); [NPL wiki](https://webwork.maa.org/wiki/NPL)
- Size: the wiki says "approximately 35,000 problems" — [NPL wiki](https://webwork.maa.org/wiki/NPL). The repo itself holds 77,134 `.pg` files: OpenProblemLibrary/ 40,541, Contrib/ 29,624, Pending/ 6,969 (counted from clone, last commit 2026-10-29). The repo README says users "should ignore the contents of Pending" — [repo README](https://github.com/openwebwork/webwork-open-problem-library)
- Counts by DBsubject tag in OpenProblemLibrary/ (number with an explicit worked-solution block in parentheses): Algebra 9,225 (4,721); Calculus - single variable 8,638 (2,502); Linear algebra 1,770 (407); Calculus - multivariable 1,575 (626); Differential equations 1,302 (215); Statistics 1,068 (370); Trigonometry 992 (310); Probability 768 (227). In Contrib/: Algebra 8,460 (5,709); Calculus - single variable 2,709 (1,833) plus "Calculus" 2,036 (778); Statistics 1,000 (554); Trigonometry 828 (727); Linear algebra 754 plus "Linear Algebra" 355 (131 with solutions in total); Probability 385; Calculus - multivariable 319 (147); Precalculus 103. These are counted from clone. OPL/ and Contrib/ partly mirror each other (both contain UBC, PCC, etc.), so the totals include duplicates. Every PG problem computes its own correct answer, so "with solution" here means a worked-solution text block, not an answer key.
- 7,568 OPL/ files carry the subject "ZZZ-Inserted Text" and 2,472 carry "WeBWorK". These are set headers, orientation or demo material, not course problems (counted from clone).
- Some Contrib folders use other licenses. Contrib/UBC has 1,218 files headed "Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)" and 71 under CC BY 4.0. Contrib/USask has 954 files that mention both CC BY 4.0 and BY-SA 4.0. Contrib/DouglasCollege has 578 under CC BY 4.0, Contrib/SFU 45 under CC-BY-4.0, and Contrib/CCCS/* is CC BY-NC-SA 4.0 by LICENSE.TXT (counted from clone) — [OPL repo](https://github.com/openwebwork/webwork-open-problem-library)
- Some OPL content mirrors commercial textbooks. OpenProblemLibrary/Wiley has 413 files tagged `Institution(John Wiley & Sons)`, `AuthorText1('Anton')`, `Problem1('9 11 12')`. OpenProblemLibrary/WHFreeman has 1,264 files (Rogawski Calculus ET 2e, Holt Linear Algebra). 7,581 files carry Stewart textbook tags (counted from clone).

**OpenStax, the XML textbook sources with exercises and solutions**
- License change: the osbooks LICENSE files moved from "Attribution 4.0 International" to "Attribution-NonCommercial-ShareAlike 4.0 International". The college-algebra bundle changed on 2026-03-18 (commit 8c1dc56, "updating preface and repo to CC BY NC-SA"), and university-physics, chemistry and introductory-statistics on 2026-03-19 (git history read from clones) — [osbooks-college-algebra-bundle](https://github.com/openstax/osbooks-college-algebra-bundle), [osbooks-university-physics-bundle](https://github.com/openstax/osbooks-university-physics-bundle), [osbooks-chemistry-bundle](https://github.com/openstax/osbooks-chemistry-bundle), [osbooks-introductory-statistics-bundle](https://github.com/openstax/osbooks-introductory-statistics-bundle)
- OpenStax says it moved "from a mix of CC BY and CC BY-NC-SA licensing" to CC BY-NC-SA, applying to "all newly released and updated versions of our titles, with limited exceptions" — [OpenStax license page/blog](https://openstax.org/license). Its help center now states that OpenStax textbooks use CC BY-NC-SA 4.0 — [OpenStax help](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks). Wikipedia/Wikiversity still describe most OpenStax books as CC BY, which is now out of date — [Wikipedia](https://en.wikipedia.org/wiki/OpenStax)
- The Calculus bundle (Vols 1–3) is CC BY-NC-SA 4.0. Each `collection.xml` carries `<md:license url="http://creativecommons.org/licenses/by-nc-sa/4.0/">` — [osbooks-calculus-bundle](https://github.com/openstax/osbooks-calculus-bundle)
- The college-algebra bundle contains College Algebra 2e, Precalculus 2e, Algebra and Trigonometry 2e, and College Algebra with Corequisite Support 2e — [repo](https://github.com/openstax/osbooks-college-algebra-bundle)
- Exercise counts, counted from clone (total, then how many have a `<solution>` element):
  - Calculus Vol 1: section exercises 2,278 (1,124 solved, i.e. the odd ones); review 156 (78); checkpoints 268 (267); worked examples 327
  - Calculus Vol 2: section exercises 2,491 (1,232); review 183 (90); checkpoints 211 (208); examples 253
  - Calculus Vol 3: section exercises 2,294 (1,104); review 185 (91); checkpoints 280 (275); examples 334
  - College Algebra 2e: section exercises 3,809 (1,918); review 563 (283); practice test 275 (140); "try it" 437 (424); examples 640. The Corequisite edition has identical exercise counts.
  - Precalculus 2e: section exercises 4,824 (2,430); review 691 (347); practice test 388 (198); "try it" 490 (482); examples 727
  - Algebra & Trigonometry 2e: section exercises 5,189 (2,612); review 767 (386); practice test 409 (208); "try it" 565 (552); examples 837. It shares many modules with College Algebra 2e and Precalculus 2e, so deduplicate by module id.
  - Introductory Statistics 2e: practice 844 (430); homework/free-response 538 (262); "bringing it together" homework 50 (27); "try it" 242 (34); examples 200
  - University Physics Vol 1: problems 1,036 (518); additional problems 326 (162); challenge 110 (58); conceptual 376 (189); check-your-understanding 153 (152)
  - University Physics Vol 2: problems 815 (408); additional 290 (145); challenge 119 (61); conceptual 358 (183); check 126 (121)
  - University Physics Vol 3: problems 617 (308); additional 258 (131); challenge 45 (22); conceptual 296 (150); check 76 (76)
  - Chemistry 2e: end-of-chapter exercises 1,736 (873). Chemistry: Atoms First 2e: 1,737 (873), largely the same exercises.

**CLP Calculus (UBC; Calc 1, 2, 3)**
- License: "It is licensed under a Creative Commons BY-NC-SA 4.0 International License" (CLP-1 through CLP-4). Sources are at github.com/arechnitzer/CLP1 through CLP4 — [CLP source page](https://personal.math.ubc.ca/~CLP/src/); the LICENSE in the repo is CC BY-NC-SA 4.0 — [arechnitzer/CLP1](https://github.com/arechnitzer/CLP1)
- The repos hold LaTeX (separate textbook and problembook) and PreTeXt; in PreTeXt, "The hints, answers and solutions are included in appendices" — [CLP1 README](https://github.com/arechnitzer/CLP1)
- Problem-book counts (counted from clone, LaTeX problembook): CLP-1 704 questions with 704 answers, 704 solutions and 630 hints; CLP-2 742 with 742/742/740; CLP-3 497 with 497/497/497; CLP-4 426 with 424/424/424. That is about 2,369 problems in total, nearly all with an answer and a full solution.
- Questions are grouped into Conceptual, Procedural and Application. A "representative question set" (outlined in blue) covers the essentials, and starred problems were "pulled from quizzes and exams given at UBC for Math 100 and 180 ... and Math 120" — CLP-1 problembook howtouse.tex, [repo](https://github.com/arechnitzer/CLP1)
- The repos were last committed in August 2024 (from clone).

**APEX Calculus (Calc 1–3)**
- License: "Licensed to the public under Creative Commons Attribution-Noncommercial 4.0 International Public License" (CC BY-NC, **no ShareAlike**) — copyright page in [APEXCalculus_Source](https://github.com/APEXCalculus/APEXCalculus_Source) and `<minilicense>Creative Commons BY NC</minilicense>` in [APEXCalculusPTX](https://github.com/APEXCalculus/APEXCalculusPTX)
- The PreTeXt edition is active (last commit 2026-10-29) and contains 3,785 `<exercise>` elements, 2,582 `<webwork>` elements (embedded PG), 650 `<answer>` and 1,950 `<solution>` elements (counted from clone) — [APEXCalculusPTX](https://github.com/APEXCalculus/APEXCalculusPTX)
- The old LaTeX v3 source repo is marked "Outdated" and has 3,061 per-exercise .tex files in a `{problem}{answer}` form — [APEXCalculus_Source](https://github.com/APEXCalculus/APEXCalculus_Source)

**Active Calculus / Active Prelude to Calculus**
- "Each text carries a Creative Commons BY-SA license", and every section has "anonymous interactive WeBWorK exercises". Source is on GitHub under active-calculus — [activecalculus.org](https://activecalculus.org/). The org's public repos are active-calculus-single-mbx, prep (Active Prelude to Calculus), active-calculus-vector, and active-calculus-single-graphics — [GitHub org](https://github.com/active-calculus)

**Linear Algebra**
- Hefferon, *Linear Algebra*: "Use it under either the GNU Free Documentation License or the Creative Commons ... Attribution-ShareAlike 2.5 License, at your discretion" (LICENSE, 2016). Source is on GitLab (last commit 2026-10-31) — [gitlab.com/jim.hefferon/linear-algebra](https://gitlab.com/jim.hefferon/linear-algebra); [book site](https://joshua.smcvt.edu/linearalgebra/). The answer book "gives the answer to every one, completely worked" — [hefferon.net](https://hefferon.net/linearalgebra/). The chapter sources contain 1,063 `\begin{answer}` blocks, inline after each exercise (counted from clone).
- Beezer, *A First Course in Linear Algebra* (FCLA): "GNU Free Documentation License, Version 1.2 or any later version ... with no Invariant Sections". Its XML `src/` has 554 `<exercise>` and 359 `<solution>` elements (counted from clone) — [rbeezer/fcla](https://github.com/rbeezer/fcla)
- Austin, *Understanding Linear Algebra*: "distributed under a Creative Commons BY 4.0 license", written in PreTeXt. Its `src/` holds 436 `<exercise>` and 551 `<solution>` elements (counted from clone, last commit 2026-09-18) — [davidaustinm/ula](https://github.com/davidaustinm/ula)
- Margalit & Rabinoff, *Interactive Linear Algebra*: source files carry the GFDL 1.3 header. The source has only about 20 `<exercise>` elements and 191 solution/answer elements, so it is mostly examples and not a deep bank (counted from clone) — [QBobWatson/ila](https://github.com/QBobWatson/ila)

**Statistics and probability**
- OpenIntro Statistics: "Creative Commons Attribution-ShareAlike 3.0 Unported license (CC BY-SA)". The LICENSE adds a "Communication obligation. Any derivative work must communicate that it is licensed under a CC BY-SA license" — [openintrostat/openintro-statistics](https://github.com/openintrostat/openintro-statistics). End-of-chapter exercises are `\eoce{}` macros in `ch_*/TeX/*.tex`, and solutions are 203 `\eocesol{}` entries in `extraTeX/eoceSolutions/eoceSolutions.tex`, apparently odd-numbered only (counted from clone).
- Grinstead & Snell, *Introduction to Probability*: GNU FDL. Answers to odd-numbered problems are on the website, and full solutions are given only to instructors on request — [Dartmouth CHANCE](https://chance.dartmouth.edu/teaching_aids/books_articles/probability_book/book.html)
- OpenStax Introductory Statistics 2e: CC BY-NC-SA 4.0 since March 2026 (see above).

**Precalculus alternatives**
- Stitz–Zeager: the site's CC badge links to CC BY-NC-SA 3.0, and LaTeX source for "Precalculus, 4th Edition" (preliminary) can be downloaded as a zip — [stitz-zeager.com](https://www.stitz-zeager.com/)
- AIM Open Textbook Initiative approved list (it does not state licenses): Yoshiwara *Modeling, Functions, and Graphs* and *Trigonometry*; Stitz–Zeager; Guichard *Calculus*; Active Calculus; APEX; CLP; Corral; Understanding Linear Algebra; Beezer; Hefferon; Treil; Grinstead & Snell; OpenIntro Statistics; Introduction to Modern Statistics — [AIM approved textbooks](https://textbooks.aimath.org/textbooks/approved-textbooks/)

**MIT OpenCourseWare**
- License CC BY-NC-SA 4.0. MIT's NC interpretation is that "users may not sell, profit from, or commercialize OCW materials", and the test looks at the use, not the user — [OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/)
- 18.01SC Single Variable Calculus links to CC BY-NC-SA 4.0 and includes "Problem sets with solutions" and "Exams with solutions" (Exam 1–4 and a Final) — [18.01SC](https://ocw.mit.edu/courses/18-01sc-single-variable-calculus-fall-2010/)

**Physics (calculus-based) beyond OpenStax**
- OPL Contrib/BrockPhysics has problems "mostly taken from the OpenStax College Physics textbook, by Urone et al." plus some modern-physics problems "from various textbooks" — [BrockPhysics README in OPL](https://github.com/openwebwork/webwork-open-problem-library). Counts: College_Physics_Urone 2,160; University_Physics_Ling (OpenStax UP Vol 3, modern physics) 214; Modern_Physics_Taylor 54; Modern_Physics_Tipler 38 (counted from clone). College Physics is algebra-based.
- Physics subjects tagged in OPL/Contrib: Mechanics 615, Electricity 569, Optics 349, Thermodynamics 301 (plus 125 in OPL/), Fluids 174, Modern Physics 252, mostly in BrockPhysics and Keele/College_Physics_Wolfe (counted from clone).
- Crowell, *Light and Matter*: the site says "Web site and books (c) 1998-2019 Benjamin Crowell, CC-BY-SA license" (CC BY-SA 3.0 US). LaTeX source is at lightandmatter.com/books.html — [lightandmatter.com](https://www.lightandmatter.com/), [LM page](https://www.lightandmatter.com/lm/)
- Physics LibreTexts: licensing is page-level. The home page says it "is shared under a not declared license" — [phys.libretexts.org](https://phys.libretexts.org/)

**Chemistry**
- OpenStax Chemistry 2e and Atoms First 2e: CC BY-NC-SA 4.0 since 2026-03-19, with 1,736 and 1,737 exercises, 873 with solutions (see above).
- The OPL has essentially no chemistry. A keyword search for chemistry, stoichiometry and molar found 21 files in BrockPhysics and a handful elsewhere (counted from clone).

**C++ programming**
- Exercism C++ track: MIT License ("Copyright (c) 2021 Exercism"). It has 86 practice exercises and 15 concept exercises. Each practice exercise ships a stub, a `*_test.cpp`, and `.meta/example.cpp` (reference solution) plus `tests.toml` (from clone) — [exercism/cpp](https://github.com/exercism/cpp)
- Exercism problem-specifications: MIT License, 152 exercises with canonical data — [exercism/problem-specifications](https://github.com/exercism/problem-specifications)
- Project Euler: problems in the Archives and Recent sections are CC BY-NC-SA 4.0 and "must not be used for commercial purposes". Suggested attribution is "The following problem is taken from Project Euler", with a link to https://projecteuler.net/problem={id}. Bonus problems and member stats "may not be published or shared elsewhere", and forum posts belong to their posters — [Project Euler copyright](https://projecteuler.net/copyright)
- Rosetta Code: "Content, once submitted to this site, becomes available under the GFDL (v1.2)" — [Rosetta Code copyrights](https://rosettacode.org/wiki/Rosetta_Code:Copyrights)

**Explicitly not usable**
- Paul's Online Math Notes: content is "the copyrighted property of Paul Dawkins and is not to be considered to be in the public domain". Mirroring or including it on other sites needs "the express written consent of Paul Dawkins" — [Lamar terms](https://tutorial.math.lamar.edu/Terms.aspx)
- LeetCode: not openly licensed. The terms page could not be fetched, but nothing indicates an open license; treat it as unusable.
- OpenStax Exercises (exercises.openstax.org): site content is Rice copyright unless a question has its own license, and "each question's own copyright and licensing information governs it" — [OpenStax Exercises copyright](https://exercises.openstax.org/copyright)

### Inferences
- Suggested core bank by course (all sources free; licenses as above):

| Course | Primary sources (license) | Rough size | Answers / solutions |
|---|---|---|---|
| College Algebra | OpenStax College Algebra 2e (BY-NC-SA 4.0); OPL Algebra (BY-NC-SA 3.0); Stitz–Zeager (BY-NC-SA 3.0) | ~3.8k OpenStax section exercises; ~17k OPL algebra files (with dupes) | OpenStax: odd solutions + all try-its/examples; OPL: computed answer for every seed, ~50–65% with worked solution |
| Trig / Precalc | OpenStax Precalculus 2e / Algebra & Trig 2e; OPL Trigonometry + Precalculus; Active Prelude (BY-SA) | ~4.8k OpenStax; ~1.8k OPL trig | as above |
| Calc 1–3 | CLP 1–4 (BY-NC-SA 4.0); OpenStax Calculus 1–3 (BY-NC-SA 4.0); OPL calculus; APEX PTX (BY-NC 4.0); Active Calculus (BY-SA) | ~2.4k CLP; ~7k OpenStax section exercises; ~13k OPL calculus files; ~3.8k APEX | CLP: full solutions to nearly all; OpenStax: odd; OPL: computed answers |
| Linear Algebra | Hefferon (GFDL or BY-SA 2.5); ULA (BY 4.0); FCLA (GFDL 1.2+); OPL linear algebra | ~1k Hefferon answers; 436 ULA; 554 FCLA; ~2.9k OPL | Hefferon: all worked; ULA/FCLA: many |
| Statistics | OpenIntro Statistics (BY-SA 3.0); OpenStax Intro Stats 2e (BY-NC-SA 4.0); OPL Statistics/Probability; Grinstead & Snell (GFDL) | ~400 OpenIntro eoce; ~1.4k OpenStax; ~3.2k OPL | odd-numbered solutions mostly |
| Physics 1–2 (calc) | OpenStax University Physics 1–2 (BY-NC-SA 4.0); OPL BrockPhysics (algebra-based, randomized); Light and Matter (BY-SA) | ~1.85k problems + ~600 additional/challenge in UP 1–2 | ~half solved (odd) in OpenStax; OPL computed |
| Gen Chem | OpenStax Chemistry 2e (BY-NC-SA 4.0) | ~1.7k | odd solutions (873) |
| C++ | Exercism cpp (MIT); Project Euler (BY-NC-SA 4.0, statements only); Rosetta Code (GFDL 1.2) | 101 Exercism; ~900+ PE (count not verified) | Exercism has tests + reference solutions |

- For a strict rule of "no copyrighted textbook exercises", OPL directories that mirror commercial textbooks are a gray zone even though the OPL license covers them. These are OpenProblemLibrary/Wiley (Anton), OpenProblemLibrary/WHFreeman (Rogawski, Holt), the BrockPhysics Modern_Physics_Tipler and Modern_Physics_Taylor sets (BrockPhysics itself says they come "from various textbooks"), and probably sets written as numbered exercises of a commercial text (Problem1('n') tags). A conservative build excludes them. Many OPL problems carry textbook tags only as cross-references, so the tags alone are not proof of copying.
- Odd-only solution coverage in OpenStax means about half of each OpenStax set has no key. In an FSRS app, unsolved items could be kept as "self-graded" or skipped. CLP and OPL fill the gap for calculus.

### Gaps
- Active Calculus, Active Prelude and Light and Matter exercise and answer counts were not measured (no clone made).
- Kuttler's linear algebra books and MathQuest/MathVote: no license or size verified. The MathQuest site states no license.
- MIT OCW 18.02, 18.06, 8.01, 8.02 and 5.111: individual course licenses and solution availability were not checked one by one. The general OCW terms apply, but third-party exclusions vary by course.
- The exact number of Project Euler problems was not verified.
- Stitz–Zeager answer coverage was not verified on the site.

## 2. License obligations: mixing licenses, NonCommercial, attribution, trademarks, third-party content

### Takeaway
CC license conditions apply only when material is "Shared" with the public. A strictly private build therefore has almost no obligations, but the database should still record per-item attribution so a later public release stays possible. Keeping items from differently licensed sources as separate, attributed entries in one database is a collection (combination), not an adaptation. That is allowed if each item is attributed and the NC terms are respected. Rewriting, translating or merging items creates adaptations, and an adaptation can never mix BY-SA and BY-NC-SA material. GFDL items need their own separate handling.

### Cited Findings
- CC BY-NC-SA 4.0 defines NonCommercial as "not primarily intended for or directed towards commercial advantage or monetary compensation" — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- Attribution (3(a)(1)): if the licensor supplies them, you must retain creator identification, a copyright notice, a notice referring to the license, a notice about the disclaimer of warranties, and a URI to the material "to the extent reasonably practicable". You must also indicate modifications and keep earlier modification notices. These may be satisfied "in any reasonable manner based on the medium" — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- The attribution and ShareAlike conditions apply "If You Share", and "Share" means providing material "to the public" — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en)
- ShareAlike (3(b)): an adapter's license must be a CC license "with the same License Elements", this version or later, or a "BY-NC-SA Compatible License" — [legal code](https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode.en). "Currently, no non-CC licenses have been designated as compatible with BY-NC-SA 4.0." BY-SA 4.0 adaptations may only be licensed under BY-SA 4.0 (or later or ported versions) or a BY-SA Compatible License (Free Art 1.3; GPLv3 one-way) — [CC compatible licenses](https://creativecommons.org/share-your-work/licensing-considerations/compatible-licenses/)
- On combining: "It depends. The first question to ask is whether doing so constitutes an adaptation." If no adaptation is created, you may combine CC content as long as you attribute and follow any NC restriction. If it is a remix, ShareAlike material generally requires the same or a compatible license — [CC FAQ](https://creativecommons.org/faq/)
- An adaptation is a modification with enough new creativity to be copyrightable, "such as a translation". "Format changes ... are not treated as adaptations under the licenses" — [CC FAQ](https://creativecommons.org/faq/)
- MIT OCW: NC means users may not "sell, profit from, or commercialize OCW materials or works derived from them"; internal training by a corporation is allowed. "you may not use MIT's names or logos ... without prior written consent of MIT", except as CC attribution. Other rights (publicity, privacy, moral) may limit use, and external linked sites may have other terms — [OCW terms](https://ocw.mit.edu/pages/privacy-and-terms-of-use/)
- OpenStax: credit OpenStax, include the book title, and link to the free version. Commercial use requires the Content Reuse Request Form — [OpenStax help](https://help.openstax.org/s/article/Licensing-information-of-OpenStax-textbooks); [commercial use](https://help.openstax.org/s/article/Commercial-use-under-the-Creative-Commons-License)
- OpenStax book prefaces (e.g. University Physics) state that users must "provide attribution to OpenStax and its content contributors, and distribute all derivatives under the same license". For unattributed art: "Copyright Rice University, OpenStax, under CC BY-NC-SA 4.0 license." (preface module text in [osbooks-university-physics-bundle](https://github.com/openstax/osbooks-university-physics-bundle))
- OpenStax hosts only the current and previous edition of each title and removes retired editions, advising users to "save a copy of the PDF" — [Edition retirement policy](https://openstax.org/openstax-edition-retirement-policy)
- The OPL is CC BY-NC-SA **3.0 Unported**, while some Contrib folders are CC BY-SA 4.0 (UBC), CC BY 4.0 (DouglasCollege, SFU, some UBC/USask) or CC BY-NC-SA 4.0 (CCCS). See Q1 — [OPL_LICENSE](https://github.com/openwebwork/webwork-open-problem-library)
- OpenIntro adds a "communication obligation": derivatives must say they are CC BY-SA — [OpenIntro LICENSE](https://github.com/openintrostat/openintro-statistics)
- Hefferon is dual-licensed (GFDL or CC BY-SA 2.5, "at your discretion"). FCLA is GFDL 1.2+ only and ILA is GFDL 1.3 — repos in Q1.
- The renderer is GPL-3.0 — [openwebwork/renderer](https://github.com/openwebwork/renderer). Its license covers the software, not the problems.

### Inferences
- A personal, never-distributed app is not "Sharing" under CC 4.0, so attribution and SA conditions are not triggered. In practice NC is satisfied because the app is never sold. If the project (the app or its repo with the bundled database) is ever published, even free, every condition applies.
- Recommended schema fields per problem: source_id, source_title, authors/creators, license SPDX id plus URL, original URL or path plus git commit, a modified flag with a description of changes, a "third-party" flag, and, for Japanese items, a "translated; unofficial solution" label. An "About/Credits" screen generated from these fields would meet the "reasonable manner" standard if the project is ever shared.
- Mixing safely: keep each item as a separate record (a collection, not an adaptation). Never merge text from a BY-SA source (OpenIntro, Hefferon-as-BY-SA, UBC Contrib, Active Calculus, Light and Matter) with text from a BY-NC-SA source (OPL, OpenStax, CLP, OCW, Project Euler) into one new problem. No license can satisfy both SA clauses. CC BY items (ULA, DouglasCollege) can go into either camp. APEX (BY-NC, no SA) can be adapted into BY-NC-SA items.
- Converting MathML or LaTeX to another markup and rendering it is a "format change", not an adaptation. Rewording, translating, or turning a static problem into a randomized template is an adaptation. Generating seeds from an unchanged PG file is most naturally treated as using the work, not adapting it.
- The OpenStax relicensing is not retroactive in effect. Copies of the osbooks repos from commits before 2026-03-18/19 were released under CC BY 4.0, and CC licenses are generally understood to be irrevocable for copies already distributed. Pinning to a pre-change commit would keep CC BY terms for those books. This rests on general CC principles; OpenStax's announcement did not address old versions in the text retrieved.
- OPL's 3.0 license versus 4.0 sources: for adaptations, CC BY-NC-SA 3.0 is generally understood to allow licensing under a later version with the same elements, which would make OPL plus OpenStax/CLP (4.0) adaptations workable as BY-NC-SA 4.0. The 3.0 legal code was not fetched to confirm this.
- Trademarks: do not use the OpenStax, MIT or university names or logos as branding. Use them only in attribution lines.

### Gaps
- The GFDL 1.2/1.3 text could not be fetched (gnu.org blocked automated access). Unverified details: the GFDL requirement to include the full license text with every distributed copy, the "aggregation with independent works" clause (section 7), and the MMC relicensing to CC BY-SA 3.0 (section 11) and whether it applies to FCLA or ILA. If FCLA or ILA items are bundled and the app is ever distributed, check those clauses.
- No primary OpenStax trademark policy page was retrieved. The help article does not address trademarks.
- The full OpenStax licensing blog post (date, the "limited exceptions") could not be read. Only its summary loaded.

## 3. Japanese university entrance exams (reuse policies, official answers, Common Test)

### Takeaway
Tokyo and Kyoto were confirmed to allow reuse without prior approval, with conditions: cite the source, mark modifications (Tokyo), label any non-official answers (Tokyo), get third-party permission yourself, and report within one month of publication. Kyoto publishes official math answers (解答例) for its latest exam, but UTokyo's 2026 math release contains only the examiners' intent (出題の意図), with no answers. Several other universities could not be verified because of fetch failures and the exhausted search budget.

### Cited Findings
- University of Tokyo (2nd-stage exams): may be used "事前に本学の承認を得ることなく" (without prior approval). Conditions: report each use "成果物の公表から１か月以内" (within one month of publishing the output) via the report form; clearly state the material is quoted from the 2nd-stage exam; "改変したことを必ず明示" (clearly state any modification); answers, explanations or scoring not published by UTokyo must be labeled "本学が公表したものでない" (not published by the university); third-party works need the user to get permission from the rights holder. Reporting is not required for prospective examinees studying on their own or for non-profit school staff teaching. Some questions may be withheld for rights reasons — [UTokyo policy PDF](https://www.u-tokyo.ac.jp/content/400243232.pdf); [UTokyo 2次利用 page](https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e01_10.html)
- UTokyo posts 3 years of 2nd-stage exams (2024–2026) — [UTokyo past exams](https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e01_04.html). The 2026 "出題の意図と解答" page links a 数学 PDF — [2026 page](https://www.u-tokyo.ac.jp/ja/admissions/undergraduate/e02_07_25.html). That PDF contains only the intent statement (three abilities assessed), with no problems and no model answers — [math PDF](https://www.u-tokyo.ac.jp/content/400239145.pdf)
- Kyoto University (policy, April 2019 version): permission "下記の条項に則って使用することを条件に許可します" (granted on condition of following the terms). Indicate the source. Submit the 利用報告書 (report form, PDF or Word) and a copy of the publication "刊行後1か月以内" (within one month of publication); for online use, submit a printout. Get permission from third-party rights holders. Schools are exempt for non-commercial educational use. The policy does not mention modification marking or translation — [Kyoto copyright policy](https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq/copyright-policy)
- Kyoto posts R7 (2025) and R8 (2026). R8 includes "解答又は解答例等及び出題意図" for 数学（文系）and 数学（理系）. For questions where "一義的な解答例等を示すことが適切でない" (a single model answer is not appropriate), only the intent is given — [Kyoto past exams](https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq); [R8 page](https://www.kyoto-u.ac.jp/ja/admissions/undergrad/past-eq/r8-eq)
- Meiji University (private): from FY2022, "事前の許諾申請は不要" (no prior application needed). Send a report and a copy of the output within one month. No fee. The university may ask users to stop if alteration or a missing source infringes moral rights. Covers general exams only — [Meiji notice, updated 2026-03-10](https://www.meiji.ac.jp/exam/info/2025/qfki0t00000gq9kh-att/a1773131235940.pdf)
- Chuo University (private, effective 2024-04-17): no prior approval. Report within one month. State that the material is a Chuo exam question. Disclose excerpts and modifications. Private copying and non-profit school use are exempt from reporting — [Chuo policy PDF](https://www.chuo-u.ac.jp/common_d/connect/admission/copyright-policy/copyright-policy.pdf)
- National Center for University Entrance Examinations (DNC): posts 3 years (2024–2026) of Common Test problems and 正解 (answer keys) for the main and make-up exams. The past-exam page itself has no reuse statement — [DNC past exams](https://www.dnc.ac.jp/kyotsu/kakomondai/)
- The CC FAQ classes translation as an adaptation — [CC FAQ](https://creativecommons.org/faq/). Japanese university policies use their own terms: UTokyo requires modifications to be marked, and Meiji and Chuo warn about moral rights (sources above).

### Inferences
- For an English app, every Japanese problem is a translation, so it is a modification under UTokyo's terms and should carry a "translated, modified" notice. Any worked solution for UTokyo math must be labeled unofficial, since UTokyo publishes none. Kyoto's 2026 math answers can be used as official, with the source cited.
- Reporting is tied to publication (公表/刊行). A purely private app arguably triggers no report. Publishing the app or its database (e.g., a public GitHub repo) would trigger a report within one month for each university.
- Math exams rarely contain third-party copyrighted material (unlike Japanese or English papers), but any figure or passage credited to a third party should be skipped.
- Archives are short (2–3 years on the official sites), so a Japanese-exam component will be small: perhaps a few dozen math problems per university per year. Extraction means PDF to OCR (Japanese plus math) to translation.

### Gaps
- Not verified: Osaka, Tohoku, Nagoya, Kyushu, Hokkaido, Institute of Science Tokyo (Tokyo Tech), Hitotsubashi, Waseda, Keio and Shinshu. Their pages either failed to load (Osaka, Nagoya and Kyushu returned client errors; Tohoku blocks robots) or were not reached before the web-search budget ran out. The brief's claim that Kyushu and Shinshu allow reuse with attribution is unconfirmed here.
- The DNC reuse/copyright policy for Common Test problems was not retrieved (dnc.ac.jp/copyright.html failed to load). Treat Common Test problems as not cleared until checked.
- It was not checked whether the UTokyo policy distinguishes commercial use. The PDF summary did not address it.
- The UTokyo report-form URL and the exact attribution wording format were not retrieved.

## 4. Olympiad and competition problems

### Takeaway
None of the major competitions checked offers an open license, so IMO, Putnam, HMMT and AoPS-hosted problems should be treated as unusable without written permission. Project Euler (CC BY-NC-SA 4.0) is the only competition-style source with explicit reuse permission, and it is for programming, not proof math.

### Cited Findings
- IMO problems page: only "© International Mathematical Olympiad", with no license statement — [imo-official.org problems](https://www.imo-official.org/problems.aspx)
- AoPS Terms of Service: materials "may be used for information purposes only". Users agree not to "reproduce, duplicate, copy, sell, resell or exploit for any commercial purposes". Users grant AoPS (not the public) a license to their posts. No open license for the Wiki or forums — [AoPS TOS](https://artofproblemsolving.com/company/tos)
- HMMT archive page: no copyright or license statement found — [HMMT archive](https://www.hmmt.org/www/archive/problems)
- Putnam (MAA): the page fetched had no license information for problems or solutions — [MAA Putnam page](https://www.maa.org/math-competitions/putnam-competition)
- Project Euler: CC BY-NC-SA 4.0 for Archives/Recent problems — [Project Euler copyright](https://projecteuler.net/copyright)

### Inferences
- "No license statement" means all rights reserved by default, so these are unusable under the user's rules.
- CLP starred problems (from past UBC exams) and MIT OCW exams already cover the "exam-style hard problem" niche under open licenses.

### Gaps
- BMT and SMT archives and the MAA's own terms of use page were not checked because of the search budget.
- No CC-licensed math competition was found in this session.

## 5. Machine-readable formats and cheapest extraction methods

### Takeaway
In order of cost: OpenStax CNXML, CLP/ULA/FCLA PreTeXt XML, and Hefferon/OpenIntro LaTeX can be parsed directly with an XML or LaTeX parser and need no rendering. The OPL needs PG (Perl) execution, which is best done with the openwebwork/renderer Docker image: loop over files and seeds and POST with `isInstructor=1` and `_format=json` to get HTML, tags and the answer hash. OCW and Japanese exams are PDFs and need math-aware OCR, which makes them the most expensive.

### Cited Findings
- **OPL repo:** a full shallow clone has a 2.3 GB working tree with 88,025 files (measured). OpenProblemLibrary/ is 296 MB and Contrib/ 1.1 GB (measured). Contrib problems can also be used "by making symbolic links from the templates directories" — [OPL repo](https://github.com/openwebwork/webwork-open-problem-library)
- **Renderer (GPL-3.0):** Docker build `docker build --tag renderer:1.0 ./container` (a `Dockerfile_with_OPL` variant clones the OPL into the image). It runs on port 3000 with the OPL bind-mounted at `/usr/app/webwork-open-problem-library`. The API is a POST to `localhost:3000/render-api` with `problemSource` (raw or base64 PG), `sourceFilePath` (relative to Library/, Contrib/ or private/) or `problemSourceURL`, plus `problemSeed`. Options include `outputFormat` ∈ {default, static, PTX, raw}, `_format` ∈ {html, json}, `includeTags`, `showSolutions`, `showHints`, `isInstructor` — [openwebwork/renderer README](https://github.com/openwebwork/renderer)
- In renderer code (`lib/WeBWorK/FormatRenderedProblem.pm`), the JSON response includes `answers => $rh_result->{answers}` only when `isInstructor` is true, `tags`/`raw_metadata_text` when `includeTags` is set, plus `renderedHTML`, `flags` and `problem_result`. The `raw` format returns the whole `rh_result` hash as JSON "with everything that a client-side application could use" (read from clone; renderer main last commit 2025-06-18) — [renderer](https://github.com/openwebwork/renderer)
- PG answer hashes carry `correct_ans` and `correct_ans_latex_string` (`lib/AnswerHash.pm`, `lib/Value/AnswerChecker.pm`; PG main last commit 2026-10-27) — [openwebwork/pg](https://github.com/openwebwork/pg)
- 50,155 of the 70,165 OPL+Contrib problems call `random(`, `list_random` or `NchooseK`, so they are randomized. 17,602 are tagged `MO(1)` (MathObjects) and 4,868 `Static(1)` (counted from clone).
- **OpenStax CNXML:** each bundle has `collections/*.collection.xml` (book order, `<col:module document="m…">`), `modules/m*/index.cnxml`, and `media/` (repo layout) — [osbooks-calculus-bundle](https://github.com/openstax/osbooks-calculus-bundle). Exercises are `<exercise><problem>…</problem><solution>…</solution><commentary type="hint">…</commentary></exercise>` with MathML math (`m:` namespace). Each exercise's type is given by the enclosing `<section class="…">`: section-exercises, review-exercises, practice-test (algebra); review-problems, review-additional-problems, review-challenge, review-conceptual-questions (physics); exercises (chemistry); practice, free-response, bring-together-homework (statistics). Inline exercises sit in `<note class="checkpoint|try|check-understanding">` or `<example>` (inspected in clones). The calculus modules directory is 20 MB.
- **CLP PreTeXt:** `pretext/problems/prob_s1.2.xml` and similar contain `<exercises><exercisegroup><title><conceptual/></title>…<exercise><statement>…</statement><hint>…</hint><answer>…</answer><solution>…</solution></exercise>`. LaTeX uses `\begin{question}` or `\begin{Mquestion}` (representative set) with `hint`/`answer`/`solution` environments in `latex/problembook/problems/prob_s*.tex`, and figures are TikZ (inspected in clone) — [CLP1](https://github.com/arechnitzer/CLP1)
- **APEX PreTeXt:** exercises in `ptx/`, of which 2,582 are `<webwork>` elements (embedded PG) — [APEXCalculusPTX](https://github.com/APEXCalculus/APEXCalculusPTX). Building uses the PreTeXt CLI and a LaTeX distribution with Asymptote — [README](https://github.com/APEXCalculus/APEXCalculusPTX)
- **Hefferon:** LaTeX in `src/<chapter>/*.tex`, with `\begin{answer}` immediately after each exercise and some exercises flagged `\recommended`. `jhanswer.tex` builds the answer book (inspected in clone) — [GitLab](https://gitlab.com/jim.hefferon/linear-algebra)
- **ULA:** PreTeXt in `src/exercises/exercises<ch>-<sec>.xml` — [davidaustinm/ula](https://github.com/davidaustinm/ula)
- **OpenIntro:** chapters are in `ch_*/TeX/*.tex` with `\eoce{}`; solutions are in `extraTeX/eoceSolutions/eoceSolutions.tex` as sequential `\eocesol{}` keyed by comments (`% 1`, `% 3`, …). Figures are in `ch_*/figures/eoce/` with R code — [openintro-statistics](https://github.com/openintrostat/openintro-statistics)
- **Exercism:** `exercises/practice/<slug>/` holds the stub `.cpp/.h`, `<slug>_test.cpp`, `.meta/example.cpp`, `.meta/tests.toml` and `.meta/config.json` (from clone) — [exercism/cpp](https://github.com/exercism/cpp)

### Inferences
- Cheapest pipeline per source:
  1. **OpenStax:** `git clone --depth 1` each bundle, then parse with Python lxml in collection order and keep `<exercise>` in the relevant section classes. Keep MathML and render it with MathJax (it reads MathML natively), or convert it to LaTeX. Copy the referenced `media/` images. This takes minutes and needs no rendering.
  2. **CLP:** parse the PreTeXt problem XML, which is already split into statement, hint, answer and solution. Precompile TikZ figures once (PreTeXt CLI can generate SVG), or take figures from the published HTML build.
  3. **OPL:** run renderer Docker locally. For each chosen `.pg`, POST N seeds (for example 5–20) with `isInstructor=1&_format=json&includeTags=1&showSolutions=1&showHints=1&outputFormat=static`. Store `renderedHTML` (or `outputFormat=PTX` for structured XML), `answers.*.correct_ans` and `correct_ans_latex_string`, and the tags. The offline app then ships frozen instances and does its own answer checking (numeric tolerance or CAS equivalence). That avoids embedding Perl/PG in the desktop app. Exclude Pending/ and deduplicate OPL/ against Contrib/ copies with a hash of the normalized PG source.
  4. **APEX:** either run its `<webwork>` blocks through the same renderer (the PG is inline) or use PreTeXt's WeBWorK extraction to get static versions with answers. This last option is from general PreTeXt knowledge and was not tested here.
  5. **Hefferon, OpenIntro:** a regex or TeX parser over the LaTeX environments. For OpenIntro, align solution numbers to exercise numbers (odd only).
  6. **Exercism:** copy as-is, then compile tests locally (CMake plus the bundled test framework) for auto-grading C++ answers.
  7. **MIT OCW, Japanese exams:** PDF to math OCR (a Mathpix/Nougat-style tool), then manual cleanup. These cost the most per problem and are best saved for small, high-value sets (exams).

### Gaps
- The renderer's `PTX` output and the answer JSON structure were not tested end to end (Docker was not run). A small pilot (100 files × 3 seeds) should check that answers come back for older non-MathObjects problems.
- How PG problems that draw graphs at runtime (dynamic images) come out in static output was not checked.
- The CLP PreTeXt build's figure assets were not inspected.

## 6. Skill and topic metadata for tagging

### Takeaway
The OPL has the richest ready-made taxonomy: a three-level Subject > Chapter > Section tree plus per-file Level, keywords and textbook-section cross-references. OpenStax gives chapter/section structure and exercise-type classes. CLP adds Conceptual/Procedural/Application groups and a curated "representative" core.

### Cited Findings
- OPL `OpenProblemLibrary/Taxonomy2` is a tab-indented three-level tree with 1,787 lines and 1,507 leaf sections. Its 31 top-level subjects include Calculus - single variable, Calculus - multivariable, Algebra, Trigonometry, Precalculus, Differential equations, Linear algebra, Probability and Statistics, plus engineering subjects (Statics, Dynamics, Thermodynamics, Electric circuits, etc.). Example leaves under Limits and continuity: "Evaluating limits - factoring", "Squeeze theorem", "Continuity - intermediate value theorem" (read from clone) — [OPL repo](https://github.com/openwebwork/webwork-open-problem-library)
- `OpenProblemLibrary/Textbooks` (3,018 lines) maps textbook editions and sections. Per-file headers use `## DBsubject(...)`, `## DBchapter(...)`, `## DBsection(...)`, `## Level(n)`, `## KEYWORDS(...)`, `## Author`, `## Institution`, `## MO(1)`, `## TitleText1/AuthorText1/EditionText1/Section1/Problem1` (from clone). The NPL wiki says searches can be narrowed by "Bloom's taxonomy-type levels" and by textbook section — [NPL wiki](https://webwork.maa.org/wiki/NPL)
- Level tags appear in about 29.8k files: Level 1: 1,171; 2: 12,901; 3: 10,131; 4: 3,244; 5: 2,110; 6: 220. 31,383 files carry textbook tags (counted from clone).
- Large OPL chapter counts (OPL+Contrib): Calc single variable: Differentiation 2,372, Applications of differentiation 1,982, Techniques of integration 1,520, Integrals 1,380, Limits and continuity 1,126, Applications of integration 1,108, Infinite sequences and series 1,103. Linear algebra: Euclidean spaces 516, Matrices 462, Systems 412, Linear transformations 308, Abstract vector spaces 212, Eigenvalues 163, Inner products 157. Statistics: Hypothesis tests 347, Descriptive 302, Confidence intervals 211, Simple linear regression 169. Trig: Trigonometric functions 597, Analytic trigonometry 468, Triangle trigonometry 290 (counted from clone).
- Renderer `includeTags` returns these tags in JSON — [renderer](https://github.com/openwebwork/renderer)
- CLP groups each section's problems into Conceptual / Procedural / Application, marks a "representative question set" (286 `Mquestion` in CLP-1) and stars UBC exam problems — [CLP1 problembook](https://github.com/arechnitzer/CLP1)
- OpenStax collection XML gives the chapter and module order. Section classes give exercise type, and physics separates conceptual, problems, additional and challenge — Q5 sources.

### Inferences
- Use OPL Taxonomy2 leaves as the master skill list for math courses. Map OpenStax and CLP sections onto it once, by hand or semi-automatically, using section titles. OPL Level and OpenStax/CLP exercise types (checkpoint, section exercise, review, challenge, representative) make reasonable initial difficulty priors for scheduling.
- About 1,000 OPL files have no DBsubject and some use nonstandard names ("Calculus", "Linear Algebra" vs "Linear algebra"), so normalization is needed.

### Gaps
- No machine-readable skill taxonomy was found for physics or chemistry beyond OPL's sparse physics subjects and OpenStax chapter structure.

## 7. Physics and chemistry: units, significant figures, numeric answers

### Takeaway
OpenStax physics and chemistry answers are free text with units and implied significant figures, so turning them into auto-gradable numeric keys needs parsing. The OPL/PG ecosystem has proper unit and significant-figure answer checkers but few calculus-level physics problems and no chemistry. The practical route is to grade OpenStax physics/chem as numeric-with-unit plus a tolerance derived from the given sig figs, and to use OPL BrockPhysics for randomized drill.

### Cited Findings
- OpenStax University Physics solutions are inline text with MathML, e.g. "Sum of displacements = −6.4 km i + 9.4 km j" and "v_avg = 4.0 i + 2.0 k m/s". Units and sig figs are embedded in the answer string, with no separate numeric field (sampled from clone) — [osbooks-university-physics-bundle](https://github.com/openstax/osbooks-university-physics-bundle)
- OpenStax Chemistry 2e solutions include conceptual prose answers (e.g. "(a) law … (b) theory … (c) hypothesis") as well as numeric ones (sampled from clone) — [osbooks-chemistry-bundle](https://github.com/openstax/osbooks-chemistry-bundle)
- OPL BrockPhysics example: randomized values (`$length = random(175,225,5)`), answer checked with `num_cmp("$E")`, and the unit printed after the blank (`\{ans_rule(40)\} m`), i.e. units are not part of the graded answer (read from clone). 2,375 BrockPhysics files use `num_cmp` — [OPL repo](https://github.com/openwebwork/webwork-open-problem-library)
- PG provides `parserNumberWithUnits.pl`, `parserFormulaWithUnits.pl`, `contextUnits.pl`, `contextSignificantFigures.pl` and `contextReaction.pl` (chemical reactions) — [openwebwork/pg macros](https://github.com/openwebwork/pg). 1,311 OPL/Contrib files use NumberWithUnits, and 386 mention significant figures (counted from clone).

### Inferences
- For OpenStax physics/chem, parse each solution into (value, unit) pairs with a units library (e.g. Python `pint`). Set the grading tolerance from the sig figs of the given data (e.g. ±0.5 in the last reported digit, or a 1–2% relative tolerance). Mark multi-part and conceptual items as self-graded.
- PG's contextUnits and contextReaction could be used to author your own randomized chemistry items (stoichiometry, balancing) if the OpenStax chem bank is too small. Items you write yourself carry no third-party license.

### Gaps
- No open, auto-gradable general chemistry bank (structured numeric answers) was found. LibreTexts chemistry homework pages were not checked for licensing, because licensing is set page by page.
- The default numeric tolerance of PG's `num_cmp` and of OpenStax's own answer conventions was not verified.
