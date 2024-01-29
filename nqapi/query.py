import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from dateutil.parser import parse
from jinja2 import BaseLoader, Environment


@dataclass
class QueryParameter:
    """
    query parameter
    """

    label: str
    type: Any
    description: str
    default_value: Optional[str] = None
    multivalued: bool = False

    def __post_init__(self):
        """
        Sanitize set properties
        """
        if not isinstance(self.multivalued, bool):
            self.multivalued = self.multivalued == "True"


@dataclass
class NamedQuery:
    """
    named query
    """

    name: str
    query: str
    version: str = "0.0.1"
    description: Optional[str] = None
    parameter: Dict[str, QueryParameter] = field(default_factory=dict)

    def __post_init__(self):
        """
        Sanitize set properties
        """
        if self.parameter:
            for name, parameter in self.parameter.items():
                if isinstance(parameter, dict):
                    query_parameter = QueryParameter(**parameter)
                    self.parameter[name] = query_parameter

    @classmethod
    def from_yaml(cls, path: Path) -> Optional["NamedQuery"]:
        """
        Load the named query from given file
        """
        query = None
        if path.exists():
            with open(path, mode="r") as f:
                record = yaml.safe_load(f)
            query = NamedQuery(**record)
        return query

    def render(
        self, query_params: Optional[Dict[str, Any]] = None, map_to_label: bool = True
    ) -> str:
        """
        Render the query with the given parameter
        """
        if query_params is None:
            query_params = {}
        if map_to_label:
            query_params = self.get_query_render_params(query_params)
        template = Environment(loader=BaseLoader()).from_string(self.query)
        res = template.render(**query_params)
        return res

    def get_query_render_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert the query parameter to the render parameter
        """
        param_label_lut = {name: param.label for name, param in self.parameter.items()}
        query_args = {
            param_label_lut.get(key, key): value for key, value in params.items()
        }
        return query_args

    def as_yaml(self) -> str:
        """
        Convert to yaml
        """
        res = yaml.dump(asdict(self), default_style=">")
        return res


@dataclass
class QueryResult:
    """
    Query result
    """

    query_name: str
    endpoint: str
    timestamp: datetime
    query_version: str
    query_params: Optional[Dict[str, Any]] = field(default_factory=dict)
    result: Optional[Any] = None
    execution_time: Optional[float] = None
    result_size: Optional[int] = None
    timeout: bool = False
    error: bool = False
    err_msg: Optional[str] = None

    def __post_init__(self):
        if isinstance(self.timestamp, str):
            self.timestamp = parse(self.timestamp)
        if self.query_params is None:
            self.query_params = dict()

    def to_log_record(self) -> str:
        """
        convert query result to log line
        """
        record = asdict(self)
        record.pop("result")
        log_line = json.dumps(record, sort_keys=True, default=str)
        return log_line
