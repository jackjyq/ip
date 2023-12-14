# Load Test

- https://github.com/JoeDog/siege

## default config

It can handle 4500 request/minute, which is about 6M request daily

`siege -c 100 -d 1 -v -t1M https://ip.jackjyq.com/json`

CPU usage is about 40%

```shell
{       "transactions":                         4498,
        "availability":                       100.00,
        "elapsed_time":                        59.18,
        "data_transferred":                     1.63,
        "response_time":                        0.80,
        "transaction_rate":                    76.01,
        "throughput":                           0.03,
        "concurrency":                         60.95,
        "successful_transactions":              4498,
        "failed_transactions":                     0,
        "longest_transaction":                  5.79,
        "shortest_transaction":                 0.65
}
```

Log size:

0.36 kb / line

if we write 6M request daily ,the log could be 2GB large.

## turn off the log (read and write)

`siege -c 100 -d 1 -v -t1M https://ip.jackjyq.com/json`

CPU usage is about 40%

```shell
{       "transactions":                         4514,
        "availability":                       100.00,
        "elapsed_time":                        59.58,
        "data_transferred":                     1.64,
        "response_time":                        0.82,
        "transaction_rate":                    75.76,
        "throughput":                           0.03,
        "concurrency":                         61.94,
        "successful_transactions":              4514,
        "failed_transactions":                     0,
        "longest_transaction":                  9.66,
        "shortest_transaction":                 0.65
}
```

## change to 3 sync works

`siege -c 100 -d 1 -v -t1M https://ip.jackjyq.com/json`

CPU usage is about 30%

```shell
{       "transactions":                         4392,
        "availability":                       100.00,
        "elapsed_time":                        59.72,
        "data_transferred":                     1.59,
        "response_time":                        0.84,
        "transaction_rate":                    73.54,
        "throughput":                           0.03,
        "concurrency":                         62.04,
        "successful_transactions":              4392,
        "failed_transactions":                     0,
        "longest_transaction":                  5.68,
        "shortest_transaction":                 0.65
}
```

## change to 3 gthread workers

`siege -c 100 -d 1 -v -t1M https://ip.jackjyq.com/json`

CPU usage is about 35%

```shell
{       "transactions":                         4395,
        "availability":                       100.00,
        "elapsed_time":                        59.05,
        "data_transferred":                     1.59,
        "response_time":                        0.83,
        "transaction_rate":                    74.43,
        "throughput":                           0.03,
        "concurrency":                         61.87,
        "successful_transactions":              4395,
        "failed_transactions":                     0,
        "longest_transaction":                  3.95,
        "shortest_transaction":                 0.65
}
```
