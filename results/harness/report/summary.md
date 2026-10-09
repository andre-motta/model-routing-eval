# Results

382 runs, 24 tasks, 11 configs

## Pass rate and mean cost per config, by tier

### Tier 1: Mechanical

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 100% | $0.000 | 87 | 3 |
| gpt-6-luna@low | 100% | $0.002 | 35 | 6 |
| gpt-6-luna@xhigh | 100% | $0.004 | 99 | 3 |
| haiku-5-5@low | 100% | $0.009 | 15 | 6 |
| haiku-5-5@medium | 100% | $0.011 | 24 | 6 |
| gpt-6.1-sol@low | 100% | $0.019 | 36 | 6 |
| sonnet-5-5@low | 100% | $0.105 | 13 | 6 |
| sonnet-5-5@medium | 100% | $0.111 | 13 | 6 |
| opus-5-5@medium | 100% | $0.227 | 15 | 3 |

### Tier 2: Bounded impl

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 100% | $0.000 | 140 | 3 |
| gpt-6-luna@low | 100% | $0.003 | 58 | 6 |
| gpt-6-luna@xhigh | 100% | $0.006 | 138 | 3 |
| haiku-5-5@low | 100% | $0.010 | 22 | 6 |
| haiku-5-5@medium | 100% | $0.014 | 35 | 6 |
| gpt-6.1-sol@low | 100% | $0.034 | 63 | 6 |
| sonnet-5-5@low | 100% | $0.130 | 18 | 6 |
| sonnet-5-5@medium | 100% | $0.147 | 23 | 6 |
| opus-5-5@medium | 100% | $0.316 | 32 | 3 |

### Tier 3: Debugging

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 100% | $0.000 | 227 | 4 |
| gpt-6-luna@low | 100% | $0.002 | 44 | 8 |
| gpt-6-luna@xhigh | 100% | $0.006 | 142 | 4 |
| haiku-5-5@low | 100% | $0.010 | 23 | 8 |
| haiku-5-5@medium | 100% | $0.012 | 33 | 8 |
| gpt-6.1-sol@low | 100% | $0.027 | 53 | 8 |
| sonnet-5-5@low | 100% | $0.152 | 20 | 8 |
| sonnet-5-5@medium | 100% | $0.159 | 20 | 8 |
| opus-5-5@medium | 100% | $0.274 | 38 | 4 |

### Tier 4: Architecture

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 100% | $0.000 | 342 | 4 |
| gpt-6-luna@low | 88% | $0.005 | 88 | 8 |
| gpt-6-luna@xhigh | 100% | $0.010 | 237 | 4 |
| haiku-5-5@low | 100% | $0.014 | 38 | 8 |
| haiku-5-5@medium | 100% | $0.043 | 87 | 8 |
| gpt-6.1-sol@low | 100% | $0.047 | 93 | 8 |
| sonnet-5-5@low | 88% | $0.141 | 26 | 8 |
| gpt-5.6-terra@medium | 100% | $0.158 | 251 | 2 |
| sonnet-5-5@medium | 100% | $0.202 | 62 | 8 |
| gpt-6-astra@medium | 100% | $0.429 | 132 | 2 |
| opus-5-5@medium | 100% | $0.951 | 261 | 4 |

### Tier 5: Long context

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 100% | $0.000 | 158 | 2 |
| gpt-6-luna@low | 75% | $0.002 | 38 | 4 |
| gpt-6-luna@xhigh | 100% | $0.005 | 117 | 2 |
| haiku-5-5@low | 100% | $0.015 | 28 | 4 |
| haiku-5-5@medium | 100% | $0.015 | 38 | 4 |
| gpt-6.1-sol@low | 100% | $0.031 | 56 | 4 |
| gpt-5.6-terra@medium | 100% | $0.101 | 123 | 1 |
| sonnet-5-5@medium | 100% | $0.165 | 26 | 4 |
| sonnet-5-5@low | 100% | $0.206 | 26 | 4 |
| gpt-6-astra@medium | 100% | $0.262 | 61 | 1 |
| opus-5-5@medium | 100% | $0.485 | 40 | 2 |

### Tier 6: Real repo

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| glm-5-3@medium | 88% | $0.000 | 484 | 8 |
| gpt-6-luna@low | 81% | $0.010 | 128 | 16 |
| gpt-6-luna@xhigh | 62% | $0.025 | 418 | 8 |
| gpt-6.1-sol@low | 94% | $0.059 | 96 | 16 |
| haiku-5-5@low | 88% | $0.097 | 86 | 16 |
| haiku-5-5@medium | 88% | $0.143 | 117 | 16 |
| gpt-5.6-terra@medium | 75% | $0.243 | 241 | 8 |
| sonnet-5-5@low | 94% | $0.416 | 54 | 16 |
| sonnet-5-5@medium | 94% | $0.422 | 54 | 16 |
| gpt-6-astra@medium | 100% | $0.615 | 123 | 8 |
| opus-5-5@medium | 100% | $1.181 | 103 | 8 |

## Cheapest config that passed every repetition, per task

| task | tier | cheapest passing config | cost | most expensive passing | cost | saving |
|---|---|---|---|---|---|---|
| r01_fromager_distinfo | 6 | gpt-6-luna@low | $0.007 | opus-5-5@medium | $1.048 | 99% |
| r01t_fromager_distinfo_ticket | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.880 | 100% |
| r02_fromager_age_filter | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.526 | 100% |
| r02t_fromager_age_filter_ticket | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.769 | 100% |
| r03_fromager_dep_chain | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $1.031 | 100% |
| r03t_fromager_dep_chain_ticket | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $1.645 | 100% |
| r04_fromager_age_fallback | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $1.504 | 100% |
| r05_fromager_version_prebuilt | 6 | glm-5-3@medium | $0.000 | opus-5-5@medium | $2.050 | 100% |
| t01_rename_symbol | 1 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.214 | 100% |
| t02_ini_to_toml | 1 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.232 | 100% |
| t03_add_type_hints | 1 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.234 | 100% |
| t04_lru_cache | 2 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.294 | 100% |
| t05_cli_json_flag | 2 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.278 | 100% |
| t06_log_parser | 2 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.376 | 100% |
| t07_mutable_default | 3 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.299 | 100% |
| t08_timezone_bug | 3 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.289 | 100% |
| t09_thread_safety | 3 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.206 | 100% |
| t10_plugin_registry | 4 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.392 | 100% |
| t11_async_migration | 4 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.253 | 100% |
| t12_needle_bug | 5 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.427 | 100% |
| t13_unicode_dedupe | 3 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.302 | 100% |
| t14_dep_resolver | 4 | glm-5-3@medium | $0.000 | opus-5-5@medium | $2.665 | 100% |
| t15_perf_regression | 5 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.543 | 100% |
| t16_json_patch | 4 | glm-5-3@medium | $0.000 | opus-5-5@medium | $0.495 | 100% |

## Routing scenario

Everything on `opus-5-5@medium`: $16.95 for 100% pass rate (24 runs).
Routed per tier to the cheapest fully-passing config: $0.00 for 23 passing tasks.
