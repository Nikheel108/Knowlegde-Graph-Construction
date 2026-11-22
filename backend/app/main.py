from __future__ import annotations

import csv
import difflib
import io
import json
import re
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import fitz
import networkx as nx
import spacy
from docx import Document as DocxDocument
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

APP_TITLE = "KnowledgeGraph AI API"
MAX_UPLOAD_BYTES = 20 * 1024 * 1024
ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}
SAMPLE_DOCUMENTS: dict[str, dict[str, Any]] = {
    "technology_companies": {
        "title": "Technology Companies",
        "category": "Technology",
        "description": "A starter document about major technology companies, founders, headquarters, products and acquisitions.",
        "filename": "technology_companies.txt",
        "questions": [
            "Who founded Apple?",
            "Where is Apple headquartered?",
            "Who is the CEO of Google?",
            "What did Microsoft acquire?",
            "What did Google acquire?",
        ],
        "text": """Steve Jobs founded Apple in 1976.
Steve Wozniak co-founded Apple in 1976.
Apple is headquartered in Cupertino, California.
Apple developed the iPhone.
Tim Cook is the CEO of Apple.
Bill Gates founded Microsoft in 1975.
Microsoft is headquartered in Redmond, Washington.
Microsoft acquired LinkedIn in 2016.
Google acquired DeepMind in 2014.
Sundar Pichai is the CEO of Google.
Google is headquartered in Mountain View, California.
""",
    },
    "space_exploration": {
        "title": "Space Exploration",
        "category": "Science & Space",
        "description": "A short document about ISRO, NASA, space missions, launch vehicles and space exploration milestones.",
        "filename": "space_exploration.txt",
        "questions": [
            "What did ISRO launch?",
            "Where is ISRO headquartered?",
            "Who is the chairman of ISRO?",
            "Who launched Chandrayaan-3?",
            "What did NASA launch?",
        ],
        "text": """India established ISRO in 1969.
ISRO launched Chandrayaan-3 in 2023.
ISRO launched the Mars Orbiter Mission in 2013.
ISRO is headquartered in Bengaluru, India.
S. Somanath is the chairman of ISRO.
NASA launched Apollo 11 in 1969.
Neil Armstrong commanded Apollo 11.
NASA launched the James Webb Space Telescope in 2021.
NASA is headquartered in Washington, D.C.
""",
    },
    "science_discoveries": {
        "title": "Science Discoveries",
        "category": "Science",
        "description": "A sample about scientists, landmark discoveries, inventions and major scientific awards.",
        "filename": "science_discoveries.txt",
        "questions": [
            "Who discovered radium?",
            "Who discovered penicillin?",
            "What did Marie Curie discover?",
            "Who won the Nobel Prize in Physics?",
        ],
        "text": """Marie Curie discovered radium in 1898.
Marie Curie won the Nobel Prize in Physics in 1903.
Pierre Curie collaborated with Marie Curie.
Alexander Fleming discovered penicillin in 1928.
Alexander Fleming received the Nobel Prize in Medicine in 1945.
Nikola Tesla invented the alternating current induction motor.
Thomas Edison developed the practical electric light bulb.
""",
    },
    "climate_action": {
        "title": "Climate Action & Environment",
        "category": "Environment",
        "description": "A starter document about climate agreements, renewable energy and environmental programmes.",
        "filename": "climate_action.txt",
        "questions": [
            "Who adopted the Paris Agreement?",
            "What did India launch?",
            "Who promotes solar energy?",
            "Where is the United Nations headquartered?",
        ],
        "text": """The United Nations adopted the Paris Agreement in 2015.
India launched the National Clean Air Programme in 2019.
The Government of India supports renewable energy projects.
The International Energy Agency publishes global energy reports.
The United Nations is headquartered in New York City.
The Solar Energy Corporation of India promotes solar energy.
The Paris Agreement aims to limit global warming.
""",
    },
}

# Backward-compatible default sample for older frontend versions.
SAMPLE_DOCUMENT = SAMPLE_DOCUMENTS["technology_companies"]["text"]

nlp = None
DOCUMENTS: dict[str, dict[str, Any]] = {}

