# Forecast benchmark - final - H=6

Series: 366 ({'synthetic': 360, 'demo': 6}); origins per series <= 6; horizon 1..6; seed 2026; forecast points scored: 12600 per method.

## Overall (lower MASE/sMAPE is better; coverage should be near 0.80 / 0.95)

| method | series | MASE_median | MASE_mean | sMAPE_median | relMAE_vs_snaive_gmean | cov80_pooled | cov95_pooled | cov95_median_series | scaled_IS95_median | ms_per_call_mean | fallback_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ensemble | 366 | 0.953 | 1.182 | 23.094 | 0.858 | 0.854 | 0.944 | 0.972 | 6.686 | 367.250 | 0.000 |
| ets_auto | 366 | 1.002 | 1.247 | 25.303 | 0.899 | 0.729 | 0.877 | 0.889 | 7.153 | 332.228 | 0.000 |
| hw_current | 366 | 0.976 | 1.259 | 24.696 | 0.902 | 0.820 | 0.919 | 0.944 | 7.010 | 39.717 | 0.000 |
| naive | 366 | 1.178 | 1.435 | 28.960 | 1.074 | 0.883 | 0.957 | 0.972 | 9.032 | 0.109 | 0.000 |
| new | 366 | 0.946 | 1.136 | 21.871 | 0.829 | 0.799 | 0.941 | 0.972 | 7.191 | 212.195 | 0.000 |
| snaive | 366 | 1.141 | 1.387 | 27.064 | 1.000 | 0.769 | 0.883 | 0.917 | 8.931 | 0.067 | 0.000 |
| theta | 366 | 0.956 | 1.215 | 24.001 | 0.882 | 0.890 | 0.952 | 0.972 | 8.158 | 34.876 | 0.000 |

## Paired per-series MASE ratio, new / other (<1 means new is better; geometric mean, 95% bootstrap CI over series)

| b | n | gmean_ratio | ci_lo | ci_hi | median_ratio | win_rate_a | wilcoxon_p |
|---|---|---|---|---|---|---|---|
| hw_current | 366 | 0.930 | 0.909 | 0.952 | 0.967 | 0.645 | 0.000 |
| snaive | 366 | 0.838 | 0.816 | 0.861 | 0.847 | 0.795 | 0.000 |
| naive | 366 | 0.776 | 0.744 | 0.806 | 0.839 | 0.798 | 0.000 |
| ets_auto | 366 | 0.932 | 0.909 | 0.956 | 0.976 | 0.596 | 0.000 |
| theta | 366 | 0.948 | 0.929 | 0.967 | 0.981 | 0.587 | 0.000 |
| ensemble | 366 | 0.974 | 0.957 | 0.991 | 0.981 | 0.604 | 0.000 |

## Interval coverage with 95% cluster-bootstrap CI (resampling series)

| method | nominal | coverage | ci_lo | ci_hi |
|---|---|---|---|---|
| hw_current | 0.800 | 0.820 | 0.805 | 0.834 |
| hw_current | 0.950 | 0.919 | 0.909 | 0.929 |
| new | 0.800 | 0.799 | 0.788 | 0.810 |
| new | 0.950 | 0.941 | 0.933 | 0.949 |

### By history: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| long (>=48) | 0.867 | 0.873 | 0.859 | 1.124 | 0.823 | 1.060 | 0.844 |
| medium (19-47) | 0.896 | 0.941 | 0.903 | 1.200 | 0.865 | 1.049 | 0.913 |
| short (<=18) | 1.039 | 1.072 | 1.096 | 1.137 | 1.077 | 1.176 | 1.090 |

### By history: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| long (>=48) | 0.891 | 0.822 | 0.962 | 0.962 |
| medium (19-47) | 0.824 | 0.794 | 0.922 | 0.953 |
| short (<=18) | 0.736 | 0.784 | 0.867 | 0.898 |

### By seasonal: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| non-seasonal | 0.930 | 0.963 | 0.976 | 1.119 | 0.920 | 1.184 | 0.913 |
| seasonal | 0.982 | 1.051 | 0.985 | 1.294 | 0.972 | 1.049 | 1.011 |

