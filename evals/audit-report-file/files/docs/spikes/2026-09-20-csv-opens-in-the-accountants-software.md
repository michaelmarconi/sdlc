---
# Change status only through the sdlc plugin's skills, which check each change; a change made by hand is not checked.
type: Spike
status: 💡 Confirmed
---

# A plain CSV file opens in the accountant's software

## Hypothesis

A CSV file with a header row opens in the accountant's software without changes.

## Finding

Confirmed: a CSV file with a header row opens in the accountant's software without changes. In run 1 it opened with every column in place.

## Next steps

- Spec: Nothing
- ADR: Nothing

## How we'll know

The sample file opens with every column in place.

## Out of scope

None.

## How the test works

1. The accountant opens a sample file.

Opening a file shows the same thing every time, so one run is enough.

## Risks and safeguards

None.

## Results

| Run | Date | Outcome | Note |
|---|---|---|---|
| 1 | 2026-09-20 | Confirmed | Every column in place. |

Run 1 counts.

## Surprises

None.

## Open questions

- None.

## Experiment

The run is the accountant's observation, recorded through the run script.

- Runs: 1
- Stop early if: None.
- Starts from commit: None.
- Inputs: None.
- Secrets: None.
- Command: None.

## Code

None.

## Runs

### Run 1

2026-09-20 10:00 UTC, observation

```
It opened with every column in place.
```
