# Full-Game Agent Effectiveness Report

## Setup
- Agents: `m2, m3, m4, rl_optimal, rl_coverage, random`
- Hands per non-LLM matchup: `50`
- Hands per LLM matchup (includes `m4`): `1`
- Starting stacks: `100 BB` each (`2000` chips)
- Blinds: `SB=10`, `BB=20`
- Seed: `1337`

## Matchup Results

### m2 vs m2 (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -70.000 | [-377.809, 237.809] | 46.00% | 4.00% | 100.00% | 0.00% | 0.00% | 0.033 | 25 | 25 | 232 |
| m2 | 70.000 | [-237.809, 377.809] | 50.00% | 4.00% | 100.00% | 0.00% | 0.00% | 0.031 | 25 | 25 | 234 |

### m2 vs m3 (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -204.000 | [-879.118, 471.118] | 48.00% | 4.00% | 100.00% | 0.00% | 0.00% | 0.040 | 25 | 25 | 278 |
| m3 | 204.000 | [-471.118, 879.118] | 48.00% | 4.00% | 100.00% | 0.00% | 0.00% | 24.063 | 25 | 25 | 253 |

### m2 vs m4 (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 300.000 | [300.000, 300.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.214 | 1 | 0 | 4 |
| m4 | -300.000 | [-300.000, -300.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 9888.900 | 0 | 1 | 7 |

### m2 vs rl_optimal (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -80.000 | [-443.601, 283.601] | 76.00% | 2.00% | 100.00% | 0.00% | 0.00% | 0.046 | 25 | 25 | 129 |
| rl_optimal | 80.000 | [-283.601, 443.601] | 22.00% | 2.00% | 100.00% | 0.00% | 0.00% | 0.537 | 25 | 25 | 149 |

### m2 vs rl_coverage (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | -66.000 | [-429.854, 297.854] | 76.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.033 | 25 | 25 | 118 |
| rl_coverage | 66.000 | [-297.854, 429.854] | 24.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.736 | 25 | 25 | 148 |

### m2 vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m2 | 663.000 | [273.470, 1052.530] | 82.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.032 | 25 | 25 | 199 |
| random | -663.000 | [-1052.530, -273.470] | 18.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 25 | 25 | 192 |

### m3 vs m3 (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | -168.000 | [-910.173, 574.173] | 44.00% | 2.00% | 100.00% | 0.00% | 0.00% | 26.501 | 25 | 25 | 290 |
| m3 | 168.000 | [-574.173, 910.173] | 54.00% | 2.00% | 100.00% | 0.00% | 0.00% | 26.285 | 25 | 25 | 293 |

### m3 vs m4 (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 300.000 | [300.000, 300.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 68.415 | 1 | 0 | 4 |
| m4 | -300.000 | [-300.000, -300.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 10714.950 | 0 | 1 | 6 |

### m3 vs rl_optimal (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 7.000 | [-449.812, 463.812] | 86.00% | 0.00% | 100.00% | 0.00% | 0.00% | 57.673 | 25 | 25 | 101 |
| rl_optimal | -7.000 | [-463.812, 449.812] | 14.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.168 | 25 | 25 | 124 |

### m3 vs rl_coverage (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | -80.000 | [-330.627, 170.627] | 90.00% | 0.00% | 100.00% | 0.00% | 0.00% | 24.684 | 25 | 25 | 60 |
| rl_coverage | 80.000 | [-170.627, 330.627] | 10.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.091 | 25 | 25 | 86 |

### m3 vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m3 | 777.000 | [369.610, 1184.390] | 90.00% | 0.00% | 100.00% | 0.00% | 0.00% | 22.593 | 25 | 25 | 166 |
| random | -777.000 | [-1184.390, -369.610] | 10.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 25 | 25 | 187 |

### m4 vs m4 (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -100.000 | [-100.000, -100.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 9270.311 | 1 | 0 | 4 |
| m4 | 100.000 | [100.000, 100.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 8822.701 | 0 | 1 | 4 |

### m4 vs rl_optimal (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -100.000 | [-100.000, -100.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 12036.570 | 1 | 0 | 2 |
| rl_optimal | 100.000 | [100.000, 100.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.203 | 0 | 1 | 1 |

### m4 vs rl_coverage (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -100.000 | [-100.000, -100.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 11199.642 | 1 | 0 | 2 |
| rl_coverage | 100.000 | [100.000, 100.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.190 | 0 | 1 | 2 |

### m4 vs random (`1` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| m4 | -900.000 | [-900.000, -900.000] | 0.00% | 0.00% | 100.00% | 0.00% | 0.00% | 13349.414 | 1 | 0 | 5 |
| random | 900.000 | [900.000, 900.000] | 100.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.018 | 0 | 1 | 4 |

### rl_optimal vs rl_optimal (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | -149.000 | [-455.501, 157.501] | 54.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.123 | 25 | 25 | 35 |
| rl_optimal | 149.000 | [-157.501, 455.501] | 46.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.121 | 25 | 25 | 40 |

### rl_optimal vs rl_coverage (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | -95.000 | [-251.606, 61.606] | 56.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.069 | 25 | 25 | 36 |
| rl_coverage | 95.000 | [-61.606, 251.606] | 44.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.077 | 25 | 25 | 41 |

### rl_optimal vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_optimal | -152.000 | [-390.493, 86.493] | 14.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.088 | 25 | 25 | 72 |
| random | 152.000 | [-86.493, 390.493] | 86.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.004 | 25 | 25 | 53 |

### rl_coverage vs rl_coverage (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | -8.000 | [-32.786, 16.786] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.077 | 25 | 25 | 29 |
| rl_coverage | 8.000 | [-16.786, 32.786] | 50.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.081 | 25 | 25 | 28 |

### rl_coverage vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| rl_coverage | 33.000 | [-229.732, 295.732] | 20.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.075 | 25 | 25 | 78 |
| random | -33.000 | [-295.732, 229.732] | 80.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.003 | 25 | 25 | 56 |

### random vs random (`50` hands)

| Agent | bb/100 | 95% CI (bb/100) | Win rate | Tie rate | Legality | Error rate | Fallback rate | Avg decision ms | SB hands | BB hands | Decisions |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| random | -24.000 | [-307.965, 259.965] | 40.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 25 | 25 | 117 |
| random | 24.000 | [-259.965, 307.965] | 60.00% | 0.00% | 100.00% | 0.00% | 0.00% | 0.002 | 25 | 25 | 111 |

