# Forecast benchmark - final - H=12 (monthly, >=36 periods)

Series: 92 ({'synthetic': 92}); origins per series <= 6; horizon 1..12; seed 2026; forecast points scored: 6624 per method.

## Overall (lower MASE/sMAPE is better; coverage should be near 0.80 / 0.95)

| method | series | MASE_median | MASE_mean | sMAPE_median | relMAE_vs_snaive_gmean | cov80_pooled | cov95_pooled | cov95_median_series | scaled_IS95_median | ms_per_call_mean | fallback_rate |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ensemble | 92 | 1.002 | 1.221 | 19.291 | 0.871 | 0.884 | 0.954 | 0.972 | 7.633 | 1450.407 | 0.000 |
| ets_auto | 92 | 1.088 | 1.339 | 23.203 | 0.939 | 0.728 | 0.877 | 0.903 | 8.814 | 1376.825 | 0.000 |
| hw_current | 92 | 1.064 | 1.264 | 18.867 | 0.903 | 0.867 | 0.936 | 0.958 | 8.216 | 122.291 | 0.000 |
| naive | 92 | 1.449 | 1.662 | 29.500 | 1.230 | 0.904 | 0.968 | 0.986 | 11.655 | 0.228 | 0.000 |
| new | 92 | 1.067 | 1.270 | 21.687 | 0.908 | 0.808 | 0.946 | 0.972 | 7.895 | 486.254 | 0.000 |
| snaive | 92 | 1.130 | 1.395 | 21.945 | 1.000 | 0.722 | 0.851 | 0.910 | 8.551 | 0.163 | 0.000 |
| theta | 92 | 1.053 | 1.269 | 19.207 | 0.908 | 0.931 | 0.971 | 0.986 | 11.232 | 73.201 | 0.000 |

## Paired per-series MASE ratio, new / other (<1 means new is better; geometric mean, 95% bootstrap CI over series)

| b | n | gmean_ratio | ci_lo | ci_hi | median_ratio | win_rate_a | wilcoxon_p |
|---|---|---|---|---|---|---|---|
| hw_current | 92 | 1.015 | 0.960 | 1.075 | 1.004 | 0.478 | 0.846 |
| snaive | 92 | 0.921 | 0.871 | 0.977 | 0.859 | 0.717 | 0.000 |
| naive | 92 | 0.744 | 0.691 | 0.791 | 0.800 | 0.967 | 0.000 |
| ets_auto | 92 | 0.975 | 0.933 | 1.020 | 0.984 | 0.554 | 0.195 |
| theta | 92 | 1.009 | 0.973 | 1.046 | 1.012 | 0.424 | 0.346 |
| ensemble | 92 | 1.051 | 1.012 | 1.093 | 1.011 | 0.435 | 0.040 |

## Interval coverage with 95% cluster-bootstrap CI (resampling series)

| method | nominal | coverage | ci_lo | ci_hi |
|---|---|---|---|---|
| hw_current | 0.800 | 0.867 | 0.843 | 0.888 |
| hw_current | 0.950 | 0.936 | 0.917 | 0.952 |
| new | 0.800 | 0.808 | 0.782 | 0.831 |
| new | 0.950 | 0.946 | 0.930 | 0.960 |

### By history: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| long (>=48) | 0.938 | 0.863 | 0.943 | 1.416 | 0.889 | 1.143 | 0.867 |
| medium (19-47) | 0.963 | 1.135 | 0.968 | 1.392 | 1.171 | 1.116 | 1.072 |
| short (<=18) | 1.274 | 1.379 | 1.183 | 1.412 | 1.110 | 1.441 | 1.332 |

### By history: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| long (>=48) | 0.906 | 0.806 | 0.963 | 0.950 |
| medium (19-47) | 0.841 | 0.808 | 0.918 | 0.943 |
| short (<=18) | 0.885 | 0.819 | 0.944 | 0.955 |

### By seasonal: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| non-seasonal | 0.931 | 1.010 | 0.995 | 1.151 | 0.973 | 1.140 | 0.911 |
| seasonal | 1.009 | 1.209 | 1.068 | 1.711 | 1.128 | 1.112 | 1.162 |

