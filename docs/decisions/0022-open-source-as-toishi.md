# ADR-0022: Open source on GitHub as Toishi

- Status: Accepted
- Date: 2026-11-02
- Amends:
  - AGENTS.md: the "No GitHub" stack line, the data path in rule 4, and the environment variables;
  - spec DEV-2 and DEV-3, the "Source hosting" open decision and the "Where the code lives" row;
  - ADR-0001's artifact names;
  - ADR-0004's data folder.

## Context

The project was built as a private app with no GitHub. On 2026-11-02 the owner decided:
- it should be open source on GitHub;
- it needs a memorable name;
- the code should be under GPL-3.0;
- none of the owner's personal details should be in the project, and the first public commit must be clean.

## Decision

- **Name: Toishi** (砥石, a whetstone). It replaces "Mastery Engine" everywhere the app is named:
  - window title, sidebar and messages;
  - `Toishi.app` and `packaging/Toishi.spec`;
  - launchd labels `com.toishi.runner` and `com.toishi.backup`;
  - environment variables `TOISHI_*`;
  - the project and web package names.
- **Internal identifiers stay.** These are formats existing files depend on, not the app's name:
  - the card and skills format lines (`mastery-cards 1`, `mastery-skills 1`);
  - the `.mepack` extension;
  - the SQLite application ids;
  - the Anki note type name.

  Renaming any of them needs its own decision with a read path for the old value.
- **Data folder: `~/Library/Application Support/com.toishi.app/`.** On first use, an existing `com.masteryengine.app` folder is moved there (`core.paths`, one atomic rename), so no progress is lost.
- **License: GPL-3.0-or-later** for the code (`LICENSE`).
  - Every runtime dependency is under a permissive license compatible with it.
  - Course packs keep their own licenses, recorded per pack and per card (Calculus I: CC BY-NC-SA 4.0).
  - Before the first binary release, the license of every bundled dependency is checked again. The 2026-11-01 review found `fsrs-rs-python` published without a license, and a bundled copy needs one.
- **Hosting: a public GitHub repository**, with downloads on its Releases page.
  - Checks still run from `scripts/` on the Mac, and core tests on Linux. GitHub Actions would be free for a public repository, but adopting it is a separate decision.
  - The nightly bundle backup stays.
- **A fresh history.** The public repository starts from one commit of the cleaned tree.
  - The earlier history held the owner's personal details. It is not published and was replaced everywhere it lived: the working copies, the Mac's repository and the sync bundles.

## Consequences

- AGENTS.md, the README and the spec are updated in the same change.
- The Mac's runner helper keeps working under its old label until it is reinstalled. `scripts/install-runner.sh` now removes the old label when it installs or uninstalls.
- Personal details never go into the repository: no names, schools, courses taken, exam dates, schedules or machine paths. Examples in docs describe a typical student or course.
