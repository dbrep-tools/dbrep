"""
We have several layers of abstraction:

1. Test driver (src & dst) - it should not be visible in pytest report at all
2. Engine (src & dst) - it should be visible in pytest report
3. Different DBs (src & dst) - it may or may not be visible in pytest report
4. Different configs - it may not be visible in pytest report
5. Different use cases - it may not be visible in pytest report

Hence:
1. Test driver should be determined based on test definition (basically two of them: SQLA and Kafka).
    - Must be hidden
    - Must handle clean-up
2. Engine - make test_engine2engine.py file
3. Different DBs - may be parameters to actual docker-compose.yaml file 

Must decouple DB state from Engine.
SRC/DST -> only one Test Driver -> many Engines

PGTemplate:
    driver: postgres
    setup:
        - create table ()
    dst:
        - driver: ch
          setup: []
          params: []

templates: [PGTemplate, CHTemplate, etc.]
steps:
 - insert into values

template: PGTemplate
steps:
 - insert into values

Test-case:
    driver: actual-DB (e.g. ClickHouse, Postgres or Kafka => driver)
    steps: [a, b, c, d]
    configs: #possible Engines
        - conn: a
          params: ...
    dst:
        driver: actual-DB
        steps: [a, b, c, d]
        configs: #possible Engines
            - conn: a
              params: ...

Test:
    src-driver: SQLAlchemy/Kafka + actual connection string
    dst-driver: SQLAlchemy/Kafka + actual connection string
    src-conn: A
    dst-conn: B
    #test_A_to_B.py -> single fixtures
    src-config: ...
    dst-config: ...

test_incremental
test_full_refresh
test_infer_incremental
test_infer_full_refresh

1 step: create explicit tests
2 step: create src -> dst structure
3 step: create templates

Expected output:
TEST[engine-name@DB, engine-name@DB, test-name]: output
TEST[engine-name@DB, engine-name@DB]: tests

.csv file with full table
"""


import sys
import logging

from config import read_test_configs
import runner

logFormatter = logging.Formatter("%(asctime)s [%(levelname)-5.5s]  %(message)s")
logger = logging.getLogger()
consoleHandler = logging.StreamHandler(stream=sys.stdout)
consoleHandler.setFormatter(logFormatter)
logger.addHandler(consoleHandler)
logger.setLevel(logging.CRITICAL)

if __name__ == '__main__':
    test_config = read_test_configs()
    result = runner.run_tests(test_config)
    logger.debug('Finished testing')