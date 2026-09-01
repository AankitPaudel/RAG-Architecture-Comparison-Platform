import json
import logging
import os
from typing import Dict, List, Optional, Set, Tuple

import networkx as nx

from app.config import settings

logger = logging.getLogger(__name__)


class GraphStore:
    """Lightweight knowledge graph backed by NetworkX with JSON persistence."""

    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path or os.path.join(
            settings.VECTOR_STORE_PATH, "knowledge_graph.json"
        )
        self.graph = nx.MultiDiGraph()
        self._load()

    def _load(self) -> None:
        if not os.path.exists(self.storage_path):
            return
        try:
            with open(self.storage_path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.graph = nx.node_link_graph(payload, directed=True, multigraph=True, edges="links")
        except Exception as error:
            logger.warning("Could not load graph store: %s", error)
            self.graph = nx.MultiDiGraph()

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        payload = nx.node_link_data(self.graph, edges="links")
        with open(self.storage_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2)

    def add_entity(
        self,
        name: str,
        entity_type: str,
        lecture_id: int,
        chunk_id: int,
    ) -> None:
        key = self._normalize(name)
        if not key:
            return

        if self.graph.has_node(key):
            node = self.graph.nodes[key]
            node["chunk_ids"] = sorted(set(node.get("chunk_ids", []) + [f"{lecture_id}:{chunk_id}"]))
            node["lecture_ids"] = sorted(set(node.get("lecture_ids", []) + [lecture_id]))
        else:
            self.graph.add_node(
                key,
                name=name.strip(),
                entity_type=entity_type,
                chunk_ids=[f"{lecture_id}:{chunk_id}"],
                lecture_ids=[lecture_id],
            )

    def add_relationship(
        self,
        source: str,
        relation: str,
        target: str,
        lecture_id: int,
        chunk_id: int,
    ) -> None:
        source_key = self._normalize(source)
        target_key = self._normalize(target)
        if not source_key or not target_key or source_key == target_key:
            return

        if not self.graph.has_node(source_key):
            self.add_entity(source, "concept", lecture_id, chunk_id)
        if not self.graph.has_node(target_key):
            self.add_entity(target, "concept", lecture_id, chunk_id)

        edge_key = f"{source_key}|{relation}|{target_key}"
        if self.graph.has_edge(source_key, target_key, key=edge_key):
            edge_data = self.graph.edges[source_key, target_key, edge_key]
            edge_data["chunk_ids"] = sorted(
                set(edge_data.get("chunk_ids", []) + [f"{lecture_id}:{chunk_id}"])
            )
        else:
            self.graph.add_edge(
                source_key,
                target_key,
                key=edge_key,
                relation=relation,
                source_name=source.strip(),
                target_name=target.strip(),
                chunk_ids=[f"{lecture_id}:{chunk_id}"],
                lecture_ids=[lecture_id],
            )

    def delete_lecture(self, lecture_id: int) -> None:
        nodes_to_remove = []
        for node, data in list(self.graph.nodes(data=True)):
            lecture_ids = data.get("lecture_ids", [])
            chunk_ids = [
                chunk_id for chunk_id in data.get("chunk_ids", [])
                if not chunk_id.startswith(f"{lecture_id}:")
            ]
            if lecture_id in lecture_ids:
                remaining_lectures = [value for value in lecture_ids if value != lecture_id]
                if not remaining_lectures and not chunk_ids:
                    nodes_to_remove.append(node)
                else:
                    data["lecture_ids"] = remaining_lectures
                    data["chunk_ids"] = chunk_ids

        for node in nodes_to_remove:
            self.graph.remove_node(node)

        edges_to_remove = []
        for source, target, key, data in list(self.graph.edges(keys=True, data=True)):
            chunk_ids = [
                chunk_id for chunk_id in data.get("chunk_ids", [])
                if not chunk_id.startswith(f"{lecture_id}:")
            ]
            lecture_ids = [value for value in data.get("lecture_ids", []) if value != lecture_id]
            if not chunk_ids and not lecture_ids:
                edges_to_remove.append((source, target, key))
            else:
                data["chunk_ids"] = chunk_ids
                data["lecture_ids"] = lecture_ids

        for edge in edges_to_remove:
            self.graph.remove_edge(*edge)

        self._save()

    def find_matching_nodes(
        self,
        entities: List[str],
        source_ids: Optional[List[int]] = None,
    ) -> List[dict]:
        matches = []
        normalized_entities = {self._normalize(entity): entity for entity in entities}

        for node, data in self.graph.nodes(data=True):
            if source_ids and not set(data.get("lecture_ids", [])).intersection(source_ids):
                continue

            for normalized, original in normalized_entities.items():
                if normalized in node or node in normalized:
                    matches.append({
                        "id": node,
                        "name": data.get("name", node),
                        "entity_type": data.get("entity_type", "concept"),
                        "matched_entity": original,
                        "chunk_ids": data.get("chunk_ids", []),
                    })
                    break
        return matches

    def traverse(
        self,
        start_nodes: List[str],
        max_hops: int = 2,
        source_ids: Optional[List[int]] = None,
    ) -> Tuple[List[dict], List[dict], List[List[str]], int]:
        visited_nodes: Set[str] = set()
        visited_edges: Set[Tuple[str, str, str]] = set()
        node_results: List[dict] = []
        relationship_results: List[dict] = []
        paths: List[List[str]] = []
        max_hop_seen = 0

        for start in start_nodes:
            if start not in self.graph:
                continue
            queue = [(start, 0, [start])]
            while queue:
                current, hop, path = queue.pop(0)
                if current in visited_nodes and hop > 0:
                    continue

                node_data = self.graph.nodes.get(current, {})
                if source_ids and not set(node_data.get("lecture_ids", [])).intersection(source_ids):
                    continue

                if current not in visited_nodes:
                    visited_nodes.add(current)
                    node_results.append({
                        "id": current,
                        "name": node_data.get("name", current),
                        "entity_type": node_data.get("entity_type", "concept"),
                        "hop": hop,
                        "chunk_ids": node_data.get("chunk_ids", []),
                    })
                    max_hop_seen = max(max_hop_seen, hop)

                if hop >= max_hops:
                    continue

                for _, neighbor, key, edge_data in self.graph.edges(current, keys=True, data=True):
                    if source_ids and not set(edge_data.get("lecture_ids", [])).intersection(source_ids):
                        continue

                    edge_id = (current, neighbor, key)
                    if edge_id not in visited_edges:
                        visited_edges.add(edge_id)
                        relationship_results.append({
                            "source": edge_data.get("source_name", current),
                            "relation": edge_data.get("relation", "RELATED_TO"),
                            "target": edge_data.get("target_name", neighbor),
                            "chunk_ids": edge_data.get("chunk_ids", []),
                            "hop": hop + 1,
                        })

                    if neighbor not in path:
                        new_path = path + [neighbor]
                        paths.append(new_path)
                        queue.append((neighbor, hop + 1, new_path))

        return node_results, relationship_results, paths, max_hop_seen

    def get_chunk_ids_for_subgraph(
        self,
        nodes: List[dict],
        relationships: List[dict],
    ) -> List[str]:
        chunk_ids: Set[str] = set()
        for node in nodes:
            chunk_ids.update(node.get("chunk_ids", []))
        for relationship in relationships:
            chunk_ids.update(relationship.get("chunk_ids", []))
        return sorted(chunk_ids)

    def _normalize(self, value: str) -> str:
        return " ".join((value or "").lower().split())

    def save(self) -> None:
        self._save()

    def clear(self) -> None:
        self.graph = nx.MultiDiGraph()
        self._save()

    @property
    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    @property
    def edge_count(self) -> int:
        return self.graph.number_of_edges()
