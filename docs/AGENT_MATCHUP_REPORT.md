# Full-Game Agent Effectiveness Report

## Setup
- Agents: `m2, m3, m4, rl_optimal, rl_coverage, random`
- Hands per non-LLM matchup: `10000`
- Hands per LLM matchup (includes `m4`): `50`
- Starting stacks: `100 BB` each (`2000` chips)
- Blinds: `SB=10`, `BB=20`
- Seed: `1337`

## Matchup Results

### m2 vs m3 (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -12.230 | [-64.826, 40.366] | 50.10% | 0.00% | 100.00% | 0.00% | 0.00% | 0.048 | 5000 | 5000 | 56328 |
| m3 | 162.230 | [109.634, 214.826] | 49.90% | 0.00% | 100.00% | 0.00% | 0.00% | 26.431 | 5000 | 5000 | 52510 |

### m2 vs m4 (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 483.000 | [75.808, 890.192] | 82.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.047 | 25 | 25 | 183 |
| m4 | -333.000 | [-740.192, 74.192] | 18.00% | 0.00% | 100.00% | 0.00% | 100.00% | 1.742 | 25 | 25 | 178 |

### m2 vs rl_optimal (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 124.170 | [96.634, 151.706] | 78.09% | 0.00% | 100.00% | 0.00% | 0.00% | 0.036 | 5000 | 5000 | 26869 |
| rl_optimal | 25.830 | [-1.706, 53.366] | 21.91% | 0.00% | 100.00% | 0.00% | 0.00% | 0.040 | 5000 | 5000 | 31589 |

### m2 vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 172.020 | [144.840, 199.200] | 80.93% | 0.00% | 100.00% | 0.00% | 0.00% | 0.037 | 5000 | 5000 | 25350 |
| rl_coverage | -22.020 | [-49.200, 5.160] | 19.07% | 0.00% | 100.00% | 0.00% | 0.00% | 0.041 | 5000 | 5000 | 30265 |

### m2 vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 531.085 | [499.231, 562.939] | 77.79% | 0.00% | 100.00% | 0.00% | 0.00% | 0.034 | 5000 | 5000 | 38506 |
| random | -381.085 | [-412.939, -349.231] | 22.21% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 37882 |

### m3 vs m4 (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 538.000 | [66.671, 1009.329] | 74.00% | 0.00% | 100.00% | 0.00% | 0.00% | 23.522 | 25 | 25 | 205 |
| m4 | -388.000 | [-859.329, 83.329] | 26.00% | 0.00% | 100.00% | 0.00% | 100.00% | 0.408 | 25 | 25 | 203 |

### m3 vs rl_optimal (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 95.530 | [73.718, 117.342] | 89.32% | 0.00% | 100.00% | 0.00% | 0.00% | 19.154 | 5000 | 5000 | 15354 |
| rl_optimal | 54.470 | [32.658, 76.282] | 10.68% | 0.00% | 100.00% | 0.00% | 0.00% | 0.043 | 5000 | 5000 | 19796 |

### m3 vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 114.545 | [93.718, 135.372] | 91.09% | 0.00% | 100.00% | 0.00% | 0.00% | 15.194 | 5000 | 5000 | 13073 |
| rl_coverage | 35.455 | [14.628, 56.282] | 8.91% | 0.00% | 100.00% | 0.00% | 0.00% | 0.042 | 5000 | 5000 | 19021 |

### m3 vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 698.025 | [665.279, 730.771] | 83.53% | 0.00% | 100.00% | 0.00% | 0.00% | 22.277 | 5000 | 5000 | 35804 |
| random | -548.025 | [-580.771, -515.279] | 16.47% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 37330 |

### m4 vs rl_optimal (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 97.000 | [-94.865, 288.865] | 82.00% | 0.00% | 100.00% | 0.00% | 100.00% | 0.332 | 25 | 25 | 55 |
| rl_optimal | 53.000 | [-138.865, 244.865] | 18.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 25 | 25 | 74 |

### m4 vs rl_coverage (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -110.000 | [-327.591, 107.591] | 74.00% | 0.00% | 100.00% | 0.00% | 100.00% | 0.314 | 25 | 25 | 54 |
| rl_coverage | 260.000 | [42.409, 477.591] | 26.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.041 | 25 | 25 | 73 |

### m4 vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -45.000 | [-331.125, 241.125] | 42.00% | 0.00% | 100.00% | 0.00% | 100.00% | 0.268 | 25 | 25 | 109 |
| random | 195.000 | [-91.125, 481.125] | 58.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 25 | 25 | 109 |

### rl_optimal vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 95.595 | [87.266, 103.924] | 54.95% | 0.00% | 100.00% | 0.00% | 0.00% | 0.036 | 5000 | 5000 | 6507 |
| rl_coverage | 54.405 | [46.076, 62.734] | 45.05% | 0.00% | 100.00% | 0.00% | 0.00% | 0.035 | 5000 | 5000 | 7110 |

### rl_optimal vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 83.030 | [70.411, 95.649] | 20.14% | 0.00% | 100.00% | 0.00% | 0.00% | 0.034 | 5000 | 5000 | 13583 |
| random | 66.970 | [54.351, 79.589] | 79.86% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 10313 |

### rl_coverage vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | 98.065 | [86.292, 109.838] | 18.87% | 0.00% | 100.00% | 0.00% | 0.00% | 0.034 | 5000 | 5000 | 13461 |
| random | 51.935 | [40.162, 63.708] | 81.13% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 9267 |

