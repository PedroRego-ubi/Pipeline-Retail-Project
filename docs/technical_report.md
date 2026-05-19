# Technical Report

## 1. Problem Statement

## 2. Architecture

### Pipeline Diagram

```
events.csv → stitcher.py → journeys.csv
                                 ↓
                         analytics.py
                                 ↓
                          metrics.json ←── ONLY data the LLM sees
                                 ↓
                          insights.py  (Ollama: llama3.1:8b)
                                 ↓
                          insights.json
                                 ↓
                          report.py    (template + LLM-narrated)
                                 ↓
                         weekly_report.md

evaluate.py → reads journeys.csv + metrics.json + insights.json
            → produces quality_report.json
```

## 3. Stitching Methodology

### Threshold Justification

## 4. Metrics Design

## 5. Anti-Hallucination Strategy

## 6. Evaluation Methodology

## 7. Results

## 8. Limitations

## 9. Reproducibility Instructions
