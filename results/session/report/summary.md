# Results

57 runs, 24 tasks, 5 configs

## Pass rate and mean cost per config, by tier

### Tier 1: Mechanical

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 100% | $0.007 | 11 | 3 |
| haiku-4-5@low | 100% | $0.073 | 28 | 3 |

### Tier 2: Bounded impl

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 100% | $0.009 | 22 | 3 |
| haiku-4-5@low | 100% | $0.126 | 63 | 3 |
| sonnet-5@medium | 100% | $0.206 | 35 | 3 |

### Tier 3: Debugging

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 100% | $0.007 | 18 | 4 |
| haiku-4-5@low | 100% | $0.105 | 63 | 3 |
| sonnet-5@medium | 100% | $0.135 | 20 | 3 |

### Tier 4: Architecture

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 100% | $0.011 | 40 | 4 |
| haiku-4-5@low | 100% | $0.146 | 68 | 1 |
| sonnet-5@medium | 100% | $0.225 | 47 | 1 |
| sonnet-5-5@medium | 100% | $0.252 | 186 | 2 |

### Tier 5: Long context

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 100% | $0.009 | 28 | 2 |
| sonnet-5-5@medium | 100% | $0.120 | 24 | 1 |
| haiku-4-5@low | 100% | $0.172 | 88 | 1 |
| sonnet-5@medium | 100% | $0.295 | 73 | 1 |

### Tier 6: Real repo

| config | pass rate | mean cost | mean wall s | n |
|---|---|---|---|---|
| haiku-5-5@low | 88% | $0.043 | 89 | 8 |
| sonnet-5-5@medium | 88% | $0.346 | 64 | 8 |
| opus-5-5@medium | 67% | $1.035 | 90 | 3 |

## Cheapest config that passed every repetition, per task

| task | tier | cheapest passing config | cost | most expensive passing | cost | saving |
|---|---|---|---|---|---|---|
| r01_fromager_distinfo | 6 | haiku-5-5@low | $0.015 | sonnet-5-5@medium | $0.318 | 95% |
| r01t_fromager_distinfo_ticket | 6 | haiku-5-5@low | $0.018 | opus-5-5@medium | $0.879 | 98% |
| r02_fromager_age_filter | 6 | haiku-5-5@low | $0.012 | sonnet-5-5@medium | $0.214 | 95% |
| r02t_fromager_age_filter_ticket | 6 | haiku-5-5@low | $0.025 | opus-5-5@medium | $0.670 | 96% |
| r03_fromager_dep_chain | 6 | haiku-5-5@low | $0.019 | sonnet-5-5@medium | $0.230 | 92% |
| r03t_fromager_dep_chain_ticket | 6 | none passed | | | | |
| r04_fromager_age_fallback | 6 | haiku-5-5@low | $0.033 | sonnet-5-5@medium | $0.290 | 89% |
| r05_fromager_version_prebuilt | 6 | haiku-5-5@low | $0.058 | sonnet-5-5@medium | $0.505 | 89% |
| t01_rename_symbol | 1 | haiku-5-5@low | $0.009 | haiku-4-5@low | $0.095 | 91% |
| t02_ini_to_toml | 1 | haiku-5-5@low | $0.006 | haiku-4-5@low | $0.058 | 90% |
| t03_add_type_hints | 1 | haiku-5-5@low | $0.005 | haiku-4-5@low | $0.066 | 92% |
| t04_lru_cache | 2 | haiku-5-5@low | $0.011 | sonnet-5@medium | $0.245 | 96% |
| t05_cli_json_flag | 2 | haiku-5-5@low | $0.006 | sonnet-5@medium | $0.161 | 96% |
| t06_log_parser | 2 | haiku-5-5@low | $0.009 | sonnet-5@medium | $0.213 | 96% |
| t07_mutable_default | 3 | haiku-5-5@low | $0.006 | sonnet-5@medium | $0.130 | 96% |
| t08_timezone_bug | 3 | haiku-5-5@low | $0.007 | haiku-4-5@low | $0.193 | 96% |
| t09_thread_safety | 3 | haiku-5-5@low | $0.008 | sonnet-5@medium | $0.142 | 94% |
| t10_plugin_registry | 4 | haiku-5-5@low | $0.010 | haiku-5-5@low | $0.010 | 0% |
| t11_async_migration | 4 | haiku-5-5@low | $0.008 | sonnet-5@medium | $0.225 | 96% |
| t12_needle_bug | 5 | haiku-5-5@low | $0.008 | sonnet-5@medium | $0.295 | 97% |
| t13_unicode_dedupe | 3 | haiku-5-5@low | $0.006 | haiku-5-5@low | $0.006 | 0% |
| t14_dep_resolver | 4 | haiku-5-5@low | $0.015 | sonnet-5-5@medium | $0.309 | 95% |
| t15_perf_regression | 5 | haiku-5-5@low | $0.010 | sonnet-5-5@medium | $0.120 | 92% |
| t16_json_patch | 4 | haiku-5-5@low | $0.011 | sonnet-5-5@medium | $0.194 | 94% |

## Routing scenario

Everything on `opus-5-5@medium`: $3.10 for 67% pass rate (3 runs).
Routed per tier to the cheapest fully-passing config: $0.31 for 23 passing tasks.
