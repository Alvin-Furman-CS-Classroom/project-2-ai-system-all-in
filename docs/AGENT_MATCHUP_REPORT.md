# Full-Game Agent Effectiveness Report

## Setup
- Agents: `m2, m3, m4, rl_optimal, rl_coverage, random`
- Hands per non-LLM matchup: `10000`
- Hands per LLM matchup (includes `m4`): `10`
- Starting stacks: `100 BB` each (`2000` chips)
- Blinds: `SB=10`, `BB=20`
- Seed: `1337`

## Matchup Results

### m2 vs m2 (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 4.055 | [-11.518, 19.628] | 49.25% | 1.32% | 100.00% | 0.00% | 0.00% | 0.041 | 5000 | 5000 | 22701 |
| m2 | -4.055 | [-19.628, 11.518] | 49.43% | 1.32% | 100.00% | 0.00% | 0.00% | 0.041 | 5000 | 5000 | 22643 |

### m2 vs m3 (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 118.065 | [80.498, 155.632] | 28.65% | 1.92% | 100.00% | 0.00% | 0.00% | 0.055 | 5000 | 5000 | 34145 |
| m3 | -118.065 | [-155.632, -80.498] | 69.43% | 1.92% | 100.00% | 0.00% | 0.00% | 22.010 | 5000 | 5000 | 30037 |

### m2 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 115.000 | [-416.985, 646.985] | 70.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.251 | 5 | 5 | 46 |
| m4 | -115.000 | [-646.985, 416.985] | 30.00% | 0.00% | 100.00% | 0.00% | 0.00% | 8945.548 | 5 | 5 | 51 |

### m2 vs rl_optimal (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 71.650 | [52.662, 90.638] | 59.08% | 0.62% | 100.00% | 0.00% | 0.00% | 0.050 | 5000 | 5000 | 14756 |
| rl_optimal | -71.650 | [-90.638, -52.662] | 40.30% | 0.62% | 100.00% | 0.00% | 0.00% | 0.043 | 5000 | 5000 | 17125 |

### m2 vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 128.145 | [106.003, 150.287] | 63.97% | 0.60% | 100.00% | 0.00% | 0.00% | 0.051 | 5000 | 5000 | 15515 |
| rl_coverage | -128.145 | [-150.287, -106.003] | 35.43% | 0.60% | 100.00% | 0.00% | 0.00% | 0.041 | 5000 | 5000 | 17857 |

### m2 vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 245.510 | [223.535, 267.485] | 41.57% | 0.58% | 100.00% | 0.00% | 0.00% | 0.045 | 5000 | 5000 | 22273 |
| random | -245.510 | [-267.485, -223.535] | 57.85% | 0.58% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 20359 |

### m3 vs m3 (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | -39.235 | [-98.704, 20.234] | 47.31% | 4.32% | 100.00% | 0.00% | 0.00% | 25.330 | 5000 | 5000 | 59983 |
| m3 | 39.235 | [-20.234, 98.704] | 48.37% | 4.32% | 100.00% | 0.00% | 0.00% | 25.325 | 5000 | 5000 | 60075 |

### m3 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 290.000 | [-435.435, 1015.435] | 70.00% | 0.00% | 100.00% | 0.00% | 0.00% | 68.207 | 5 | 5 | 35 |
| m4 | -290.000 | [-1015.435, 435.435] | 30.00% | 0.00% | 100.00% | 0.00% | 0.00% | 9563.536 | 5 | 5 | 50 |

### m3 vs rl_optimal (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 44.080 | [22.548, 65.612] | 89.39% | 0.57% | 100.00% | 0.00% | 0.00% | 17.267 | 5000 | 5000 | 15143 |
| rl_optimal | -44.080 | [-65.612, -22.548] | 10.04% | 0.57% | 100.00% | 0.00% | 0.00% | 0.044 | 5000 | 5000 | 19696 |

### m3 vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 56.235 | [35.139, 77.331] | 91.28% | 0.56% | 100.00% | 0.00% | 0.00% | 14.375 | 5000 | 5000 | 13253 |
| rl_coverage | -56.235 | [-77.331, -35.139] | 8.16% | 0.56% | 100.00% | 0.00% | 0.00% | 0.042 | 5000 | 5000 | 19139 |

### m3 vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 637.625 | [604.703, 670.547] | 83.03% | 1.30% | 100.00% | 0.00% | 0.00% | 20.923 | 5000 | 5000 | 36062 |
| random | -637.625 | [-670.547, -604.703] | 15.67% | 1.30% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 37589 |

### m4 vs m4 (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 0.000 | [-65.333, 65.333] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 8126.105 | 5 | 5 | 40 |
| m4 | 0.000 | [-65.333, 65.333] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 7771.862 | 5 | 5 | 40 |

### m4 vs rl_optimal (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -290.000 | [-506.588, -73.412] | 40.00% | 0.00% | 100.00% | 0.00% | 0.00% | 10785.591 | 5 | 5 | 27 |
| rl_optimal | 290.000 | [73.412, 506.588] | 60.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.440 | 5 | 5 | 25 |

### m4 vs rl_coverage (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -55.000 | [-399.614, 289.614] | 60.00% | 0.00% | 100.00% | 0.00% | 0.00% | 10531.039 | 5 | 5 | 20 |
| rl_coverage | 55.000 | [-289.614, 399.614] | 40.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.440 | 5 | 5 | 22 |

### m4 vs random (`10` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | 90.000 | [-472.929, 652.929] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 10622.633 | 5 | 5 | 35 |
| random | -90.000 | [-652.929, 472.929] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.025 | 5 | 5 | 29 |

### rl_optimal vs rl_optimal (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | -1.600 | [-8.903, 5.703] | 50.17% | 0.02% | 100.00% | 0.00% | 0.00% | 0.040 | 5000 | 5000 | 6967 |
| rl_optimal | 1.600 | [-5.703, 8.903] | 49.81% | 0.02% | 100.00% | 0.00% | 0.00% | 0.040 | 5000 | 5000 | 6970 |

### rl_optimal vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 13.410 | [5.404, 21.416] | 54.28% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 5000 | 5000 | 6504 |
| rl_coverage | -13.410 | [-21.416, -5.404] | 45.72% | 0.00% | 100.00% | 0.00% | 0.00% | 0.039 | 5000 | 5000 | 7006 |

### rl_optimal vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | 12.065 | [-0.794, 24.924] | 20.17% | 0.13% | 100.00% | 0.00% | 0.00% | 0.036 | 5000 | 5000 | 13675 |
| random | -12.065 | [-24.924, 0.794] | 79.70% | 0.13% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 10332 |

### rl_coverage vs rl_coverage (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | -1.675 | [-4.071, 0.721] | 49.71% | 0.00% | 100.00% | 0.00% | 0.00% | 0.040 | 5000 | 5000 | 6151 |
| rl_coverage | 1.675 | [-0.721, 4.071] | 50.29% | 0.00% | 100.00% | 0.00% | 0.00% | 0.040 | 5000 | 5000 | 6101 |

### rl_coverage vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | 20.810 | [9.143, 32.477] | 18.00% | 0.12% | 100.00% | 0.00% | 0.00% | 0.036 | 5000 | 5000 | 13481 |
| random | -20.810 | [-32.477, -9.143] | 81.88% | 0.12% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 9108 |

### random vs random (`10000` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | -8.630 | [-29.922, 12.662] | 49.25% | 0.24% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 23605 |
| random | 8.630 | [-12.662, 29.922] | 50.51% | 0.24% | 100.00% | 0.00% | 0.00% | 0.002 | 5000 | 5000 | 23483 |

