# Weekly Retail Intelligence Report
**Period:** 2025-03-10 09:00:32 – 2025-03-16 21:53:00
**Generated:** 2026-05-19T10:41:33.525804
**Prompt version:** v3_grounded

---

## Summary

| Metric | Value |
|---|---|
| Total journeys | 85347 |
| Avg journey duration | 83.6s |
| Median journey duration | 72.0s |
| Avg zones per journey | 2.2 |
| Completion rate | 1.0 |

---

## Traffic

**Peak hours:** 

### Journeys per Day

| Day | Journeys |
|---|---|
| 2025-03-10 | 11229 |
| 2025-03-11 | 9559 |
| 2025-03-12 | 12028 |
| 2025-03-13 | 12388 |
| 2025-03-14 | 11361 |
| 2025-03-15 | 15118 |
| 2025-03-16 | 13664 |


---

## Zones

### Top Zones by Visits

| Zone | Visits |
|---|---|
| Z_C1 | 33267 |
| Z_C2 | 38933 |
| Z_C3 | 22075 |
| Z_CK | 10895 |
| Z_E1 | 11489 |
| Z_E2 | 11095 |
| Z_N1 | 4804 |
| Z_N10 | 6629 |
| Z_N2 | 4494 |
| Z_N3 | 4969 |
| Z_N4 | 4156 |
| Z_N5 | 6735 |
| Z_N6 | 5310 |
| Z_N7 | 4597 |
| Z_N8 | 5888 |
| Z_N9 | 5620 |
| Z_S1 | 2875 |
| Z_S2 | 1601 |
| Z_S3 | 3941 |
| Z_S4 | 2921 |
| Z_S5 | 4075 |
| Z_S6 | 2406 |
| Z_S7 | 2032 |


---

## Demographics

| Gender | Count | Share |
|---|---|---|
| F | 41668 | 48.8% |
| M | 43679 | 51.2% |


| Age Range | Count | Share |
|---|---|---|
| adult | 26570 | 31.1% |
| child | 4867 | 5.7% |
| middle_aged | 23143 | 27.1% |
| senior | 8477 | 9.9% |
| teenager | 6326 | 7.4% |
| young_adult | 15964 | 18.7% |


---

## Key Findings


### Average duration of customer journeys across all days

avg_duration_s > 90

*Confidence: high | Supporting metrics: `demographics.avg_duration_s` = N/A, `journey_patterns.avg_zones_per_journey` = 2.2*


### Most visited zones on a given day

total_zone_visits / total_journeys > 0.5

*Confidence: medium | Supporting metrics: `zones.total_zone_visits` = 200807, `journey_patterns.total_journeys` = N/A*


### Average duration of customer journeys by age range

avg_duration_s > 80 for adults, < 90 for children

*Confidence: low | Supporting metrics: `demographics.avg_duration_s` = N/A, `journey_patterns.avg_zones_per_journey` = 2.2*



---

## Recommendations


### Optimize store layout to reduce single-zone journeys

single_zone_journeys < 50% of total journeys

*Supporting metrics: `journey_patterns.single_zone_journeys`, `zones.ranked_by_dwell`*



---

## Anomalies


- **High number of force-closed journeys on day 10**
  Possible explanations: inadequate staffing, poor customer service


---

## Data Quality

| Signal | Value |
|---|---|
| Avg stitch confidence | 1.0 |
| Low-confidence rate | 0.0 |
| Force-closed rate | 0.0 |
| Completion rate | 1.0 |

---

## Caveats


- The 'force_closed_journeys' metric is only available for days with a peak hour of 10.

- The 'total_zone_visits' and 'total_journeys' metrics are not correlated.

