from __future__ import annotations

from datetime import datetime

try:
    from airflow import DAG
    from airflow.operators.python import PythonOperator
except Exception:
    DAG = None
    PythonOperator = None


def refresh_materialized_views() -> str:
    import os
    import psycopg
    with psycopg.connect(os.getenv("DATABASE_URL", "postgresql://earningsiq:earningsiq@localhost:5432/earningsiq")) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT refresh_all_materialized_views();")
    return "refreshed"


if DAG is not None and PythonOperator is not None:
    with DAG(
        dag_id="earningsiq_daily_refresh",
        start_date=datetime(2026, 1, 1),
        schedule="@daily",
        catchup=False,
        tags=["earningsiq", "sql"],
    ) as dag:
        PythonOperator(task_id="refresh_materialized_views", python_callable=refresh_materialized_views)
