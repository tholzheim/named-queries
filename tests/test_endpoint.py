import unittest

from nqapi.endpoints import Endpoints, SparqlEndpoint
from nqapi.resources import Resources


class TestEndpoints(unittest.TestCase):
    """
    test Endpoints
    """

    def test_query(self):
        """
        test querying an endpoint with a named query
        """
        named_query = Resources().get_query_by_name("event_proceedings")
        query_params = {"event_id": "Q112055391", "lang": "en"}
        endpoints = Endpoints.load_endpoints_from_config()
        qres = endpoints.query("qlever", named_query, "csv", query_params=query_params)
        self.assertGreaterEqual(qres.result_size, 17)

    def test_load_endpoints_from_config(self):
        """
        test load_endpoints_from_config
        """
        endpoints = Endpoints.load_endpoints_from_config()
        self.assertGreaterEqual(len(endpoints.endpoints), 2)
        for name, endpoint in endpoints.endpoints.items():
            self.assertIsInstance(endpoint, SparqlEndpoint)
            self.assertEqual(name, endpoint.key)

    def test_unknown_endpoint(self):
        """
        tests if exception is raised if the endpoint is unknown
        """
        endpoints = Endpoints.load_endpoints_from_config()
        named_query = Resources().get_query_by_name("event_proceedings")
        self.assertRaises(Exception, endpoints.query, "unkown", named_query)


if __name__ == "__main__":
    unittest.main()