### By seasonal: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.843 | 0.795 | 0.935 | 0.943 |
| True | 0.798 | 0.803 | 0.904 | 0.940 |

### By freq: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| D | 0.796 | 0.775 | 0.805 | 1.066 | 0.774 | 0.967 | 0.800 |
| MS | 1.096 | 1.185 | 1.133 | 1.395 | 1.092 | 1.171 | 1.169 |
| W | 0.953 | 0.954 | 0.947 | 1.107 | 0.901 | 1.199 | 0.917 |

### By freq: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| D | 0.824 | 0.809 | 0.923 | 0.952 |
| MS | 0.786 | 0.794 | 0.892 | 0.930 |
| W | 0.857 | 0.797 | 0.948 | 0.947 |

### By intermittent: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| continuous | 0.964 | 1.020 | 0.990 | 1.214 | 0.961 | 1.151 | 0.978 |
| intermittent | 0.927 | 0.892 | 0.914 | 0.992 | 0.889 | 1.027 | 0.887 |

### By intermittent: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.811 | 0.798 | 0.913 | 0.938 |
| True | 0.909 | 0.812 | 0.976 | 0.976 |

### By noise: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| demo | 1.433 | 1.710 | 1.559 | 1.436 | 1.585 | 1.766 | 1.793 |
| high | 0.829 | 0.802 | 0.842 | 1.069 | 0.836 | 1.063 | 0.863 |
| low | 0.959 | 1.044 | 0.997 | 1.281 | 0.891 | 1.221 | 0.972 |
| med | 1.031 | 1.097 | 1.050 | 1.239 | 1.005 | 1.159 | 1.053 |

### By noise: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| demo | 0.630 | 0.759 | 0.773 | 0.954 |
| high | 0.857 | 0.812 | 0.941 | 0.957 |
| low | 0.811 | 0.788 | 0.908 | 0.928 |
| med | 0.812 | 0.801 | 0.920 | 0.941 |

### By events: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| clean | 0.887 | 0.906 | 0.892 | 1.168 | 0.889 | 1.068 | 0.895 |
| has spike/shift | 1.071 | 1.107 | 1.084 | 1.221 | 1.007 | 1.221 | 1.051 |

### By kind: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| demo | 1.433 | 1.710 | 1.559 | 1.436 | 1.585 | 1.766 | 1.793 |
| synthetic | 0.951 | 0.996 | 0.976 | 1.176 | 0.944 | 1.133 | 0.955 |

### By kind: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| demo | 0.630 | 0.759 | 0.773 | 0.954 |
| synthetic | 0.823 | 0.800 | 0.922 | 0.941 |

### By horizon step

| h | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 | hw_current_MASE | new_MASE |
|---|---|---|---|---|---|---|
| 1.000 | 0.679 | 0.783 | 0.843 | 0.936 | 1.047 | 1.007 |
| 2.000 | 0.775 | 0.793 | 0.900 | 0.934 | 1.192 | 1.095 |
| 3.000 | 0.835 | 0.803 | 0.927 | 0.947 | 1.288 | 1.181 |
| 4.000 | 0.860 | 0.806 | 0.944 | 0.940 | 1.283 | 1.122 |
| 5.000 | 0.882 | 0.822 | 0.949 | 0.950 | 1.279 | 1.094 |
| 6.000 | 0.890 | 0.788 | 0.952 | 0.941 | 1.432 | 1.246 |

### New method: chosen model frequency

| cfg | count |
|---|---|
| combo_all | 1208 |
| ses | 199 |
| naive | 167 |
| snaive | 163 |
| damped | 113 |
| theta | 110 |
| ets_s_log | 73 |
| ets_s | 51 |
| combo_trend | 16 |

### New method: confidence label vs realised error

| conf | forecasts | MASE_median | WAPE_median | cov80 | cov95 |
|---|---|---|---|---|---|
| high | 981 | 0.776 | 0.139 | 0.786 | 0.943 |
| low | 383 | 0.974 | 0.431 | 0.813 | 0.930 |
| medium | 736 | 0.858 | 0.231 | 0.809 | 0.944 |
