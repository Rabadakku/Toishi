# Study mindset (owner direction, 2026-11-02)

**The owner's direction.** Instill a gaokao study mindset in everyone who uses the app, and provide plenty of good material against a culture of laziness and weakness. The core message is "if you don't suffer now, you'll suffer later". Drive students away from Instagram, TikTok, YouTube, gambling, porn, drugs, nicotine, alcohol and other super stimuli. Recommend the books and material that hardcore students are told to read.

**Owner, 2026-11-02 21:19: go hardcore.** The voice is an intense, gaokao-style work ethic: long study days are the goal, not the exception, and the app promotes them openly. The softer "high standards with respect" voice proposed earlier is replaced.

**Status.** Direction recorded. The design below is the coordinator's proposal. It will be built after the wave 2 merge, and claims and helplines are verified before anything ships.

## Principles

1. **The app practices what it preaches.** No streaks, badges, points, confetti, notifications or feeds. The only reward is getting better.
2. **The voice is hardcore about effort.**
   - Slogans and essays push long hours, sacrifice, cutting distractions, and "suffer now or suffer later".
   - The intensity is aimed at the work and the competition ("someone else is studying right now"), not at calling the student worthless. A student who quits the app in anger studies zero hours.
3. **Every warning comes with a next step.** Fear appeals work best when paired with a concrete way to act (Tannenbaum et al. 2015, meta-analysis). "If you don't suffer now, you'll suffer later" is always followed by today's plan.
4. **Make the future concrete.**
   - Imagining a specific future in detail (episodic future thinking) reduces the discounting of later rewards (Rung & Madden 2018, meta-analysis).
   - Mental contrasting with if-then plans improved students' study effort (Duckworth et al. 2011).
   - Both go into the study plan screen (LIB-12).
5. **Long days, full nights.** The plan never cuts into sleep.
   - China's Ministry of Education requires 8 hours of sleep for high school students (2021), and its "double reduction" policy (2021) cut homework loads. Even the system the app is modelled on protects sleep.
   - Sleep is when practice consolidates, so all-nighters cost more than they gain.
6. **Claims that hold up.** The case against super stimuli uses solid findings, such as media multitasking during study lowering learning (for example Sana, Weston & Cepeda 2013) and time displaced from study and sleep. Contested findings are labeled. Exaggeration gives a reader a reason to dismiss the whole message.
7. **Private by design.** The app never tracks what the student does outside it.
8. **Real addiction gets real help.** A help page lists helplines (localized; numbers verified before shipping).

## Slogans

Classical Chinese sayings, public domain, used in Chinese schools. Each is shown with its pinyin and an English line, one a day on Home.

- **宝剑锋从磨砺出，梅花香自苦寒来**: a sword's edge comes from the grinding; the plum blossom's fragrance comes from the bitter cold. *This is the app's motto.* 砥石 is the whetstone that does the grinding.
- **少壮不努力，老大徒伤悲**: work hard while you are young, or grieve in vain when you are old. ("If you don't suffer now, you'll suffer later.")
- **吃得苦中苦，方为人上人**: endure the bitterest hardship to rise above others.
- **业精于勤，荒于嬉**: mastery comes from diligence and is ruined by play (Han Yu). This is the line against super stimuli.
- **书山有路勤为径，学海无涯苦作舟**: diligence is the path up the mountain of books; hardship is the boat across the endless sea of learning.
- **天道酬勤**: heaven rewards diligence.
- **提高一分，干掉千人**: one more point beats a thousand people. A modern gaokao classroom banner.

## Hardcore mode: the mechanics

Long days only help if the hours go to the right work. The planner's limits (at most 3 growth problems per skill a day; more of the same skill the same day gives little) stay. Instead, the student's extra hours go to material that pays:

- **A daily hours target** the student sets, up to 12. Home shows today's minutes against it and a plain log of days and hours. It is a record, not a streak.
- **After the day's plan is done, the extra hours fill in this order:**
  1. **Go ahead of the course:** the pace factor rises beyond the current 1.5×, up to 3×, introducing sections before the class reaches them.
  2. **Harder targets:** tier 5 problems, and the target tier above the default.
  3. **Practice tests:** timed mixed sets at exam conditions.
  4. **Other courses:** the next pack.
  5. **The reading list.**
