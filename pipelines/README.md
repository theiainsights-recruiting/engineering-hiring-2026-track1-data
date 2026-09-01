# pipelines

Stages of the nightly document ingest DAG. Each module is one stage;
stages read and write dated parquet partitions under the shared data root.
