import inspect
import logging
from typing import Annotated, Any, Callable, Dict, List, Optional, Union

from fastapi import Body, FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from starlette.responses import RedirectResponse

from nqapi.endpoints import Endpoints
from nqapi.exceptions import EndpointUnknown
from nqapi.query import NamedQuery
from nqapi.query_stats import NamedQueryMetadata
from nqapi.resources import Resources
from nqapi.responses import CsvResponse, TSVResponse, YamlResponse

logger = logging.getLogger(__name__)


known_types = {
    "int": int,
    "float": float,
    "str": str,
    "Qid": Annotated[
        Optional[str],
        Query(
            min_length=2,
            pattern=r"^Q[1-9]\d*$",
            title="Qid",
            description="Wikidata item identifier",
            examples=["Q5", "Q43649390"],
        ),
    ],
    "Pid": Annotated[
        Optional[str],
        Query(
            min_length=2,
            pattern=r"^P[1-9]\d*$",
            title="Pid",
            description="Wikidata property identifier",
            examples=["P31", "P179"],
        ),
    ],
}


app = FastAPI()
resources = Resources()


@app.get("/query")
async def get_all_named_queries():
    """
    Get names of all queries
    """
    query_names = resources.get_all_named_queries()
    return JSONResponse(query_names)


@app.post("/query/{name}")
async def get_query(
    name: str, query_params: Annotated[Dict[Any, Any], Body(default_factory=dict)]
):
    """
    Get query by name
    """
    named_query = resources.get_query_by_name(name)
    if named_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    query = named_query.render(query_params)
    return PlainTextResponse(query)


@app.post("/query/{name}/exec")
async def execute_query(
    name: str,
    endpoint: str = "wdqs",
    result_format: str = "json",
    query_params: Optional[Dict[str, Any]] = None,
):
    """
    Get query by name
    """
    named_query = resources.get_query_by_name(name)
    if named_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    return _execute_query(named_query, endpoint, result_format, query_params)


@app.get("/query/{name}/stats")
async def get_named_query_statistics(name: str) -> JSONResponse:
    """
    Get query statistics by name
    """
    named_query = resources.get_query_by_name(name)
    if named_query is None:
        raise HTTPException(status_code=404, detail="Query not found")
    log_file = resources.get_named_query_stats_path(name)
    query_metadata = NamedQueryMetadata.load_statistics_from(name, log_file)
    res = jsonable_encoder(query_metadata.get_record())
    return JSONResponse(res)


@app.get("/query/{name}/spec")
async def get_named_query_specification(name: str) -> YamlResponse:
    """
    Get query statistics by name
    """
    path = resources.get_named_query_path(name)
    with open(path, mode="r") as f:
        yaml_str = f.read()
    return YamlResponse(yaml_str)


@app.get("/", include_in_schema=False)
async def home() -> RedirectResponse:
    """
    Get query statistics by name
    """
    return RedirectResponse(url="/docs")


def add_endpoint_for_query(query: NamedQuery):
    """
    Add endpoint for given query
    """
    # query
    app.add_api_route(
        path="/query/" + query.name,
        endpoint=get_query_callback(query),
        name=query.name,
        description=query.description,
        response_class=PlainTextResponse,
        tags=["Query"],
    )
    # result
    app.add_api_route(
        path="/exec/" + query.name,
        endpoint=get_query_exec_callback(query),
        name=query.name,
        description=query.description,
        response_class=PlainTextResponse,
        tags=["Query Result"],
    )


def add_endpoints(limit_to: Optional[List[str]] = None):
    """
    Add endpoints for all named queries
    """
    if limit_to is None:
        limit_to = []
    query_names = resources.get_all_named_queries()
    for name in query_names:
        if limit_to and name not in limit_to:
            continue
        query = resources.get_query_by_name(name)
        if query is None:
            logger.debug(f"Query {query} is known but can not be loaded")
            continue
        add_endpoint_for_query(query)


def get_query_callback(query: NamedQuery) -> Callable:
    """
    see https://stackoverflow.com/questions/73291228/add-route-to-fastapi-with-custom-path-parameters
    """

    args = _get_kwargs_for_query(query)

    def fn_callback(**kwargs):
        res = query.render(query_params=kwargs)
        # ToDo: Log query generation
        return PlainTextResponse(res)

    params = []
    for param, type_ in args.items():
        query_parameter = query.parameter.get(param, None)
        default: Union[str, type] = inspect.Parameter.empty
        if query_parameter:
            if query_parameter.default_value:
                default = query_parameter.default_value
        param_definition = inspect.Parameter(
            param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=type_,
            default=default,
        )
        params.append(param_definition)
    fn_callback.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined, misc]
    fn_callback.__annotations__ = args
    return fn_callback


def get_query_exec_callback(query: NamedQuery) -> Callable:
    """
    see https://stackoverflow.com/questions/73291228/add-route-to-fastapi-with-custom-path-parameters
    """
    args = _get_kwargs_for_query(query)
    args["endpoint"] = str
    args["result_format"] = str

    def fn_callback(endpoint: str, result_format: str, **kwargs):
        return _execute_query(
            query=query, endpoint=endpoint, _format=result_format, query_params=kwargs
        )

    params = []
    for param, type_ in args.items():
        query_parameter = query.parameter.get(param, None)
        default: Union[str, type] = inspect.Parameter.empty
        if query_parameter:
            if query_parameter.default_value:
                default = query_parameter.default_value
        else:
            if param == "result_format":
                default = "json"
            elif param == "endpoint":
                default = "wdqs"
        param_definition = inspect.Parameter(
            param,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            annotation=type_,
            default=default,
        )

        params.append(param_definition)
    fn_callback.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined, misc]
    fn_callback.__annotations__ = args
    return fn_callback


def _execute_query(
    query: NamedQuery,
    endpoint: str,
    _format: str,
    query_params: Optional[Dict[str, Any]] = None,
) -> Response:
    endpoints = Endpoints.load_endpoints_from_config()
    try:
        qres = endpoints.query(
            endpoint=endpoint,
            query=query,
            result_format=_format,
            query_params=query_params,
        )
    except EndpointUnknown as e:
        raise HTTPException(status_code=404, detail=e.msg)
    resources.save_query_log(qres)
    response: Response
    if qres.result:
        if _format.lower() == "json":
            response = JSONResponse(qres.result)
        elif _format.lower() == "csv":
            response = CsvResponse(qres.result)
        elif _format.lower() == "tsv":
            response = TSVResponse(qres.result)
        else:
            response = JSONResponse(qres.result)
    elif qres.timeout:
        response = Response(
            status_code=504, content="SPARQL endpoint timeout when executing the query"
        )
    elif qres.error:
        response = Response(status_code=500, content=qres.err_msg)
    else:
        response = Response(qres)
    return response


def _get_kwargs_for_query(query: NamedQuery) -> Dict[str, Any]:
    """
    Generate the mapping of argument and expected type for given query
    """
    args = {}
    for name, param in query.parameter.items():
        param_type = known_types.get(param.type, str)
        if param.multivalued:
            if isinstance(param_type, type):
                param_type = Annotated[List[param_type], Query()]  # type: ignore[valid-type, misc]
        args[name] = param_type
    return args


add_endpoints(
    ["author_topics", "event_proceedings", "publisher_editors", "works_topics"]
)
