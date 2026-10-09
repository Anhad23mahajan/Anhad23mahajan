# Forecast benchmark - smoke - H=6

Series: 24 ({'synthetic': 24}); origins per series <= 6; horizon 1..6; seed 1; forecast points scored: 864 per method.

## Overall (lower MASE/sMAPE is better; coverage should be near 0.80 / 0.95)

| method | series | MASE_median | MASE_mean | sMAPE_median | relMAE_vs_snaive_gmean | cov80_pooled | cov95_pooled | cov95_median_series | scaled_IS95_median | ms_per_call_mean | fallback_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| hw_current | 24 | 0.904 | 0.906 | 23.787 | 0.871 | 0.877 | 0.953 | 0.972 | 6.603 | 146.534 | 0.000 |
| naive | 24 | 1.192 | 1.178 | 29.368 | 1.025 | 0.912 | 0.973 | 0.986 | 8.772 | 0.171 | 0.000 |
| new | 24 | 0.999 | 0.931 | 26.165 | 0.866 | 0.736 | 0.906 | 0.917 | 6.617 | 455.354 | 0.000 |
| snaive | 24 | 1.018 | 1.075 | 26.758 | 1.000 | 0.766 | 0.902 | 0.931 | 7.160 | 0.330 | 0.000 |
| theta | 24 | 0.940 | 0.937 | 24.302 | 0.871 | 0.926 | 0.979 | 0.986 | 7.954 | 84.962 | 0.000 |

## Paired per-series MASE ratio, new / other (<1 means new is better; geometric mean, 95% bootstrap CI over series)

| b | n | gmean_ratio | ci_lo | ci_hi | median_ratio | win_rate_a | wilcoxon_p |
|---|---|---|---|---|---|---|---|
| hw_current | 24 | 0.997 | 0.872 | 1.099 | 1.026 | 0.417 | 0.406 |
| snaive | 24 | 0.862 | 0.778 | 0.950 | 0.876 | 0.750 | 0.011 |
| naive | 24 | 0.840 | 0.731 | 0.988 | 0.806 | 0.708 | 0.008 |
| theta | 24 | 0.998 | 0.920 | 1.079 | 1.025 | 0.458 | 0.747 |

## Interval coverage with 95% cluster-bootstrap CI (resampling series)

| method | nominal | coverage | ci_lo | ci_hi |
|---|---|---|---|---|
| hw_current | 0.800 | 0.877 | 0.830 | 0.920 |
| hw_current | 0.950 | 0.953 | 0.931 | 0.971 |
| new | 0.800 | 0.736 | 0.703 | 0.773 |
| new | 0.950 | 0.906 | 0.885 | 0.926 |

### By history: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| long (>=48) | 0.947 | 1.109 | 0.968 | 1.196 | 1.036 |
| medium (19-47) | 0.878 | 1.184 | 0.905 | 0.871 | 0.915 |
| short (<=18) | 0.908 | 1.052 | 0.978 | 1.085 | 0.907 |

### By history: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| long (>=48) | 0.865 | 0.663 | 0.957 | 0.904 |
| medium (19-47) | 0.873 | 0.761 | 0.941 | 0.911 |
| short (<=18) | 0.910 | 0.801 | 0.974 | 0.897 |

### By seasonal: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| non-seasonal | 0.797 | 1.178 | 1.003 | 1.044 | 0.805 |
| seasonal | 0.943 | 1.217 | 0.995 | 0.979 | 0.949 |

### By seasonal: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.881 | 0.747 | 0.960 | 0.891 |
| True | 0.874 | 0.726 | 0.947 | 0.919 |

### By freq: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| D | 0.747 | 1.137 | 0.931 | 0.872 | 0.768 |
| MS | 0.983 | 1.246 | 1.003 | 1.036 | 1.051 |
| W | 0.914 | 1.114 | 0.975 | 1.146 | 0.937 |

### By freq: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| D | 0.829 | 0.671 | 0.935 | 0.875 |
| MS | 0.861 | 0.771 | 0.941 | 0.910 |
| W | 0.919 | 0.747 | 0.972 | 0.922 |

### By intermittent: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| continuous | 0.954 | 1.198 | 1.007 | 1.018 | 0.956 |
| intermittent | 0.774 | 1.128 | 0.794 | 0.990 | 0.863 |

### By intermittent: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.876 | 0.729 | 0.952 | 0.904 |
| True | 0.889 | 0.819 | 0.958 | 0.931 |

### By noise: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| high | 0.753 | 1.143 | 0.999 | 0.895 | 0.770 |
| low | 0.943 | 1.261 | 1.120 | 1.044 | 0.973 |
| med | 1.022 | 1.178 | 0.947 | 1.050 | 0.962 |

### By noise: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| high | 0.924 | 0.729 | 0.976 | 0.917 |
| low | 0.778 | 0.648 | 0.898 | 0.889 |
| med | 0.872 | 0.761 | 0.951 | 0.904 |

### By events: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| clean | 0.865 | 1.206 | 0.857 | 0.993 | 0.925 |
| has spike/shift | 1.023 | 1.147 | 1.037 | 1.259 | 0.949 |

### By kind: median MASE

| segment | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|
| synthetic | 0.904 | 1.192 | 0.999 | 1.018 | 0.940 |

### By kind: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| synthetic | 0.877 | 0.736 | 0.953 | 0.906 |

### By horizon step

| h | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 | hw_current_MASE | new_MASE |
|---|---|---|---|---|---|---|
| 1.000 | 0.722 | 0.646 | 0.833 | 0.868 | 0.815 | 0.882 |
| 2.000 | 0.833 | 0.674 | 0.944 | 0.896 | 0.861 | 0.961 |
| 3.000 | 0.924 | 0.771 | 0.986 | 0.910 | 0.852 | 0.843 |
| 4.000 | 0.896 | 0.743 | 0.979 | 0.896 | 1.039 | 1.011 |
| 5.000 | 0.958 | 0.778 | 0.993 | 0.924 | 0.858 | 0.965 |
| 6.000 | 0.931 | 0.806 | 0.979 | 0.944 | 1.008 | 0.926 |

### New method: chosen model frequency

| cfg | count |
|---|---|
| ses | 50 |
| snaive | 23 |
| naive | 21 |
| theta | 18 |
| damped | 15 |
| ets_s | 9 |
| ets_s_log | 5 |
| combo_trend | 3 |

### New method: confidence label vs realised error

| conf | forecasts | MASE_median | WAPE_median | cov80 | cov95 |
|---|---|---|---|---|---|
| high | 83 | 0.865 | 0.172 | 0.689 | 0.892 |
| low | 18 | 0.547 | 0.637 | 0.833 | 0.935 |
| medium | 43 | 0.777 | 0.275 | 0.787 | 0.922 |
