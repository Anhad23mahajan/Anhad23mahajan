# Forecast benchmark - dev1 - H=6

Series: 120 ({'synthetic': 120}); origins per series <= 6; horizon 1..6; seed 1; forecast points scored: 4212 per method.

## Overall (lower MASE/sMAPE is better; coverage should be near 0.80 / 0.95)

| method | series | MASE_median | MASE_mean | sMAPE_median | relMAE_vs_snaive_gmean | cov80_pooled | cov95_pooled | cov95_median_series | scaled_IS95_median | ms_per_call_mean | fallback_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| c_combo_seasonal | 120 | 0.965 | 1.102 | 24.385 | 0.889 | 0.293 | 0.311 | 0.000 | 29.174 | 62.214 | 0.318 |
| c_combo_trend | 120 | 0.974 | 1.162 | 24.805 | 0.949 | 0.000 | 0.000 | 0.000 | 38.953 | 40.404 | 0.000 |
| c_damped | 120 | 1.008 | 1.253 | 26.124 | 1.009 | 0.000 | 0.000 | 0.000 | 40.316 | 17.534 | 0.000 |
| c_ets_s | 120 | 1.029 | 1.131 | 25.428 | 0.912 | 0.505 | 0.540 | 0.556 | 17.583 | 35.624 | 0.558 |
| c_ets_s_log | 120 | 1.048 | 1.118 | 24.571 | 0.896 | 0.537 | 0.574 | 0.806 | 15.484 | 14.430 | 0.594 |
| c_ses | 120 | 0.975 | 1.191 | 25.679 | 0.966 | 0.000 | 0.000 | 0.000 | 39.020 | 8.261 | 0.000 |
| ensemble | 120 | 0.962 | 1.083 | 23.250 | 0.876 | 0.863 | 0.959 | 0.972 | 6.396 | 0.108 | 0.000 |
| ets_auto | 120 | 0.993 | 1.119 | 25.127 | 0.909 | 0.733 | 0.881 | 0.889 | 6.815 | 597.785 | 0.000 |
| hw_current | 120 | 1.028 | 1.175 | 24.461 | 0.935 | 0.824 | 0.921 | 0.944 | 6.949 | 75.463 | 0.000 |
| naive | 120 | 1.178 | 1.325 | 28.850 | 1.077 | 0.892 | 0.965 | 1.000 | 8.619 | 0.165 | 0.000 |
| new | 120 | 1.020 | 1.106 | 23.611 | 0.890 | 0.750 | 0.902 | 0.917 | 6.723 | 302.493 | 0.000 |
| snaive | 120 | 1.070 | 1.261 | 25.538 | 1.000 | 0.772 | 0.897 | 0.944 | 7.761 | 0.147 | 0.000 |
| theta | 120 | 0.989 | 1.134 | 25.009 | 0.914 | 0.898 | 0.960 | 0.972 | 8.020 | 64.246 | 0.000 |

## Paired per-series MASE ratio, new / other (<1 means new is better; geometric mean, 95% bootstrap CI over series)

| b | n | gmean_ratio | ci_lo | ci_hi | median_ratio | win_rate_a | wilcoxon_p |
|---|---|---|---|---|---|---|---|
| hw_current | 120 | 0.955 | 0.913 | 0.993 | 0.973 | 0.583 | 0.047 |
| snaive | 120 | 0.893 | 0.845 | 0.936 | 0.920 | 0.658 | 0.000 |
| naive | 120 | 0.825 | 0.760 | 0.889 | 0.880 | 0.733 | 0.000 |
| ets_auto | 120 | 0.980 | 0.942 | 1.018 | 1.003 | 0.433 | 0.988 |
| theta | 120 | 0.977 | 0.943 | 1.010 | 0.996 | 0.508 | 0.769 |
| ensemble | 120 | 1.017 | 0.982 | 1.051 | 1.020 | 0.433 | 0.141 |

## Interval coverage with 95% cluster-bootstrap CI (resampling series)

| method | nominal | coverage | ci_lo | ci_hi |
|---|---|---|---|---|
| hw_current | 0.800 | 0.824 | 0.799 | 0.847 |
| hw_current | 0.950 | 0.921 | 0.904 | 0.937 |
| new | 0.800 | 0.750 | 0.731 | 0.769 |
| new | 0.950 | 0.902 | 0.887 | 0.916 |

