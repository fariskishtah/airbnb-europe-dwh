# Numeric validation: Silver (pandas) vs Gold (SQL) vs dashboard query layer

Comparisons: 42 | mismatches: 0 | relative tolerance 1e-09 | city ranking identical across all three: True

| kpi                                     |   silver_pandas |     gold_sql |   dashboard_query | match   |
|:----------------------------------------|----------------:|-------------:|------------------:|:--------|
| total observations                      |    51707.000000 | 51707.000000 |      51707.000000 | True    |
| avg two-night total                     |      279.879591 |   279.879591 |        279.879591 | True    |
| median two-night total                  |      211.343089 |   211.343089 |        211.343089 | True    |
| avg satisfaction                        |       92.628232 |    92.628232 |         92.628232 | True    |
| avg cleanliness                         |        9.390624 |     9.390624 |          9.390624 | True    |
| avg nightly equivalent                  |      139.939796 |   139.939796 |        139.939796 | True    |
| Amsterdam avg two-night total           |      573.112795 |   573.112795 |        573.112795 | True    |
| Amsterdam median two-night total        |      460.244183 |   460.244183 |        460.244183 | True    |
| Athens avg two-night total              |      151.744121 |   151.744121 |        151.744121 | True    |
| Athens median two-night total           |      127.715417 |   127.715417 |        127.715417 | True    |
| Barcelona avg two-night total           |      293.753706 |   293.753706 |        293.753706 | True    |
| Barcelona median two-night total        |      208.299393 |   208.299393 |        208.299393 | True    |
| Berlin avg two-night total              |      244.583752 |   244.583752 |        244.583752 | True    |
| Berlin median two-night total           |      191.175096 |   191.175096 |        191.175096 | True    |
| Budapest avg two-night total            |      176.513548 |   176.513548 |        176.513548 | True    |
| Budapest median two-night total         |      152.982093 |   152.982093 |        152.982093 | True    |
| Lisbon avg two-night total              |      238.210479 |   238.210479 |        238.210479 | True    |
| Lisbon median two-night total           |      225.375235 |   225.375235 |        225.375235 | True    |
| London avg two-night total              |      362.469256 |   362.469256 |        362.469256 | True    |
| London median two-night total           |      261.294950 |   261.294950 |        261.294950 | True    |
| Paris avg two-night total               |      392.531403 |   392.531403 |        392.531403 | True    |
| Paris median two-night total            |      317.597167 |   317.597167 |        317.597167 | True    |
| Rome avg two-night total                |      205.391950 |   205.391950 |        205.391950 | True    |
| Rome median two-night total             |      182.591822 |   182.591822 |        182.591822 | True    |
| Vienna avg two-night total              |      241.582484 |   241.582484 |        241.582484 | True    |
| Vienna median two-night total           |      208.494028 |   208.494028 |        208.494028 | True    |
| Amsterdam weekend-vs-weekday avg diff % |       10.973438 |    10.973438 |         10.973438 | True    |
| Athens weekend-vs-weekday avg diff %    |       -5.316409 |    -5.316409 |         -5.316409 | True    |
| Barcelona weekend-vs-weekday avg diff % |        4.121573 |     4.121573 |          4.121573 | True    |
| Berlin weekend-vs-weekday avg diff %    |        3.759920 |     3.759920 |          3.759920 | True    |
| Budapest weekend-vs-weekday avg diff %  |        9.909947 |     9.909947 |          9.909947 | True    |
| Lisbon weekend-vs-weekday avg diff %    |        1.564909 |     1.564909 |          1.564909 | True    |
| London weekend-vs-weekday avg diff %    |        1.154650 |     1.154650 |          1.154650 | True    |
| Paris weekend-vs-weekday avg diff %     |       -2.948466 |    -2.948466 |         -2.948466 | True    |
| Rome weekend-vs-weekday avg diff %      |        3.725862 |     3.725862 |          3.725862 | True    |
| Vienna weekend-vs-weekday avg diff %    |        0.979550 |     0.979550 |          0.979550 | True    |
| Entire home/apt avg                     |      324.315150 |   324.315150 |        324.315150 | True    |
| Entire home/apt median                  |      248.456736 |   248.456736 |        248.456736 | True    |
| Private room avg                        |      204.940233 |   204.940233 |        204.940233 | True    |
| Private room median                     |      166.371516 |   166.371516 |        166.371516 | True    |
| Shared room avg                         |      143.566164 |   143.566164 |        143.566164 | True    |
| Shared room median                      |      124.479283 |   124.479283 |        124.479283 | True    |