### By seasonal: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.863 | 0.778 | 0.938 | 0.930 |
| True | 0.870 | 0.829 | 0.935 | 0.958 |

### By freq: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| MS | 1.002 | 1.088 | 1.064 | 1.449 | 1.067 | 1.130 | 1.053 |

### By freq: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| MS | 0.867 | 0.808 | 0.936 | 0.946 |

### By intermittent: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| continuous | 1.002 | 1.088 | 1.064 | 1.514 | 1.090 | 1.137 | 1.053 |
| intermittent | 0.930 | 0.944 | 0.921 | 1.001 | 0.883 | 1.041 | 0.925 |

### By intermittent: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| False | 0.863 | 0.807 | 0.934 | 0.944 |
| True | 0.951 | 0.833 | 0.979 | 0.990 |

### By noise: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| high | 0.870 | 0.952 | 0.920 | 1.201 | 0.877 | 1.032 | 0.980 |
| low | 1.073 | 1.183 | 1.116 | 1.931 | 1.240 | 1.173 | 1.259 |
| med | 1.066 | 1.201 | 1.026 | 1.494 | 1.081 | 1.126 | 1.047 |

### By noise: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| high | 0.908 | 0.822 | 0.962 | 0.963 |
| low | 0.823 | 0.788 | 0.893 | 0.928 |
| med | 0.872 | 0.812 | 0.949 | 0.949 |

### By events: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| clean | 0.859 | 0.911 | 0.846 | 1.302 | 0.927 | 1.005 | 0.870 |
| has spike/shift | 1.269 | 1.374 | 1.219 | 1.592 | 1.359 | 1.387 | 1.295 |

### By kind: median MASE

| segment | ensemble | ets_auto | hw_current | naive | new | snaive | theta |
|---|---|---|---|---|---|---|---|
| synthetic | 1.002 | 1.088 | 1.064 | 1.449 | 1.067 | 1.130 | 1.053 |

### By kind: pooled interval coverage

| segment | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 |
|---|---|---|---|---|
| synthetic | 0.867 | 0.808 | 0.936 | 0.946 |

### By horizon step

| h | hw_current_cov80 | new_cov80 | hw_current_cov95 | new_cov95 | hw_current_MASE | new_MASE |
|---|---|---|---|---|---|---|
| 1.000 | 0.667 | 0.808 | 0.832 | 0.946 | 1.006 | 1.025 |
| 2.000 | 0.759 | 0.813 | 0.877 | 0.947 | 1.128 | 1.127 |
| 3.000 | 0.822 | 0.797 | 0.929 | 0.967 | 1.175 | 1.219 |
| 4.000 | 0.844 | 0.793 | 0.946 | 0.951 | 1.169 | 1.178 |
| 5.000 | 0.871 | 0.784 | 0.946 | 0.935 | 1.291 | 1.341 |
| 6.000 | 0.926 | 0.792 | 0.947 | 0.949 | 1.256 | 1.332 |
| 7.000 | 0.906 | 0.793 | 0.951 | 0.944 | 1.284 | 1.374 |
| 8.000 | 0.908 | 0.824 | 0.958 | 0.942 | 1.388 | 1.369 |
| 9.000 | 0.913 | 0.803 | 0.957 | 0.940 | 1.398 | 1.393 |
| 10.000 | 0.918 | 0.812 | 0.951 | 0.944 | 1.374 | 1.305 |
| 11.000 | 0.931 | 0.835 | 0.966 | 0.944 | 1.428 | 1.363 |
| 12.000 | 0.938 | 0.839 | 0.975 | 0.947 | 1.275 | 1.214 |

### New method: chosen model frequency

| cfg | count |
|---|---|
| combo_all | 310 |
| ses | 79 |
| naive | 36 |
| snaive | 33 |
| theta | 26 |
| ets_s | 25 |
| damped | 23 |
| ets_s_log | 19 |
| combo_trend | 1 |

### New method: confidence label vs realised error

| conf | forecasts | MASE_median | WAPE_median | cov80 | cov95 |
|---|---|---|---|---|---|
| high | 264 | 0.877 | 0.150 | 0.790 | 0.936 |
| low | 78 | 0.973 | 0.234 | 0.861 | 0.973 |
| medium | 210 | 1.083 | 0.255 | 0.810 | 0.950 |
