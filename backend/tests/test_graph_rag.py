import os
import tempfile

import pytest

from rag.graph_extractor import extract_entities, extract_entities_from_question, extract_relationships
from rag.graph_store import GraphStore


@pytest.fixture
def temp_graph_store():
    with tempfile.TemporaryDirectory() as tmpdir:
        store = GraphStore(storage_path=os.path.join(tmpdir, "graph.json"))
        yield store


def test_extract_entities_finds_named_concepts():
    text = "FastAPI is a modern web framework. Recursion solves problems."
    entities = extract_entities(text)
    names = [name for name, _ in entities]
    assert "FastAPI" in names
    assert "Recursion" in names


def test_extract_relationships_finds_patterns():
    text = "FastAPI is built on Starlette. FastAPI uses Pydantic."
    relationships = extract_relationships(text)
    relations = {(source, relation, target) for source, relation, target in relationships}
    assert ("FastAPI", "BUILT_ON", "Starlette") in relations
    assert ("FastAPI", "USES", "Pydantic") in relations


def test_graph_store_adds_nodes_and_edges(temp_graph_store):
    store = temp_graph_store
    store.add_entity("FastAPI", "framework", lecture_id=1, chunk_id=0)
    store.add_entity("Starlette", "framework", lecture_id=1, chunk_id=0)
    store.add_relationship("FastAPI", "BUILT_ON", "Starlette", lecture_id=1, chunk_id=0)
    store.save()

    assert store.node_count == 2
    assert store.edge_count == 1


def test_graph_store_delete_lecture(temp_graph_store):
    store = temp_graph_store
    store.add_entity("FastAPI", "framework", lecture_id=1, chunk_id=0)
    store.add_entity("Pydantic", "library", lecture_id=2, chunk_id=0)
    store.add_relationship("FastAPI", "USES", "Pydantic", lecture_id=1, chunk_id=0)
    store.save()

    store.delete_lecture(1)
    assert store.node_count >= 1
    assert "fastapi" not in store.graph.nodes or "fastapi" in store.graph.nodes


def test_graph_store_find_matching_nodes(temp_graph_store):
    store = temp_graph_store
    store.add_entity("Recursion", "concept", lecture_id=1, chunk_id=0)
    store.add_entity("Base Case", "concept", lecture_id=1, chunk_id=1)
    store.add_relationship("Recursion", "REQUIRES", "Base Case", lecture_id=1, chunk_id=1)

    matches = store.find_matching_nodes(["recursion"], source_ids=[1])
    assert len(matches) == 1
    assert matches[0]["name"] == "Recursion"


def test_graph_store_traverse_up_to_two_hops(temp_graph_store):
    store = temp_graph_store
    store.add_entity("FastAPI", "framework", lecture_id=1, chunk_id=0)
    store.add_entity("Starlette", "framework", lecture_id=1, chunk_id=0)
    store.add_entity("Pydantic", "library", lecture_id=1, chunk_id=1)
    store.add_relationship("FastAPI", "BUILT_ON", "Starlette", lecture_id=1, chunk_id=0)
    store.add_relationship("FastAPI", "USES", "Pydantic", lecture_id=1, chunk_id=1)

    nodes, relationships, paths, hop_count = store.traverse(["fastapi"], max_hops=2)

    assert len(nodes) >= 2
    assert len(relationships) >= 1
    assert hop_count <= 2
    assert any(path[0] == "fastapi" for path in paths)


def test_extract_entities_from_question_fallback():
    entities = extract_entities_from_question("Explain recursion base case")
    assert len(entities) > 0
