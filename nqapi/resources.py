from pathlib import Path
from typing import List, Optional

from nqapi.query import NamedQuery, QueryResult


class Resources:
    """
    Handles the resource files
    """

    def __init__(self, root_dir: Optional[Path] = None):
        if root_dir is None:
            root_dir = Path(__file__).parent.joinpath("resources")
        self.root_dir = root_dir

    def get_named_query_directory(self) -> Path:
        """
        return path of the named query directory
        """
        return self.root_dir.joinpath("queries")

    def get_named_query_logs_directory(self) -> Path:
        """
        return path of the named query directory
        """
        return self.root_dir.joinpath("stats")

    def get_named_query_stats_path(self, name: str) -> Path:
        """
        Return path for the named query statistics
        """
        path = self.get_named_query_logs_directory()
        query_path = path.joinpath(f"{name}.json")
        return query_path

    def get_named_query_path(self, name: str) -> Path:
        """
        Return path for the named query
        """
        path = self.get_named_query_directory()
        query_path = path.joinpath(f"{name}.yaml")
        return query_path

    def get_query_by_name(self, name: str) -> Optional[NamedQuery]:
        """
        Get NamedQuery by name
        """
        query_path = self.get_named_query_path(name)
        if query_path.is_file():
            query = NamedQuery.from_yaml(query_path)
        else:
            query = None
        return query

    def get_all_named_queries(self) -> List[str]:
        """
        Get list of all names of named queries
        """
        named_query_dir = self.get_named_query_directory()
        query_names = []
        for entry in named_query_dir.iterdir():
            if entry.is_file():
                query_names.append(entry.stem)
        return query_names

    def get_endpoint_config_path(self):
        """
        returns the config path for endpoints
        """
        path = self.root_dir.joinpath("endpoints.yaml")
        return path

    def save_query_log(self, query_result: QueryResult):
        """
        Save the given query result by appending the query result to the log file of the corresponding query
        """
        log_file = self.get_named_query_stats_path(query_result.query_name)
        log_line = query_result.to_log_record()
        with open(log_file, mode="a") as f:
            f.write(f"{log_line}\n")
