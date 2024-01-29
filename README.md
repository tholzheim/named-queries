# Named Query API (nqapi)

# Starting the server

```shell
uvicorn nqapi.webserver:app --reload
```

# Named Query
The specification of a named query provides a structured description of a parametrized SPARQL Query.
Example:
```yaml
name: instances_of_entity_class
description:
  Get all scholarly articles published as proceedings of the given event
version: 0.0.2
parameter:
  event_id:
      label: q
      type: Qid
      description: Wikidata id of the event
  lang:
    label: lang
    type: str
    default_value: en
    description: language of the labels that are queried

query: |
  PREFIX target: <http://www.wikidata.org/entity/{{ q }}> 
  PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> 
  PREFIX wdt: <http://www.wikidata.org/prop/direct/> 
  SELECT ?item
  WHERE{
    ?item wdt:P31 target: .
  }
```

# Execution Modi

* Auto: Select the best fitting endpoint
* Voting: Execute on all endpoints and compare results or variants
* Fastest: Use fastest endpoint
* Recent: Use endpoint with the most recent data (max age)
* Forced: Only use one endpoint e.g. selected by user, forced by query definition
* Cached: if cache available use it otherwise execute query and store as cache
* greenest: minimize carbon footprint
