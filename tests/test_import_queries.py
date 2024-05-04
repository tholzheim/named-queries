import unittest
import urllib.request
import zipfile
from pathlib import Path

import yaml

from nqapi.query import NamedQuery
from tempfile import TemporaryDirectory


class MyTestCase(unittest.TestCase):
    @unittest.skip("Only execute if the queries should be regenerated")
    def test_something(self):
        with TemporaryDirectory() as tmpdir:
            git_archive = "https://github.com/WDscholia/scholia/archive/refs/heads/master.zip"
            path = Path(tmpdir)
            zip_file = path.joinpath("master.zip")
            urllib.request.urlretrieve(git_archive, path.joinpath("master.zip"))
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(tmpdir)
            query_path = path.joinpath("scholia-master", "scholia/app/templates")
            exclude = ["author_topics", "event_proceedings", "publisher_editors", "works_topics", ]
            for entry in query_path.iterdir():
                if entry.is_file():
                    if entry.suffix == ".sparql":
                        name = entry.stem
                        if name in exclude:
                            continue
                        with open(entry, mode="r") as f:
                            query_str = f.read()
                        query = NamedQuery(name=name, query=query_str)
                        target = Path(__file__).parent.parent.joinpath(
                            "nqapi", "resources", "queries", f"{name}.yaml"
                        )
                        with open(target, mode="w") as f:
                            f.write(yaml.dump({"name": name, "query": query_str}))


if __name__ == "__main__":
    unittest.main()
