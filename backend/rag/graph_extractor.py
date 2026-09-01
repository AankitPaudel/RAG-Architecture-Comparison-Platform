import re
from typing import List, Tuple

RELATION_PATTERNS = [
    (r"(\b[A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,2})\s+is\s+(?:a|an)\s+([A-Za-z0-9][\w\s-]{1,40})", "IS_A"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+uses\s+([A-Za-z0-9][\w\s-]{1,40})", "USES"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+is\s+built on\s+([A-Za-z0-9][\w\s-]{1,40})", "BUILT_ON"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+built on\s+([A-Za-z0-9][\w\s-]{1,40})", "BUILT_ON"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+provides\s+([A-Za-z0-9][\w\s-]{1,40})", "PROVIDES"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+depends on\s+([A-Za-z0-9][\w\s-]{1,40})", "DEPENDS_ON"),
    (r"(\b[A-Z][A-Za-z0-9]*)\s+calls\s+([A-Za-z0-9][\w\s-]{1,40})", "CALLS"),
]

STOP_ENTITIES = {
    "the", "this", "that", "these", "those", "it", "they", "we", "you",
}


def extract_entities(text: str) -> List[Tuple[str, str]]:
    entities = []
    seen = set()

    patterns = [
        (r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", "concept"),
        (r"\b[A-Z][a-z]*[A-Z][A-Za-z0-9]+\b", "framework"),
        (r"\b[A-Z]{2,}\b", "acronym"),
    ]

    for pattern, entity_type in patterns:
        for match in re.finditer(pattern, text or ""):
            value = match.group(0).strip()
            key = value.lower()
            if key in STOP_ENTITIES or key in seen or len(value) < 3:
                continue
            seen.add(key)
            entities.append((value, entity_type))

    return entities


def extract_relationships(text: str) -> List[Tuple[str, str, str]]:
    relationships = []
    seen = set()

    for pattern, relation in RELATION_PATTERNS:
        for match in re.finditer(pattern, text or ""):
            source = match.group(1).strip(" .,;:")
            target = match.group(2).strip(" .,;:")
            key = (source.lower(), relation, target.lower())
            if source and target and key not in seen:
                seen.add(key)
                relationships.append((source, relation, target))

    return relationships


def extract_from_chunk(content: str, lecture_id: int, chunk_id: int) -> Tuple[List[dict], List[dict]]:
    entities = [
        {"name": name, "entity_type": entity_type, "lecture_id": lecture_id, "chunk_id": chunk_id}
        for name, entity_type in extract_entities(content)
    ]
    relationships = [
        {
            "source": source,
            "relation": relation,
            "target": target,
            "lecture_id": lecture_id,
            "chunk_id": chunk_id,
        }
        for source, relation, target in extract_relationships(content)
    ]
    return entities, relationships


def extract_entities_from_question(question: str) -> List[str]:
    entities = [name for name, _ in extract_entities(question)]
    if entities:
        return entities

    words = re.findall(r"[A-Za-z0-9]+", question or "")
    return [word for word in words if len(word) > 3 and word.lower() not in STOP_ENTITIES][:5]
