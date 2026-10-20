"""DuckDB access layer.

The API is read-only. A single in-memory DuckDB connection registers a view over the
Parquet warehouse. Queries are serialized with a lock because DuckDB connections are not
meant to be shared across concurrent threads without coordination.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any, Sequence

import duckdb
import pandas as pd


class Database:
    def __init__(self, parquet_path: Path) -> None:
        if not parquet_path.exists():
            raise FileNotFoundError(
                f"Warehouse not found at {parquet_path}. Run `make warehouse` first."
            )
        self.parquet_path = parquet_path
        self._lock = threading.Lock()
        self._connection = duckdb.connect(database=":memory:")
        escaped = str(parquet_path).replace("'", "''")
        self._connection.execute(
            f"CREATE OR REPLACE VIEW detentions AS "
            f"SELECT * FROM read_parquet('{escaped}')"
        )

    def query(self, sql: str, params: Sequence[Any] | None = None) -> list[dict[str, Any]]:
        with self._lock:
            frame: pd.DataFrame = self._connection.execute(
                sql, list(params or [])
            ).fetchdf()
        return _records(frame)

    def query_one(
        self, sql: str, params: Sequence[Any] | None = None
    ) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def close(self) -> None:
        with self._lock:
            self._connection.close()


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for row in frame.to_dict(orient="records"):
        clean: dict[str, Any] = {}
        for key, value in row.items():
            if pd.isna(value):
                clean[key] = None
            elif hasattr(value, "isoformat"):
                clean[key] = value.isoformat()
            elif hasattr(value, "item"):
                clean[key] = value.item()
            else:
                clean[key] = value
        records.append(clean)
    return records
