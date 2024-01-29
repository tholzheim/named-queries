import json
import statistics
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from nqapi.query import QueryResult


@dataclass
class NamedQueryMetadata:
    """
    Access metadata of a named query
    """

    query_name: str
    execution_stats: Dict[str, "QueryExecutionMetadata"] = field(default_factory=dict)

    def __post_init__(self):
        for endpoint, stats in self.execution_stats.items():
            if isinstance(stats, dict):
                self.execution_stats[endpoint] = QueryExecutionMetadata(**stats)

    @classmethod
    def load_statistics_from(cls, query_name: str, path: Path) -> "NamedQueryMetadata":
        """
        Load query statistics from given path
        """
        meta = NamedQueryMetadata(query_name)
        if path.exists() and path.is_file():
            with open(path, mode="r") as log_file:
                for line in log_file.readlines():
                    record = json.loads(line)
                    qres = QueryResult(**record)
                    meta._add_query_result(qres)
        return meta

    def _add_query_result(self, qres: "QueryResult"):
        if qres.endpoint not in self.execution_stats:
            self.execution_stats[qres.endpoint] = QueryExecutionMetadata(
                endpoint=qres.endpoint
            )
        exec_stats = self.execution_stats[qres.endpoint]
        exec_stats.update_stats(qres)

    @classmethod
    def from_json(cls, path: Path) -> "NamedQueryMetadata":
        """
        Load the named query from given file
        """
        if path.exists():
            with open(path, mode="r") as f:
                record = json.load(f)
            query_metadata = NamedQueryMetadata(**record)
            return query_metadata
        else:
            return NamedQueryMetadata(path.stem)

    def as_json(self) -> str:
        """
        Convert to yaml
        """
        res = json.dumps(asdict(self), indent=4)
        return res

    def get_record(self) -> dict:
        record = asdict(self)
        for key, value in self.execution_stats.items():
            record["execution_stats"][key][
                "median_execution_time"
            ] = value.median_execution_time
            record["execution_stats"][key][
                "median_result_size"
            ] = value.median_result_size
        return record

    def safe_to_json(self, path: Path):
        """
        safe content as yaml file at given location
        """
        with open(path, mode="w") as f:
            f.write(self.as_json())

    def update_stats(self, query_result: "QueryResult"):
        exec_metadata = self.execution_stats.get(query_result.endpoint, None)
        if exec_metadata is None:
            exec_metadata = QueryExecutionMetadata(query_result.endpoint)
        self.execution_stats[query_result.endpoint] = exec_metadata
        exec_metadata.update_stats(query_result)


@dataclass
class QueryExecutionMetadata:
    """
    Metadata about the execution of a query
    """

    endpoint: str
    no_executions: int = 0
    no_successes: int = 0
    no_timeouts: int = 0
    no_errors: int = 0
    execution_times: List[float] = field(default_factory=list)
    result_sizes: List[int] = field(default_factory=list)

    @property
    def median_execution_time(self) -> Optional[float]:
        values = [value for value in self.execution_times if value is not None]
        median = statistics.median(values) if values else None
        return median

    @property
    def median_result_size(self) -> Optional[float]:
        values = [value for value in self.result_sizes if value is not None]
        median = statistics.median(values) if values else None
        return median

    def update_stats(self, qres: "QueryResult"):
        self.no_executions += 1
        if qres.error:
            self.no_errors += 1
        if qres.timeout:
            self.no_timeouts += 1
        if not (qres.timeout or qres.error):
            self.no_successes += 1
            if qres.execution_time:
                self.execution_times.append(qres.execution_time)
            if qres.result_size:
                self.result_sizes.append(qres.result_size)