app = FastAPI(
    title=APP_TITLE,
    description="Document ingestion, spaCy NER, rule-based relation extraction, knowledge graph analysis and evidence-backed queries.",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_nlp():
    """Load the same spaCy model used in the supplied notebook, lazily."""
    global nlp
    if nlp is None:
        try:
            nlp = spacy.load("en_core_web_sm")
        except OSError as exc:
            raise RuntimeError(
                "spaCy model 'en_core_web_sm' is not installed. Run: "
                "python -m spacy download en_core_web_sm"
            ) from exc
    return nlp


def extract_text_from_bytes(filename: str, content: bytes) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Unsupported file type. Upload PDF, DOCX or TXT.")
    if suffix == ".pdf":
        with fitz.open(stream=content, filetype="pdf") as pdf:
            return "\n".join(page.get_text() for page in pdf)
    if suffix == ".docx":
        document = DocxDocument(io.BytesIO(content))
        return "\n".join(p.text for p in document.paragraphs if p.text.strip())
    return content.decode("utf-8", errors="replace")


def clean_text(raw_text: str) -> str:
    """Notebook preprocessing: normalize whitespace and punctuation spacing."""
    text = re.sub(r"\s+", " ", raw_text)
    text = re.sub(r"\s+([.,;:])", r"\1", text)
    return text.strip()


def split_into_sentences(cleaned_text: str) -> list[str]:
    """Use spaCy sentence boundary detection, as in the notebook."""
    doc = get_nlp()(cleaned_text)
    return [sent.text.strip() for sent in doc.sents if sent.text.strip()]


# ============================================================
# MODULE 3: NAMED ENTITY RECOGNITION (NER)
# ============================================================

def extract_entities(sentence: str):
    '''
    Run spaCy NER on a single sentence.
    Returns a list of dicts: {text, label, start_char, end_char}
    '''
    doc = nlp(sentence)
    entities = [
        {
            "text": ent.text,
            "label": ent.label_,
            "start_char": ent.start_char,
            "end_char": ent.end_char,
        }
        for ent in doc.ents
    ]
    return entities



# ============================================================
# MODULE 4: RELATION EXTRACTION (rule-based, dependency parsing)
# ============================================================

def _head_noun(token):
    '''If `token` is just a compound modifier (e.g. "Marc" inside "Marc
    Tarpenning"), walk up to the true head noun of the phrase so we always
    expand from the head, never from a modifier alone.'''
    seen = set()
    while token.dep_ == "compound" and token.head is not token and token.i not in seen:
        seen.add(token.i)
        token = token.head
    return token

def _expand_to_noun_chunk(token, doc):
    '''Given a token, return the full noun phrase it belongs to (if any).'''
    token = _head_noun(token)
    for chunk in doc.noun_chunks:
        if chunk.start <= token.i < chunk.end:
            return chunk.text
    # Fallback: stitch together compound/flat modifiers attached to this token
    modifiers = [c for c in token.children if c.dep_ in ("compound", "flat", "name")]
    if modifiers:
        idxs = sorted([token.i] + [c.i for c in modifiers])
        return doc[idxs[0]: idxs[-1] + 1].text
    return token.text

def _expand_conjuncts(token):
    '''Given a token (e.g. a subject or object), return it plus any tokens
    coordinated with it via "and"/"," (conj dependency) -- so
    "Steve Jobs, Wozniak and Wayne" all get captured, not just the first one.'''
    return [token] + list(token.conjuncts)

def extract_relations(sentence: str, sent_index: int, source_doc: str):
    '''
    Extract (subject, relation, object) triples from one sentence using
    dependency-parse patterns. Returns a list of triple dicts with metadata.
    Handles both active voice ("X founded Y") and passive voice
    ("Y was founded by X"), and expands coordinated subjects/objects
    ("X, Y and Z founded W").
    '''
    doc = nlp(sentence)
    triples = []

    for token in doc:
        # We are looking for verbs (and copula "is/are/was") that have a subject
        if token.pos_ not in ("VERB", "AUX"):
            continue

        # ---- find raw subject(s) of this verb (before passive handling) ----
        raw_subjects = [c for c in token.children if c.dep_ in ("nsubj", "nsubjpass")]
        if not raw_subjects:
            continue
        is_passive = any(c.dep_ == "nsubjpass" for c in raw_subjects)

        # ---- find candidate objects: dobj / attr / oprd / prepositional objects ----
        direct_objects = []     # e.g. dobj/attr -> "developed the iPhone"
        prep_objects = []       # e.g. "headquartered IN Austin" -> (prep_text, Austin)
        agent_objects = []      # e.g. passive "founded BY Steve Jobs" -> Steve Jobs
        fully_labeled = []      # (ready-made relation label, object token)

        for child in token.children:
            if child.dep_ in ("dobj", "attr", "oprd"):
                # Special case: copula + attribute-with-prep, e.g.
                # "Tim Cook is the CEO of Apple" -> attr="CEO" has its own
                # prep "of" -> pobj "Apple". We turn this into a direct,
                # ready-made relation: Tim Cook --CEO_OF--> Apple (much more
                # useful than the generic Tim Cook --IS--> CEO).
                attr_prep_handled = False
                if child.dep_ == "attr":
                    for grandchild in child.children:
                        if grandchild.dep_ == "prep":
                            for gg in grandchild.children:
                                if gg.dep_ == "pobj":
                                    label = f"{child.text}_{grandchild.text}".upper()
                                    fully_labeled.append((label, gg))
                                    attr_prep_handled = True
                if not attr_prep_handled:
                    direct_objects.append(child)
            elif child.dep_ == "prep":
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        prep_objects.append((child.text, grandchild))
            elif child.dep_ == "agent":  # the "by" phrase in passive voice
                for grandchild in child.children:
                    if grandchild.dep_ == "pobj":
                        agent_objects.append(grandchild)

        verb_lemma = token.lemma_.upper()

        def make_triples(subj_tokens, rel_label, obj_tokens):
            for s in subj_tokens:
                for o in obj_tokens:
                    subj_text = _expand_to_noun_chunk(s, doc)
                    obj_text = _expand_to_noun_chunk(o, doc)
                    if subj_text.lower() in ("it", "this", "that", "they", "he", "she") or \
                       obj_text.lower() in ("it", "this", "that", "they", "he", "she"):
                        continue  # skip unresolved pronouns
                    if subj_text.strip().lower() == obj_text.strip().lower():
                        continue  # skip self-loops
                    triples.append({
                        "subject": subj_text.strip(),
                        "predicate": rel_label.strip(),
                        "object": obj_text.strip(),
                        "source": source_doc,
                        "sentence_index": sent_index,
                        "sentence": sentence,
                        "confidence": 0.8,   # heuristic confidence for rule-based extraction
                    })

        if is_passive:
            # PASSIVE VOICE: "Tesla was founded by Martin Eberhard"
            #   nsubjpass = Tesla (syntactic subject, semantic OBJECT)
            #   agent     = Martin Eberhard (semantic SUBJECT -- who did the action)
            # We flip subject/object so the relation reads naturally:
            #   Martin Eberhard --FOUND--> Tesla
            passive_subjects = [t for s in raw_subjects for t in _expand_conjuncts(s)]
            if agent_objects:
                semantic_subjects = [t for a in agent_objects for t in _expand_conjuncts(a)]
                make_triples(semantic_subjects, verb_lemma, passive_subjects)
            # passive verbs can still have their own prepositional objects,
            # e.g. "Tesla is headquartered IN Austin" (headquartered = passive-form verb)
            for prep_text, obj in prep_objects:
                objs = _expand_conjuncts(obj)
                make_triples(passive_subjects, f"{verb_lemma}_{prep_text.upper()}", objs)
        else:
            # ACTIVE VOICE: "Steve Jobs founded Apple" / "Tim Cook is the CEO of Apple"
            active_subjects = [t for s in raw_subjects for t in _expand_conjuncts(s)]
            if direct_objects:
                objs = [t for o in direct_objects for t in _expand_conjuncts(o)]
                make_triples(active_subjects, verb_lemma, objs)
            for prep_text, obj in prep_objects:
                objs = _expand_conjuncts(obj)
                make_triples(active_subjects, f"{verb_lemma}_{prep_text.upper()}", objs)
            for label, obj in fully_labeled:
                objs = _expand_conjuncts(obj)
                make_triples(active_subjects, label, objs)

    return triples



# ============================================================
# MODULE 5: ENTITY RESOLUTION + FINAL TRIPLE GENERATION
# ============================================================

_CORP_SUFFIXES = r"\b(inc\.?|incorporated|corp\.?|corporation|ltd\.?|llc|co\.?|company)\b"

def normalize_entity(text: str) -> str:
    '''Lowercase, strip leading articles ("the"/"a"), and strip common
    corporate suffixes (Inc., Corp., Ltd., ...) so "Apple" and "Apple Inc."
    normalize to the same string for comparison purposes.'''
    text = text.strip().lower()
    text = re.sub(r"^(the|a|an)\s+", "", text)
    text = re.sub(_CORP_SUFFIXES, "", text)
    text = re.sub(r"[.,]", "", text)          # drop stray punctuation
    text = re.sub(r"\s+", " ", text).strip()  # collapse whitespace
    return text

def build_canonical_map(entity_strings, similarity_threshold: float = 0.80):
    '''
    Groups near-duplicate entity strings (e.g. "Apple" / "Apple Inc.")
    into one canonical name.
    Strategy:
      1. Exact match after normalization (strip articles/corp suffixes)   -> always merge
      2. Otherwise, fuzzy string match above `similarity_threshold`        -> merge
      3. Otherwise, keep as its own new entity
    Returns a dict: {original_string -> canonical_display_name}
    We pick the SHORTEST original surface form as the display name (e.g.
    "Apple" rather than "Apple Inc.") since that reads better in a graph.
    '''
    unique_entities = sorted(set(entity_strings), key=len)  # shortest first
    norm_to_canonical_original = {}   # normalized form -> chosen original display string
    canonical_map = {}                # original string -> normalized canonical key

    normalized_keys = []  # all normalized keys chosen so far, for fuzzy matching
    for entity in unique_entities:
        norm = normalize_entity(entity)
        if not norm:
            norm = entity.strip().lower()

        if norm in norm_to_canonical_original:
            canonical_map[entity] = norm
            continue

        fuzzy_match = difflib.get_close_matches(norm, normalized_keys, n=1, cutoff=similarity_threshold)
        if fuzzy_match:
            canonical_map[entity] = fuzzy_match[0]
        else:
            norm_to_canonical_original[norm] = entity  # first (shortest) surface form wins
            normalized_keys.append(norm)
            canonical_map[entity] = norm

    # Map each original string to the chosen display name (nicely title-cased)
    pretty_map = {}
    for original, norm_key in canonical_map.items():
        display = norm_to_canonical_original[norm_key]
        pretty_map[original] = display
    return pretty_map




def build_graph(triples: list[dict[str, Any]]) -> nx.DiGraph:
    """Build a directed NetworkX graph, preserving the notebook's DiGraph model."""
    graph = nx.DiGraph()
    for triple in triples:
        graph.add_node(triple["subject"])
        graph.add_node(triple["object"])
        graph.add_edge(
            triple["subject"], triple["object"],
            relation=triple["predicate"], source=triple["source"],
            sentence_index=triple["sentence_index"], sentence=triple["sentence"],
            confidence=triple["confidence"],
        )
    return graph


def analyze_document(raw_text: str, filename: str) -> dict[str, Any]:
    """Run the end-to-end pipeline from the uploaded notebook."""
    if not raw_text or not raw_text.strip():
        raise ValueError("No readable text was found in this document.")
    model = get_nlp()  # ensure global model is loaded before pipeline functions run
    cleaned = clean_text(raw_text)
    sentences = split_into_sentences(cleaned)

    entities_by_sentence = [extract_entities(sentence) for sentence in sentences]
    entity_mentions: list[dict[str, Any]] = []
    for sentence_index, (sentence, entities) in enumerate(zip(sentences, entities_by_sentence)):
        for entity in entities:
            entity_mentions.append({
                "id": f"mention-{sentence_index}-{entity['start_char']}-{uuid.uuid4().hex[:5]}",
                "text": entity["text"],
                "type": entity["label"],
                "sentence_index": sentence_index,
                "sentence": sentence,
                "start_char": entity["start_char"],
                "end_char": entity["end_char"],
            })

    raw_triples: list[dict[str, Any]] = []
    for sentence_index, sentence in enumerate(sentences):
        raw_triples.extend(extract_relations(sentence, sentence_index, filename))

    all_entity_strings: list[str] = []
    for triple in raw_triples:
        all_entity_strings.extend([triple["subject"], triple["object"]])
    canonical_map = build_canonical_map(all_entity_strings)

    resolved_triples: list[dict[str, Any]] = []
    for triple in raw_triples:
        resolved_triples.append({
            "id": str(uuid.uuid4())[:8],
            "subject": canonical_map[triple["subject"]],
            "predicate": triple["predicate"],
            "object": canonical_map[triple["object"]],
            "source": triple["source"],
            "sentence_index": triple["sentence_index"],
            "sentence": triple["sentence"],
            "confidence": triple["confidence"],
        })

    # Match the notebook's duplicate rule: same subject + predicate + object.
    seen: set[tuple[str, str, str]] = set()
    triples: list[dict[str, Any]] = []
    for triple in resolved_triples:
        key = (triple["subject"].lower(), triple["predicate"], triple["object"].lower())
        if key not in seen:
            seen.add(key)
            triples.append(triple)

    graph = build_graph(triples)
    type_by_name: dict[str, str] = {}
    mentions_count: Counter[str] = Counter()
    for mention in entity_mentions:
        mentions_count[mention["text"]] += 1
        type_by_name.setdefault(mention["text"].casefold(), mention["type"])

    entity_frequency: Counter[str] = Counter()
    for triple in triples:
        entity_frequency[triple["subject"]] += 1
        entity_frequency[triple["object"]] += 1

    nodes = []
    for name in graph.nodes:
        match_type = type_by_name.get(name.casefold(), "ENTITY")
        nodes.append({
            "id": name,
            "name": name,
            "type": match_type,
            "degree": int(graph.degree(name)),
            "in_degree": int(graph.in_degree(name)),
            "out_degree": int(graph.out_degree(name)),
            "triple_mentions": int(entity_frequency[name]),
        })

    # Use triples, rather than DiGraph edges, in the UI payload so distinct
    # predicates between the same pair are not hidden by DiGraph's edge model.
    edges = [{
        "id": triple["id"],
        "source": triple["subject"],
        "target": triple["object"],
        "label": triple["predicate"],
        "confidence": triple["confidence"],
        "source_doc": triple["source"],
        "sentence_index": triple["sentence_index"],
        "sentence": triple["sentence"],
    } for triple in triples]

    type_counts = Counter(mention["type"] for mention in entity_mentions)
    predicate_counts = Counter(triple["predicate"] for triple in triples)
    degree_sorted = sorted(nodes, key=lambda node: node["degree"], reverse=True)
    graph_nodes = graph.number_of_nodes()
    graph_edges = graph.number_of_edges()
    density = nx.density(graph) if graph_nodes > 1 else 0.0
    avg_degree = (sum(dict(graph.degree()).values()) / graph_nodes) if graph_nodes else 0.0

    suggested_questions: list[str] = []
    for triple in triples:
        predicate = triple["predicate"].upper()
        if "CEO_OF" in predicate:
            candidate = f"Who is the CEO of {triple['object']}?"
        elif "CHAIRMAN_OF" in predicate:
            candidate = f"Who is the chairman of {triple['object']}?"
        elif "HEADQUARTER" in predicate:
            candidate = f"Where is {triple['subject']} headquartered?"
        elif predicate == "FOUND" or predicate.endswith("_FOUND"):
            candidate = f"Who founded {triple['object']}?"
        elif predicate == "ACQUIRE" or predicate.endswith("_ACQUIRE"):
            candidate = f"What did {triple['subject']} acquire?"
        elif predicate == "DISCOVER" or predicate.endswith("_DISCOVER"):
            candidate = f"Who discovered {triple['object']}?"
        else:
            candidate = None
        if candidate and candidate not in suggested_questions:
            suggested_questions.append(candidate)
        if len(suggested_questions) >= 5:
            break

    return {
        "id": str(uuid.uuid4()),
        "filename": filename,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_chars": len(cleaned),
        "source_preview": raw_text[:1200],
        "sentence_count": len(sentences),
        "raw_triple_count": len(raw_triples),
        "entity_count": graph_nodes,
        "relation_count": len(triples),
        "graph_edge_count": graph_edges,
        "entity_mention_count": len(entity_mentions),
        "entity_type_count": len(type_counts),
        "graph_density": round(float(density), 4),
        "average_degree": round(float(avg_degree), 2),
        "mean_extraction_confidence": round(
            sum(t["confidence"] for t in triples) / len(triples), 2
        ) if triples else 0,
        "entity_types": [{"type": key, "count": value} for key, value in type_counts.most_common()],
        "relation_types": [{"type": key, "count": value} for key, value in predicate_counts.most_common()],
        "suggested_questions": suggested_questions,
        "top_entities": degree_sorted[:10],
        "entities": entity_mentions,
        "triples": triples,
        "nodes": nodes,
        "edges": edges,
        "sentences": [{"index": i, "text": sentence} for i, sentence in enumerate(sentences)],
        "_graph": graph,
        "_raw_text": raw_text,
    }


def find_entity(name: str, graph: nx.DiGraph):
    name_lower = name.lower().strip()
    for node in graph.nodes:
        if node.lower() == name_lower:
            return node
    for node in graph.nodes:
        if name_lower in node.lower() or node.lower() in name_lower:
            return node
    return None


def lemmatize_word(word: str) -> str:
    tokens = get_nlp()(word)
    return tokens[0].lemma_.lower() if tokens else word.lower()


def query_graph(question: str, result: dict[str, Any]) -> dict[str, Any]:
    """Rule-based Q&A matching the intent patterns in the supplied notebook."""
    graph: nx.DiGraph = result["_graph"]
    triples = result["triples"]
    q = question.strip().rstrip("?")
    q_lower = q.lower()
    matches: list[dict[str, Any]] = []
    route = "keyword search"

    def incoming(entity_name: str, keyword: str):
        entity = find_entity(entity_name, graph)
        if not entity:
            return []
        lemma = lemmatize_word(keyword)
        return [t for t in triples if t["object"] == entity and lemma in t["predicate"].lower()]

    def outgoing(entity_name: str, keyword: str):
        entity = find_entity(entity_name, graph)
        if not entity:
            return []
        lemma = lemmatize_word(keyword)
        return [t for t in triples if t["subject"] == entity and lemma in t["predicate"].lower()]

    # Order matches the notebook: role query, location query, what-did query,
    # generic who-verb query, then token-based keyword fallback.
    match = re.match(r"who\s+is\s+the\s+(\w+)\s+of\s+(.+)", q_lower)
    if match:
        route = "role lookup"
        matches = incoming(match.group(2), match.group(1))
    else:
        match = re.match(r"where\s+is\s+(.+?)\s+(headquartered|located|based)", q_lower)
        if match:
            route = "location lookup"
            matches = outgoing(match.group(1), "headquarter") or outgoing(match.group(1), "locat")
        else:
            match = re.match(r"what\s+did\s+(.+?)\s+(\w+)", q_lower)
            if match:
                route = "subject-action lookup"
                matches = outgoing(match.group(1), match.group(2))
            else:
                match = re.match(r"who\s+(\w+)\s+(.+)", q_lower)
                if match:
                    route = "person/entity lookup"
                    matches = incoming(match.group(2), match.group(1))

    if not matches:
        words = [word for word in q_lower.split() if len(word) > 2 and word not in {"who", "what", "where", "did", "the", "is", "was", "are", "and", "for"}]
        for triple in triples:
            haystack = f"{triple['subject']} {triple['predicate']} {triple['object']}".lower()
            if any(word in haystack for word in words):
                matches.append(triple)
        if matches:
            route = "keyword search"

    if matches:
        answer = "Found {} evidence-backed relation(s) in the knowledge graph.".format(len(matches))
    else:
        answer = "No matching evidence was found in this document's knowledge graph. Try another entity or relation keyword."
    return {"question": question, "answer": answer, "matched_by": route, "matches": matches}


class TextAnalyzeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=500_000)
    filename: str = "pasted_text.txt"


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)


