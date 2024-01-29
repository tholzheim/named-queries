from typing import List, Optional


class EndpointUnknown(Exception):
    """
    Endpoint is unknown
    """

    msg = "Endpoint is unknown"

    def __init__(
        self,
        unknown_endpoint: str,
        known_endpoints: Optional[List[str]] = None,
        **kwargs,
    ):
        super.__init__(**kwargs)
        self.msg = f"Endpoint with the name {unknown_endpoint} is not known."
        if known_endpoints:
            self.msg += f" The endpoint must be one of: {known_endpoints}"
