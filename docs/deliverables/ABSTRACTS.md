# Required Abstracts

Two abstracts are required by the SULI Program Student Obligations and are **not**
listed in `README.md`. Both are drafted below. Word counts verified.

---

## 1. Presentation abstract — 150-word limit

*Required prior to the oral presentation, per SULI Obligations §1.*

> Regional grid operators must forecast electricity demand a day ahead, and those
> forecasts are least reliable during the extreme weather that most threatens
> reliability. This project tested whether Adaptive Conditional Neural Processes,
> a method reported to improve extreme-load forecasting on two other US grids,
> reproduces that advantage on ERCOT data across seventeen extreme cold events
> from 2002 to 2026. The statistical analysis was pre-registered before any
> confirmatory run. Two results follow. The method did outperform its baseline on
> the pre-registered metric, though the effect sits near the limit this design can
> resolve and appears only in the committed configuration. More consequentially,
> both models are severely overconfident during extreme events: a nominal ninety
> percent prediction interval contains the observed load ninety-six percent of the
> time on normal days but only sixty-three percent during extreme cold, and it
> degrades further as events worsen.

**Word count: 149**

---

## 2. General-audience abstract — 300-word limit

*Required per SULI Obligations §3, at non-expert (Scientific American) level.
Due prior to end of appointment.*

> Electricity is almost impossible to store at the scale a country needs, so the
> people who run the power grid have to match supply to demand every second of
> every day. That means guessing tomorrow's demand today. Guess too low and there
> may not be enough power when people turn on their heat; guess too high and
> everyone pays for generators that sat idle. Operators can buy insurance against
> a bad guess by starting up generators early, but that insurance costs money, so
> the decision depends on how much they trust the forecast.
>
> Extreme cold makes this harder, and Texas learned the cost in February 2021,
> when forecasts fell short and the grid cut power to homes that were paying for
> it. The difficulty is fundamental: extreme events are rare. Twenty-four years of
> Texas grid data contain only seventeen usable extreme cold events, so a computer
> model has very few examples of exactly the situations that matter most.
>
> I tested a recently published forecasting method designed for this problem. It
> works by predicting tomorrow through comparison with similar days in the past,
> and it had been shown to help on two other regional grids. I asked whether it
> also helps in Texas, and I wrote down in advance what would count as success so
> that I could not talk myself into a favourable answer afterwards.
>
> It did help, modestly, though the improvement is close to the smallest my study
> could reliably detect. The more important discovery was different. Both models
> are badly overconfident exactly when the grid is under stress. A range the model
> claims will contain the real demand nine times out of ten does so about six
> times out of ten during extreme cold — and it gives no warning that it has
> become unreliable.

**Word count: 297**

---

## Still required and not produced

**One-page peer review** of another SULI intern's talk or poster (SULI Obligations
§2). This requires an assigned presentation to review and cannot be drafted from
the project repository.
