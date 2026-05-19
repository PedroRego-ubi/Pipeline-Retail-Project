# Prompt Comparison Study

Comparison of three prompt variants on three axes:
schema-compliance rate, hallucinated-number count, and qualitative usefulness.

## Prompts Compared

| Version | File | Strategy |
|---|---|---|
| v1 | `prompts/insights_v1_naive.txt` | Naive: "Summarize this retail data" |
| v2 | `prompts/insights_v2_structured.txt` | Adds JSON schema requirement and section headers |
| v3 | `prompts/insights_v3_grounded.txt` | Role + schema + grounding constraint + cite-the-metric |

## Results

### Schema Compliance (3 runs each)

| Version | Run 1 | Run 2 | Run 3 | Rate |
|---|---|---|---|---|
| v1 | | | | |
| v2 | | | | |
| v3 | | | | |

### Hallucinated Numbers

| Version | Numbers in output not in metrics.json |
|---|---|
| v1 | |
| v2 | |
| v3 | |

### Qualitative Assessment

#### v1 — Naive

#### v2 — Structured

#### v3 — Grounded (Production)

## Conclusion
