import json
import unittest
from datetime import datetime
from pathlib import Path

from nqapi.query import NamedQuery, QueryParameter, QueryResult
from nqapi.resources import Resources


class TestNamedQuery(unittest.TestCase):
    def test_named_query_roundtrip(self):
        """
        tests loading and storing a named query
        """
        path = Resources().get_named_query_path("event_proceedings")
        query = NamedQuery.from_yaml(path)
        self.assertIsInstance(query, NamedQuery)
        self.assertEqual(query.name, "event_proceedings")
        self.assertEqual(len(query.parameter), 2)
        for param in query.parameter.values():
            self.assertIsInstance(param, QueryParameter)
            self.assertIsInstance(param.multivalued, bool)

    def test_get_query_render_params(self):
        """
        tests get_query_render_params
        """
        path = Resources().get_named_query_path("event_proceedings")
        query = NamedQuery.from_yaml(path)
        params = {"event_id": "Q123", "lang": "en"}
        expected_params = {"q": "Q123", "lang": "en"}
        actual = query.get_query_render_params(params)
        self.assertDictEqual(actual, expected_params)

    def test_render(self):
        """
        tests test_render
        """
        path = Resources().get_named_query_path("event_proceedings")
        query = NamedQuery.from_yaml(path)
        params = {"event_id": "Q123", "lang": "en"}
        query_str = query.render(params)
        expected_parts = [
            "PREFIX target: <http://www.wikidata.org/entity/Q123>",
            """OPTIONAL{?work rdfs:label ?workLabel. FILTER(lang(?workLabel) = "en")}""",
        ]
        for expected_part in expected_parts:
            self.assertIn(expected_part, query_str)


class TestQueryResult(unittest.TestCase):
    """
    test QueryResult
    """

    def test_post_init(self):
        """
        test __post_init__
        """
        log_str = """{"endpoint": "qlever", "err_msg": null, "error": false, "execution_time": 3.2787322998046875, "query_name": "event_proceedings", "query_params": {"event_id": "Q112055391", "lang": "en"}, "query_version": "0.0.1", "result_size": 17, "timeout": false, "timestamp": "2024-01-26 11:27:09.955090"}"""
        record = json.loads(log_str)
        qr = QueryResult(**record)
        self.assertEqual(qr.endpoint, "qlever")
        self.assertIsInstance(qr.timestamp, datetime)

    def test_to_log_record(self):
        """
        test to_log_record
        """
        log_str = """{"endpoint": "qlever", "err_msg": null, "error": false, "execution_time": 3.2787322998046875, "query_name": "event_proceedings", "query_params": {"event_id": "Q112055391", "lang": "en"}, "query_version": "0.0.1", "result_size": 17, "timeout": false, "timestamp": "2024-01-26 11:27:09.955090"}"""
        record = json.loads(log_str)
        qr = QueryResult(**record)
        # set query result and expect removal for query log
        qr.result = "item,itemLabel\nQ5,human"
        actual_log_str = qr.to_log_record()
        self.assertEqual(actual_log_str, log_str)


if __name__ == "__main__":
    unittest.main()
