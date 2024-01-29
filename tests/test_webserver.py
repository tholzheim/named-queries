import unittest

import yaml
from fastapi.testclient import TestClient

from nqapi.webserver import app


class TestWebserver(unittest.TestCase):
    """
    test webserver
    """

    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_get_all_named_queries(self):
        """
        test get_all_named_queries
        """
        response = self.client.get("/query")
        self.assertEqual(response.status_code, 200)
        query_names = response.json()
        self.assertGreaterEqual(len(query_names), 200)
        self.assertIn("event_proceedings", query_names)

    def test_get_query(self):
        """
        test get_query
        """
        query_params = {"event_id": "Q112055391", "lang": "en"}
        response = self.client.post("/query/event_proceedings", json=query_params)
        self.assertEqual(response.status_code, 200)
        query = response.content.decode()
        expected_parts = [
            "PREFIX target: <http://www.wikidata.org/entity/Q112055391>",
            """OPTIONAL{?work rdfs:label ?workLabel. FILTER(lang(?workLabel) = "en")}""",
        ]
        for expected_part in expected_parts:
            self.assertIn(expected_part, query)

    def test_unknown_query(self):
        """
        test get_query with unknown query
        """
        query_params = {"event_id": "Q112055391", "lang": "en"}
        responses = {
            "/query/unknown": self.client.post("/query/unknown", json=query_params),
            "/query/unknown/stats": self.client.get("/query/unknown/stats"),
            "/query/unknown/exec": self.client.post(
                "/query/unknown/exec", json=query_params
            ),
        }
        for route, response in responses.items():
            with self.subTest(route):
                print(route)
                self.assertEqual(response.status_code, 404)
                self.assertEqual(response.json().get("detail"), "Query not found")

    def test_get_named_query_statistics(self):
        """
        test get_named_query_statistics
        """
        response = self.client.get("/query/event_proceedings/stats")
        self.assertEqual(response.status_code, 200)
        record = response.json()
        self.assertEqual(record.get("query_name", None), "event_proceedings")

    def test_get_named_query_specification(self):
        """
        test get_named_query_specification
        """
        response = self.client.get("/query/event_proceedings/spec")
        self.assertEqual(response.status_code, 200)
        record = yaml.safe_load(response.content)
        self.assertEqual(record.get("name", None), "event_proceedings")

    def test_execute_query(self):
        """
        test execute_query
        """
        query_params = {"event_id": "Q112055391", "lang": "en"}
        response = self.client.post(
            "/query/event_proceedings/exec",
            params={"endpoint": "qlever", "result_format": "json"},
            json=query_params,
        )
        record = response.json()
        print(record)


if __name__ == "__main__":
    unittest.main()
