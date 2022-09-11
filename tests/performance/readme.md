# Performance testing results

## SQL with single column

#### Setup

Postgre instance on VM with 16GB RAM and 4 vCPU

Table preview:
| rid | col    |
|-----|--------|
| 1   | 1234567|
| 2   | abcdefg|

#### Results

| Solution  | Method                  | 1 MLN | 10 MLN  |
|-----------|-------------------------|-------|---------|
| dbrep     | sqlalchemy, full-copy   | 12s   |    134s |
| dbrep     | dbapi, full-copy        | 7s    |     69s |
| dbrep     | pg-copy, full-copy      | 3s    |     38s |
| custom    | pandas                  | 12s   |    128s |
| airbyte   | full refresh            | 100s  | NA      |
| NiFi      | 1 thread, avro          | 12s   |         |

Airbyte docker compose: https://github.com/airbytehq/airbyte/blob/master/docker-compose.yaml
NiFi via docker run