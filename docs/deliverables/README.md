```markdown
# Internship Deliverables — Track A

## Deadline
2026-07-30, 2:00 PM EDT

## What I need to hand in
1. Technical report format: PDF from LaTeX 
2. Presentation — format: PowerPoint 


## Audience
- **Report**: Read by 1. The internship director 2. Mentor (Technical Level: High) 3. Federal Team Supervisor (Technical Level: High)
- **Presentation**: Audience: consists of scientists who are not very versed with my topic. how long do I present: 10 minutes Q&A: 5 minutes for Q & A 

## Requirements I already know
- Page/slide limit: "see GUIDELINES_technical_report.pdf §X"
- Required sections: "see GUIDELINES_technical_report.pdf §X"
- Citation style: "see GUIDELINES_technical_report.pdf §X"
- Template required: "see GUIDELINES_technical_report.pdf §X"
- Anything else mandatory: "see GUIDELINES_technical_report.pdf §X"

## State of paper_outline.tex
- **Written already**: Nothing written yet.
- **Outline only, needs filling**: 1. Introduction 2. Methodology 3. Results and Discussion 4. Conclusions 5. Acknowledgements 6. References
- **Not started**: None of the sections
- Figures currently in the file: Unsure

## Things I'm unsure about — ask me, don't guess
- whether I should name Hu et al. as a replication target or frame it as inspired-by

## Environment
- LaTeX compiles locally: not tested yet
- If no: I'll compile on Overleaf 

## Presentation brainstorm — NOT INSTRUCTIONS

> **Status: unfinalized brainstorming. Do not treat any of this as a specification, a required structure, or a decision I have made.**
> This is a narrative direction I'm considering for the presentation. I have not committed to it. The authoritative requirements are in
> `GUIDELINES_presentation.pdf` — where this brainstorm and the guidelines conflict, the guidelines win, every time. Use it as: context on the framing I find compelling, and the tone I'm aiming for. Do NOT use it as: a slide-by-slide outline, a timing plan, or a source of claims to put in the deliverable.
If you think something here is a good idea, propose it to me — don't just build it.

## A structure for ten minutes

**0:00–2:00 — The problem, made physical.** Electricity is nearly impossible to store at scale, so supply and demand must match continuously, second by second. Someone has to guess tomorrow's demand *today*. Get it wrong low and there isn't enough power. Get it wrong high and everyone pays for generators that idled. That's the whole job, and it's harder than it sounds because demand depends on weather, and weather is getting less predictable.

**2:00–4:00 — The consequences, made human.** February 2021: forecasts missed, reserves fell short, and ERCOT shed firm load — the industry term for cutting power to homes that were paying for it. Hundreds died, mostly from cold. Billions in damages. Then the part your audience won't expect: **operators can hedge by committing generators early**, before the market says it's economical. That's insurance, and it costs money that lands on customers' bills. So every forecast is a bet with two ways to lose: too confident and people freeze, too cautious and everyone overpays. That tension is your whole summer in one sentence.

**4:00–6:00 — Why this is genuinely hard.** Extreme events are rare by definition. You have twenty-four years of ERCOT data and seventeen usable extreme cold events. A model that learns beautifully from ten thousand ordinary days has almost nothing to learn from for the days that actually matter. And the ordinary days actively mislead — the relationship between weather and demand *changes* in extremes. This is where a lay audience gets genuinely interested, because the difficulty is intuitive once stated.

**6:00–8:30 — What you did.** Now the method has a reason to exist. Neural processes let a model make a prediction by referring to past examples rather than only to learned parameters — and AdaCNP's idea is that when predicting a freeze, it should weight past *freezes* more heavily than past Tuesdays. You found this in the literature, it was demonstrated on two other grids, and you asked whether it holds on Texas.

**8:30–10:00 — What you found, and what it cost you to find out honestly.** Three things, in this order:

- The replication didn't work at first, and you found out why: the model couldn't see temperature, while the events themselves are *defined* by temperature. You were asking it to find cold days without showing it cold. Fixing that changed the answer.
- Both models are badly overconfident during extreme events — roughly 36% coverage where 90% was intended. **For this audience, lead on this.** A wrong forecast is survivable. A forecast that is confidently wrong is what makes an operator skip the expensive hedge.
- You measured what your own experiment could and couldn't detect, and it couldn't resolve an effect the size the original paper reported. So you're not claiming a verdict.


- **Pathos** — February 2021, and the fact that you worked with those exact hours. Don't dramatize; just be specific. Specificity does the work.
- **Logos** — the two-sided cost structure of a forecast error, and the seventeen-events constraint. Both are simple and both land.
- **Ethos** — you built leakage controls, a censoring treatment, and a pre-registered analysis committed before you saw results. You don't need to explain pre-registration in depth. "I wrote down what would count as success before I looked at the answer" is one sentence and it is the most trustworthy thing you can say.

## One practical caution

Don't explain neural processes architecturally. One sentence — "it predicts by referring to similar past days" — is enough, and more will lose the room.

```

