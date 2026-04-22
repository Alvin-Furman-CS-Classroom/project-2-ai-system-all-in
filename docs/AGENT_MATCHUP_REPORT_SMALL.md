# Full-Game Agent Effectiveness Report

## Setup
- Agents: `m2, m3, m4, rl_optimal, rl_coverage, random`
- Hands per non-LLM matchup: `1000`
- Hands per LLM matchup (includes `m4`): `10`
- Starting stacks: `100 BB` each (`2000` chips)
- Blinds: `SB=10`, `BB=20`
- Seed: `1337`

## Matchup Results

### m2 vs m2 (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -2.100 | [-81.037, 76.837] | 49.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.030 | 500 | 500 | 4675 |
| m2 | 152.100 | [73.163, 231.037] | 51.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.030 | 500 | 500 | 4659 |

### m2 vs m3 (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -39.200 | [-202.121, 123.721] | 48.10% | 0.00% | 100.00% | 0.00% | 0.00% | 0.058 | 500 | 500 | 5656 |
| m3 | 189.200 | [26.279, 352.121] | 51.90% | 0.00% | 100.00% | 0.00% | 0.00% | 29.147 | 500 | 500 | 5244 |

### m2 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 560.000 | [-443.436, 1563.436] | 80.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.278 | 5 | 5 | 42 |
| m4 | -410.000 | [-1413.436, 593.436] | 20.00% | 0.00% | 100.00% | 0.00% | 53.19% | 24443.611 | 5 | 5 | 47 |

### m2 vs rl_optimal (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 76.100 | [-11.431, 163.631] | 76.80% | 0.00% | 100.00% | 0.00% | 0.00% | 0.035 | 500 | 500 | 2688 |
| rl_optimal | 73.900 | [-13.631, 161.431] | 23.20% | 0.00% | 100.00% | 0.00% | 0.00% | 0.061 | 500 | 500 | 3161 |

### m2 vs rl_coverage (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 269.900 | [184.194, 355.606] | 82.30% | 0.00% | 100.00% | 0.00% | 0.00% | 0.034 | 500 | 500 | 2527 |
| rl_coverage | -119.900 | [-205.606, -34.194] | 17.70% | 0.00% | 100.00% | 0.00% | 0.00% | 0.058 | 500 | 500 | 3005 |

### m2 vs random (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 572.050 | [471.401, 672.699] | 77.70% | 0.00% | 100.00% | 0.00% | 0.00% | 0.032 | 500 | 500 | 3909 |
| random | -422.050 | [-522.699, -321.401] | 22.30% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 500 | 500 | 3812 |

### m3 vs m3 (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 14.950 | [-176.274, 206.174] | 49.50% | 0.00% | 100.00% | 0.00% | 0.00% | 37.159 | 500 | 500 | 6079 |
| m3 | 135.050 | [-56.174, 326.274] | 50.50% | 0.00% | 100.00% | 0.00% | 0.00% | 37.386 | 500 | 500 | 6030 |

### m3 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 1360.000 | [714.918, 2005.082] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 42.241 | 5 | 5 | 39 |
| m4 | -1210.000 | [-1855.082, -564.918] | 0.00% | 0.00% | 100.00% | 0.00% | 59.52% | 25423.151 | 5 | 5 | 42 |

### m3 vs rl_optimal (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 116.800 | [48.528, 185.072] | 89.50% | 0.00% | 100.00% | 0.00% | 0.00% | 24.417 | 500 | 500 | 1484 |
| rl_optimal | 33.200 | [-35.072, 101.472] | 10.50% | 0.00% | 100.00% | 0.00% | 0.00% | 0.069 | 500 | 500 | 1960 |

### m3 vs rl_coverage (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 133.850 | [65.974, 201.726] | 90.70% | 0.00% | 100.00% | 0.00% | 0.00% | 22.177 | 500 | 500 | 1371 |
| rl_coverage | 16.150 | [-51.726, 84.026] | 9.30% | 0.00% | 100.00% | 0.00% | 0.00% | 0.071 | 500 | 500 | 1966 |

### m3 vs random (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 757.650 | [654.535, 860.765] | 82.90% | 0.00% | 100.00% | 0.00% | 0.00% | 32.267 | 500 | 500 | 3694 |
| random | -607.650 | [-710.765, -504.535] | 17.10% | 0.00% | 100.00% | 0.00% | 0.00% | 0.003 | 500 | 500 | 3856 |

### m4 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 375.000 | [-109.360, 859.360] | 50.00% | 0.00% | 100.00% | 0.00% | 95.24% | 29281.796 | 5 | 5 | 21 |
| m4 | -225.000 | [-709.360, 259.360] | 50.00% | 0.00% | 100.00% | 0.00% | 95.24% | 29183.467 | 5 | 5 | 21 |

### m4 vs rl_optimal (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 65.000 | [-72.083, 202.083] | 80.00% | 0.00% | 100.00% | 0.00% | 100.00% | 30003.723 | 5 | 5 | 7 |
| rl_optimal | 85.000 | [-52.083, 222.083] | 20.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.112 | 5 | 5 | 10 |

### m4 vs rl_coverage (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 140.000 | [-21.229, 301.229] | 80.00% | 0.00% | 100.00% | 0.00% | 100.00% | 30003.446 | 5 | 5 | 9 |
| rl_coverage | 10.000 | [-151.229, 171.229] | 20.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.140 | 5 | 5 | 14 |

### m4 vs random (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 95.000 | [-338.483, 528.483] | 40.00% | 0.00% | 100.00% | 0.00% | 95.45% | 29988.969 | 5 | 5 | 22 |
| random | 55.000 | [-378.483, 488.483] | 60.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.010 | 5 | 5 | 21 |

### rl_optimal vs rl_optimal (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 78.350 | [51.513, 105.187] | 51.50% | 0.00% | 100.00% | 0.00% | 0.00% | 0.048 | 500 | 500 | 718 |
| rl_optimal | 71.650 | [44.813, 98.487] | 48.50% | 0.00% | 100.00% | 0.00% | 0.00% | 0.048 | 500 | 500 | 737 |

### rl_optimal vs rl_coverage (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 104.400 | [78.863, 129.937] | 54.50% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 500 | 500 | 641 |
| rl_coverage | 45.600 | [20.063, 71.137] | 45.50% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 500 | 500 | 700 |

### rl_optimal vs random (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 86.950 | [45.589, 128.311] | 20.70% | 0.00% | 100.00% | 0.00% | 0.00% | 0.035 | 500 | 500 | 1371 |
| random | 63.050 | [21.689, 104.411] | 79.30% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 500 | 500 | 1054 |

### rl_coverage vs rl_coverage (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | 75.950 | [68.892, 83.008] | 51.60% | 0.00% | 100.00% | 0.00% | 0.00% | 0.040 | 500 | 500 | 599 |
| rl_coverage | 74.050 | [66.992, 81.108] | 48.40% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 500 | 500 | 613 |

### rl_coverage vs random (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | 93.050 | [53.254, 132.846] | 16.60% | 0.00% | 100.00% | 0.00% | 0.00% | 0.035 | 500 | 500 | 1389 |
| random | 56.950 | [17.154, 96.746] | 83.40% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 500 | 500 | 930 |

### random vs random (`1000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | 47.700 | [-21.963, 117.363] | 49.20% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 500 | 500 | 2319 |
| random | 102.300 | [32.637, 171.963] | 50.80% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 500 | 500 | 2334 |

