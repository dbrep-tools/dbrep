# Performance testing results

## SQL with single column on 1 million records

Table preview:
| rid | col |
|-----|-----|

| Solution  | Method                  | Time  | Comment  |
|-----------|-------------------------|-------|----------|
| custom    | pandas                  | 24s   |   |
| dbrep     | sqlalchemy, full-copy   | 33s   |   |
| dbrep     | sqlalchemy, incremental | 35s   |   |
| dbrep     | pg-copy, full-copy      | TBD   |   |
| dbrep     | pg-copy, incremental    | TBD   |   |
| airbyte   | full refresh            | 500s+ |   |
| NiFi      | incremental             | TBD   |   |

Airbyte docker compose: https://github.com/airbytehq/airbyte/blob/master/docker-compose.yaml
NiFi docker compose: 

## SQL with single column on 100 million records