- **Exam countdown:** an entered exam shows the days left and the hours needed at the current pace, as the course page already does.
- **Bedtime is a hard stop.** The plan's last item ends before the student's bedtime, and the day's target never assumes less than 8 hours of sleep.

## What to build

- **First run, "why you're here":**
  - a short episodic-future exercise: the day the result arrives, the course or job it opens;
  - an obstacle and if-then plans, including one for the phone.
- **A Read section** of short original essays (about 600 words each, cited, graded like the design notes):
  - why practice should feel hard;
  - attention is the price you pay;
  - supernormal stimuli;
  - your future self;
  - sleep is part of studying;
  - how to quit something, and where to get help.
- **The reading list below**, each book with one line on why it is there.
- **Focus sessions:**
  - full screen with a pre-session checklist (phone in another room, notifications off);
  - setup help for macOS Screen Time and Focus modes. The app is offline and cannot block other apps, and it won't try.
- **A small flashcard deck on how learning works** (retrieval, spacing, interleaving, sleep), so students practice the ideas themselves.
- **A help page,** in the United States:
  - SAMHSA's National Helpline 1-800-662-4357 (substances);
  - 1-800-GAMBLER (gambling);
  - 1-800-QUIT-NOW (nicotine).

## Reading list (draft; check editions and descriptions before shipping)

**How to learn and get good**
- George Pólya, *How to Solve It* (1945). The classic on solving math problems.
- Richard Hamming, *The Art of Doing Science and Engineering: Learning to Learn* (1997), and his talk "You and Your Research" (1986, free online). Written for future engineers.
- Santiago Ramón y Cajal, *Advice for a Young Investigator* (1897). A Nobel laureate on why will and work beat talent.
- K. Anders Ericsson and Robert Pool, *Peak* (2016). Deliberate practice.
- Peter Brown, Henry Roediger and Mark McDaniel, *Make It Stick* (2014). The science behind the app's method: retrieval, spacing, interleaving.
- Barbara Oakley, *A Mind for Numbers* (2014). Learning math and science.
- Cal Newport, *How to Become a Straight-A Student* (2006).
- Josh Waitzkin, *The Art of Learning* (2007).
- Michael Spivak, *Calculus*. The hardest honest version of the course, for students who want it.

**Attention and super stimuli**
- Cal Newport, *Deep Work* (2016) and *Digital Minimalism* (2019).
- Anna Lembke, *Dopamine Nation* (2021). A psychiatrist on compulsive overconsumption.
- Deirdre Barrett, *Supernormal Stimuli* (2010). The concept itself.
- Adam Alter, *Irresistible* (2017). How apps are built to hook you.
- Johann Hari, *Stolen Focus* (2022).
- Jonathan Haidt, *The Anxious Generation* (2024). Read with its critics: the causal evidence is debated.

**Discipline and endurance**
- Marcus Aurelius, *Meditations*; Seneca, *Letters from a Stoic*.
- Viktor Frankl, *Man's Search for Meaning* (1946).
- Ryan Holiday, *Discipline Is Destiny* (2022).
- David Goggins, *Can't Hurt Me* (2018). "Suffer now" in its purest form.
- Angela Duckworth, *Grit* (2016). Read with the caveat that grit largely overlaps conscientiousness (Credé et al. 2017).

**Free**
- Richard Feynman, "Cargo Cult Science" (1974), and *The Feynman Lectures on Physics* (free online).
- Terence Tao, "Does one have to be a genius to do maths?".
- Paul Graham, "How to Do Great Work" (2023).

## References

- Credé, Tynan & Harms 2017, Much ado about grit: a meta-analytic synthesis of the grit literature (JPSP).
- Duckworth, Grant, Loew, Oettingen & Gollwitzer 2011, Self-regulation strategies improve self-discipline in adolescents (Educational Psychology).
- Rung & Madden 2018, Experimental reductions of delay discounting and impulsive choice: a systematic review and meta-analysis (JEP: General).
- Sana, Weston & Cepeda 2013, Laptop multitasking hinders classroom learning for both users and nearby peers (Computers & Education).
- Tannenbaum et al. 2015, Appealing to fear: a meta-analysis of fear appeal effectiveness and theories (Psychological Bulletin).
- Yeager et al. 2014, Breaking the cycle of mistrust: wise interventions to provide critical feedback across the racial divide (JEP: General).
