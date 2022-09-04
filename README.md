# dbrep
Package to sync tables across DBs, i.e. EL in ELT/ETL

## What it is
It is tool for loading data from one DB and uploading into another. That is it. It is the simplest EL-tool.

## What it is NOT
- It is NOT orchestrator. You may use existing one, like Airflow, Prefect or Dagster.
- It is NOT data transformation tool. You may use DBT or others.
- It is NOT data ingestion tool -- it won't grab data from external resources.

## Distinctive features
### Simple
It does not try to solve miriad of problems, but nicely fits into existing data-engineering stack with (airflow, dbt and other tools).

### Stateless
It does not store state of jobs or tables, besides connection configs.

### Robust
Since it is stateless there is only a handful of things that could go wrong.

### Type-aware
Types are not lost in translation. I.e. if it was a *number(10,0)* in Oracle, it won't suddenly become a *Float64* in ClickHouse.