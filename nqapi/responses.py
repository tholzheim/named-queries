from fastapi.responses import Response


class YamlResponse(Response):
    """
    YAML Response
    """

    media_type = "application/yaml"


class CsvResponse(Response):
    """
    CSV Response
    """

    media_type = "text/csv"


class TSVResponse(Response):
    """
    TSV Response
    """

    media_type = "text/tab-separated-values"
