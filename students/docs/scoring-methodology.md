# Scoring Methodology

## Student Success Score

The prototype calculates a transparent Student Success Score on a 0–100 scale using the formula below:

Student Success Score = 0.30 × Academic + 0.20 × Attendance + 0.15 × LMS + 0.15 × Skills + 0.15 × Placement + 0.05 × Engagement

Each component is normalized to a 0–100 scale based on the best available data. When essential inputs are absent, the system reports a data completeness value and the score is treated as provisional rather than silently penalizing the student.

## Risk logic

Academic risk is triggered by findings such as low attendance, weak internal assessment performance, low CGPA, significant backlog counts, or repeated assignment non-completion. Placement risk is computed separately from aptitude, coding, mock interview, resume readiness, and communication indicators.

## Why the system is explainable

The platform displays:

- the contributing indicators
- their values
- the threshold comparisons
- positive drivers
- factors needing attention
- missing data impact
- a plain-language explanation based on the computed data

This keeps the tool aligned with educational decision support instead of opaque scoring.