def public_result(result: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in result.items() if not key.startswith("_")}


def store_result(result: dict[str, Any]) -> dict[str, Any]:
    DOCUMENTS[result["id"]] = result
    # Keep the in-memory demo workspace bounded.
    if len(DOCUMENTS) > 12:
        oldest_id = next(iter(DOCUMENTS))
        DOCUMENTS.pop(oldest_id, None)
    return public_result(result)


def require_document(document_id: str):
    result = DOCUMENTS.get(document_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document session not found. Upload or analyze the document again.")
    return result


@app.get("/api/health")
def health():
    model_ready = False
    try:
        model_ready = "en_core_web_sm" in spacy.util.get_installed_models()
    except Exception:
        pass
    return {
        "status": "ok",
        "service": APP_TITLE,
        "model_ready": model_ready,
        "model": "en_core_web_sm",
        "message": "Ready" if model_ready else "Install model with: python -m spacy download en_core_web_sm",
    }


@app.get("/api/documents")
def list_documents():
    return [{"id": item["id"], "filename": item["filename"], "created_at": item["created_at"],
             "entity_count": item["entity_count"], "relation_count": item["relation_count"]}
            for item in reversed(list(DOCUMENTS.values())[-12:])]


@app.post("/api/analyze")
async def analyze_upload(file: UploadFile = File(...)):
    filename = Path(file.filename or "uploaded_document").name
    if Path(filename).suffix.lower() not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, DOCX and TXT.")
    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is larger than 20 MB.")
    try:
        raw_text = extract_text_from_bytes(filename, content)
        result = analyze_document(raw_text, filename)
        return store_result(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ValueError, Exception) as exc:
        raise HTTPException(status_code=422, detail=f"Document analysis failed: {exc}") from exc


@app.get("/api/sample-documents")
def list_sample_documents():
    """Return the built-in document library shown on the React welcome page."""
    return [
        {
            "id": sample_id,
            "title": sample["title"],
            "category": sample["category"],
            "description": sample["description"],
            "filename": sample["filename"],
            "preview": sample["text"][:900],
            "questions": sample["questions"],
            "characters": len(sample["text"]),
        }
        for sample_id, sample in SAMPLE_DOCUMENTS.items()
    ]


@app.get("/api/sample-documents/{sample_id}/download")
def download_sample_document(sample_id: str):
    sample = SAMPLE_DOCUMENTS.get(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample document not found.")
    return Response(
        sample["text"].encode("utf-8"),
        media_type="text/plain; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{sample["filename"]}"'},
    )


@app.post("/api/analyze-sample/{sample_id}")
def analyze_named_sample(sample_id: str):
    sample = SAMPLE_DOCUMENTS.get(sample_id)
    if sample is None:
        raise HTTPException(status_code=404, detail="Sample document not found.")
    try:
        result = analyze_document(sample["text"], sample["filename"])
        result["suggested_questions"] = sample["questions"]
        result["sample_category"] = sample["category"]
        return store_result(result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/api/analyze-sample")
def analyze_sample():
    # Keep the original endpoint available for older clients.
    return analyze_named_sample("technology_companies")


@app.post("/api/analyze-text")
def analyze_pasted_text(payload: TextAnalyzeRequest):
    try:
        return store_result(analyze_document(payload.text, payload.filename))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/documents/{document_id}")
def get_document(document_id: str):
    return public_result(require_document(document_id))


@app.post("/api/documents/{document_id}/query")
def ask_document(document_id: str, payload: QueryRequest):
    result = require_document(document_id)
    try:
        return query_graph(payload.question, result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/documents/{document_id}/export/{file_format}")
def export_document(document_id: str, file_format: str):
    result = require_document(document_id)
    filename_stem = Path(result["filename"]).stem or "knowledge_graph"
    if file_format == "json":
        payload = json.dumps(result["triples"], ensure_ascii=False, indent=2).encode("utf-8")
        return Response(payload, media_type="application/json", headers={
            "Content-Disposition": f'attachment; filename="{filename_stem}_triples.json"'
        })
    if file_format == "csv":
        output = io.StringIO()
        fields = ["id", "subject", "predicate", "object", "confidence", "source", "sentence_index", "sentence"]
        writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(result["triples"])
        return Response(output.getvalue().encode("utf-8-sig"), media_type="text/csv", headers={
            "Content-Disposition": f'attachment; filename="{filename_stem}_triples.csv"'
        })
    if file_format == "graphml":
        graph_text = "\n".join(nx.generate_graphml(result["_graph"], encoding="utf-8"))
        return Response(graph_text.encode("utf-8"), media_type="application/graphml+xml", headers={
            "Content-Disposition": f'attachment; filename="{filename_stem}_graph.graphml"'
        })
    raise HTTPException(status_code=400, detail="Format must be csv, json or graphml.")
