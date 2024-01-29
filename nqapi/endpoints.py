import datetime
import time
from http.client import IncompleteRead
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from SPARQLWrapper import SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import EndPointInternalError, QueryBadFormed

from nqapi.exceptions import EndpointUnknown
from nqapi.query import NamedQuery, QueryResult
from nqapi.resources import Resources


class SparqlEndpoint:
    """
    SPARQL Endpoint interface
    """

    def __init__(
        self,
        name: str,
        key: str,
        endpoint_url: str,
        description: Optional[str],
        homepage: Optional[str],
    ):
        """
        constructor
        Args:
            name: name of the endpoint
            endpoint_url: endpoint url
            description: description of the endpoint
            homepage: homepage of the endpoint
        """
        self.name = name
        self.key = key
        self.endpoint_url = endpoint_url
        self.description = description
        self.homepage = homepage

    def query(
        self,
        query: NamedQuery,
        result_format: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        execute given query
        """
        query_str = query.render(query_params=query_params)
        wrapper = SPARQLWrapper(self.endpoint_url)
        wrapper.setQuery(query_str)
        if isinstance(result_format, str):
            wrapper.setReturnFormat(result_format)
        else:
            result_format = wrapper.returnFormat
        wrapper.setOnlyConneg(True)
        query_result = QueryResult(
            query_name=query.name,
            query_params=query_params,
            endpoint=self.key,
            timestamp=datetime.datetime.now(),
            query_version=query.version,
        )
        try:
            start = time.time()
            qres = wrapper.query()
            res = (
                qres.convert()
            )  # ToDo: Check execution again. Early observations showed that Timeout issues only occured on converting the query
            end = time.time()
            query_result.execution_time = end - start
            query_result.result = res
            query_result.result_size = self._count_results(res, result_format)
        except QueryBadFormed as e:
            query_result.error = True
            query_result.err_msg = e.msg
        except (IncompleteRead, EndPointInternalError) as e:
            query_result.timeout = True
            msg = str(e)
            if isinstance(e, EndPointInternalError):
                msg = e.msg
            query_result.err_msg = msg
        except Exception as e:
            query_result.error = True
            query_result.err_msg = str(e)
        return query_result

    @classmethod
    def _count_results(cls, result: Any, result_format: str):
        count = None
        if result_format == "json":
            count = len(result.get("results", {}).get("bindings", {}))
        elif result_format == "csv":
            count = len(result.decode().strip().split("\n")) - 1
        elif result_format == "tsv":
            count = len(result.decode().strip().split("\n")) - 1
        return count


class Endpoints:
    """
    Holds multiple SPARQL endpoints
    """

    def __init__(self, endpoints: Dict[str, SparqlEndpoint]):
        """
        constructor
        """
        self.endpoints = endpoints

    def get_by_name(self, name: str) -> Optional[SparqlEndpoint]:
        """
        Get endpoint by name
        """
        return self.endpoints.get(name, None)

    def query(
        self,
        endpoint: str,
        query: NamedQuery,
        result_format: Optional[str] = None,
        query_params: Optional[Dict[str, Any]] = None,
    ) -> QueryResult:
        """
        execute given query
        """
        sparql_endpoint = self.get_by_name(endpoint)
        if sparql_endpoint is None:
            raise EndpointUnknown(endpoint, list(self.endpoints.keys()))
        res = sparql_endpoint.query(
            query, result_format=result_format, query_params=query_params
        )
        return res

    @classmethod
    def load_endpoints_from_config(cls, path: Optional[Path] = None) -> "Endpoints":
        """
        Load endpoints from config file
        Args:
            path: location of config file to load
        Returns:
            endpoints
        """
        if path is None:
            path = Resources().get_endpoint_config_path()
        with open(path, mode="r") as f:
            records = yaml.safe_load(f)
        endpoints = dict()
        for key, endpoint_record in records.get("endpoints").items():
            endpoint = SparqlEndpoint(**endpoint_record)
            endpoints[endpoint.key] = endpoint
        return Endpoints(endpoints)
