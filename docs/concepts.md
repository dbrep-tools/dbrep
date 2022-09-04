# Concept
## Core job
1. Load data from source DB/MQ
2. Upload data to destination DB/MQ
3. That is it


It supports 2 modes of work:
- **Full-refresh** - truncate destination, load every record from source
- **Incremental** - find latest *RID* in **Destination**, load increment from **Source**, insert into **Destination**

Note, that this tool **DOES NOT** support update of existing records by incremental RID (i.e. PK and RID are different fields and RID indicates updates to rows). Main reason: it is post-transform, which should be performed by responsible tool.

## Responsibility separation
This package is **NOT** responsible for:
- orchestration (you may use Airflow, Prefect, Dagster or any other)
- data transformation (you may use DBT)
- change data capture
- integration with external resources
- data bus (but may be used to communicate with one)

## Stateless
This tool does not store state besides connection configuration. Everything is deduced based on current state of source and destination storage.

## Retriable errors
Any error happening during workflow can be solved by retrying.

# Architecture

## Key entities
On the other hand it focuses on incremental updates of data marts. Hence there is several key concepts:
- **Source** - connection to source data base (or message queue)
- **Destination** - connection to destination data base (or message queue)
- **Config** - config for establishing connection with src or dst

## Connection config
Design concepts:
- make it secure
- make it interoperable with orchestrators like Airflow
- make it simple
- make it overrideable

Basic config will consist of following entries:
- **engine** -- what engine to use (e.g. sqlalchemy, clickhouse, kafka)
- **user** / **password** -- should be securely stored
- **config** -- more or less individual to each engine

## Source
Implements method *features()* which can contain:
- **incremental**
- **full-refresh** (e.g. not supported for Kafka)

## Destination
Implements method *features()* which can contain:
- **incremental**
- **full-refresh**

## Replication
Describes connection between two tables:
- **Source** -- source connection
- **Destination** -- destination connection
- **Mode** -- full-refresh or incremental
- **Config**
- **Typing**