### By history: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| long (>=48) | 0.936 | 0.978 | 0.937 | 1.182 | 0.885 | 1.088 | 0.931 |
| medium (19-47) | 0.965 | 0.945 | 0.971 | 1.200 | 1.017 | 1.071 | 0.967 |
| short (<=18) | 0.954 | 0.963 | 1.101 | 1.078 | 1.074 | 1.071 | 1.003 |

### By history: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| long (>=48) | 0.883 | 0.730 | 0.964 | 0.913 |
| medium (19-47) | 0.825 | 0.760 | 0.919 | 0.920 |
| short (<=18) | 0.774 | 0.749 | 0.891 | 0.866 |

### By seasonal: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| non-seasonal | 1.030 | 0.993 | 1.052 | 1.176 | 1.040 | 1.184 | 0.985 |
| seasonal | 0.905 | 0.997 | 1.021 | 1.229 | 0.986 | 0.977 | 1.003 |

### By seasonal: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.850 | 0.745 | 0.935 | 0.890 |
| True | 0.797 | 0.754 | 0.907 | 0.914 |

### By freq: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| D | 0.796 | 0.799 | 0.867 | 1.062 | 0.852 | 0.931 | 0.857 |
| MS | 1.048 | 1.146 | 1.079 | 1.322 | 1.074 | 1.115 | 1.069 |
| W | 1.040 | 1.017 | 1.040 | 1.158 | 1.039 | 1.192 | 1.014 |

### By freq: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| D | 0.835 | 0.758 | 0.926 | 0.907 |
| MS | 0.788 | 0.753 | 0.898 | 0.903 |
| W | 0.848 | 0.739 | 0.939 | 0.897 |

### By intermittent: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| continuous | 0.975 | 1.014 | 1.032 | 1.178 | 1.011 | 1.080 | 0.984 |
| intermittent | 0.919 | 0.902 | 1.021 | 1.152 | 1.064 | 1.050 | 0.997 |

### By intermittent: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.817 | 0.751 | 0.917 | 0.904 |
| True | 0.884 | 0.735 | 0.960 | 0.881 |

### By noise: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| high | 0.880 | 0.885 | 0.983 | 1.080 | 0.991 | 1.033 | 0.931 |
| low | 0.993 | 1.001 | 1.033 | 1.281 | 1.048 | 1.061 | 0.995 |
| med | 0.980 | 1.020 | 1.048 | 1.191 | 1.061 | 1.123 | 1.031 |

### By noise: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| high | 0.838 | 0.738 | 0.936 | 0.914 |
| low | 0.792 | 0.750 | 0.897 | 0.889 |
| med | 0.836 | 0.757 | 0.928 | 0.903 |

### By events: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| clean | 0.891 | 0.884 | 0.938 | 1.177 | 0.918 | 1.026 | 0.912 |
| has spike/shift | 1.088 | 1.147 | 1.143 | 1.191 | 1.078 | 1.248 | 1.052 |

### By kind: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| synthetic | 0.962 | 0.993 | 1.028 | 1.178 | 1.020 | 1.070 | 0.989 |

### By kind: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| synthetic | 0.824 | 0.750 | 0.921 | 0.902 |

### By horizon step

| h | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 | hw_current_MASE | new_MASE |
|---|---|---|---|---|---|---|
| 1.000 | 0.681 | 0.665 | 0.819 | 0.850 | 1.008 | 1.022 |
| 2.000 | 0.779 | 0.709 | 0.906 | 0.896 | 1.040 | 1.024 |
| 3.000 | 0.832 | 0.756 | 0.933 | 0.895 | 1.211 | 1.134 |
| 4.000 | 0.866 | 0.776 | 0.954 | 0.916 | 1.195 | 1.113 |
| 5.000 | 0.896 | 0.789 | 0.957 | 0.919 | 1.269 | 1.186 |
| 6.000 | 0.887 | 0.801 | 0.957 | 0.936 | 1.327 | 1.167 |

### New method: chosen model frequency

| cfg | count |
|---|---|
| ses | 232 |
| snaive | 115 |
| naive | 112 |
| damped | 87 |
| theta | 70 |
| ets_s | 38 |
| ets_s_log | 25 |
| combo_trend | 14 |
| combo_seasonal | 9 |

### New method: confidence label vs realised error

| conf | forecasts | MASE_median | WAPE_median | cov80 | cov95 |
|---|---|---|---|---|---|
| high | 335 | 0.824 | 0.134 | 0.733 | 0.907 |
| low | 137 | 0.992 | 0.521 | 0.775 | 0.898 |
| medium | 230 | 0.922 | 0.272 | 0.759 | 0.896 |
