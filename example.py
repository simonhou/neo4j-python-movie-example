#!/usr/bin/env python


import json

from bottle import get, run, request, response, static_file
from py2neo import Graph



graph = Graph(  
    "http://127.0.0.1:7474/db/data/",   
    username="neo4j",   
    password="neo4j",bolt=False  
)  


@get("/")
def get_index():
    return static_file("index.html", root="static")


@get("/graph")
def get_graph():
    results = graph.data(
        "MATCH (m:Movie)<-[:ACTED_IN]-(a:Person) "
        "RETURN m.title as movie, collect(a.name) as cast "
        "LIMIT {limit}", {"limit": 100})
    nodes = []
    rels = []
    i = 0
    for movie, cast in results:
        nodes.append({"title": movie, "label": "movie"})
        target = i
        i += 1
        for name in cast:
            actor = {"title": name, "label": "actor"}
            try:
                source = nodes.index(actor)
            except ValueError:
                nodes.append(actor)
                source = i
                i += 1
            rels.append({"source": source, "target": target})
    print nodes
    return {"nodes": nodes, "links": rels}


@get("/search")
def get_search():
    print request.query["q"]
    try:
        q = request.query["q"]
    except KeyError:
        return []
    else:
        results = graph.data(
            "MATCH (movie:Movie) "
            "WHERE movie.title =~ {title} "
            "RETURN movie", {"title": "(?i).*" + q + ".*"})
        response.content_type = "application/json"

        return json.dumps(results)


@get("/movie/<title>")
def get_movie(title):
    results = graph.data(
        "MATCH (movie:Movie {title:{title}}) "
        "OPTIONAL MATCH (movie)<-[r]-(person:Person) "
        "RETURN movie.title as title,"
        "collect([person.name, head(split(lower(type(r)),'_')), r.roles]) as cast "
        "LIMIT 1", {"title": title})
    row = results[0]
    print row['title']
    return {"title": row['title'],
            "cast": [dict(zip(("name", "job", "role"), member)) for member in row['cast']]}


if __name__ == "__main__":
    run(port=8080)
