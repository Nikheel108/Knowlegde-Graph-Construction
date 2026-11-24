# KnowledgeGraph AI — React + FastAPI

An advanced full-stack dashboard built around the **Knowledge Graph Construction** notebook supplied with this project. It retains the notebook's core NLP workflow and exposes it through a React interface and REST API.

## Features

- PDF, DOCX and TXT document ingestion (20 MB upload limit)
- Text normalization and spaCy sentence segmentation
- Named Entity Recognition using `en_core_web_sm`
- Rule-based dependency-parsing relation extraction
  - Active and passive voice handling
  - Coordinated subjects and objects
  - Prepositional relations such as `HEADQUARTER_IN`
  - Role relations such as `CEO_OF`
- Entity resolution (normalized corporate suffixes + fuzzy matching)
- Subject–predicate–object triples with source sentence, document and confidence metadata
- Directed NetworkX graph with interactive React Flow visualization
- Entity and predicate analytics, filtering and evidence inspection
- Rule-based natural-language graph query with source-backed results
- Gemini-powered multilingual document extraction and question answering, including Hindi
- CSV, JSON and GraphML export
- Built-in sample document library: Technology, Space Exploration, Science Discoveries and Climate Action
- Sample document preview, one-click TXT download and one-click graph analysis
- Context-specific suggested questions for sample and uploaded documents

## Project structure

```text
KnowledgeGraph_AI/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── sample_documents/
│   ├── technology_companies.txt
│   ├── space_exploration.txt
│   ├── science_discoveries.txt
│   └── climate_action.txt
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── App.jsx
│       ├── api.js
│       ├── main.jsx
│       ├── styles.css
│       └── components/GraphView.jsx
├── README.md
└── .gitignore
```

## Requirements

- Python 3.10 or 3.11
- Node.js 18 or later and npm
- Internet access for the first-time dependency and spaCy model installation

## Run locally on Windows (VS Code)

### 1. Start the backend

Open a terminal in the project root:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

The API is available at `http://localhost:8000`. Interactive API documentation is at `http://localhost:8000/docs`.

If PowerShell blocks activation of `.venv`, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in that terminal, then activate the environment. If PowerShell reports that `npm.ps1` is blocked, use the `npm.cmd` commands shown above.

### 2. Start the React frontend

Open a **second terminal** in the project root (PowerShell on Windows):

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
```

Open `http://localhost:5173` in your browser.

### macOS / Linux activation

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
uvicorn app.main:app --reload --port 8000
```

In a second terminal:

```bash
cd frontend
npm install
npm run dev
```

## First run

1. Start both servers.
2. Open the React app.
3. In the welcome page, choose a built-in sample document (Technology Companies, Space Exploration, Science Discoveries or Climate Action), preview it, and optionally download its TXT file. You can also upload your own PDF/DOCX/TXT document.
4. Select **Analyze this document** to run the spaCy and knowledge-graph pipeline.
5. Open **Ask Your Graph** and use the suggested questions for the selected document, or type your own question.
6. Explore Overview, Knowledge Graph, Entities and Relations, then download triples as CSV/JSON or the graph as GraphML.

## API endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | API and spaCy-model status |
| GET | `/api/documents` | In-memory analyzed document sessions |
| POST | `/api/analyze` | Upload and analyze PDF/DOCX/TXT; multipart `language` may be `en`, `hi` or `auto` |
| GET | `/api/sample-documents` | List built-in sample documents and previews |
| GET | `/api/sample-documents/{sample_id}/download` | Download a sample as TXT |
| POST | `/api/analyze-sample/{sample_id}` | Analyze a selected built-in sample; optional `?language=en|hi|auto` |
| POST | `/api/analyze-sample` | Backward-compatible technology sample endpoint |
| POST | `/api/analyze-text` | Analyze pasted text |
| GET | `/api/documents/{id}` | Retrieve an analyzed document |
| POST | `/api/documents/{id}/query` | Ask a question against the graph |
| GET | `/api/documents/{id}/export/csv` | Export triples as CSV |
| GET | `/api/documents/{id}/export/json` | Export triples as JSON |
| GET | `/api/documents/{id}/export/graphml` | Export graph as GraphML |

## How the notebook logic is used

The backend follows the notebook's pipeline and reuses its dependency-rule implementation for relation extraction and entity normalization:

`Document → Text Extraction → Preprocessing → NER → Relation Extraction → Entity Resolution → Triples → NetworkX Graph → Visualization / Query / Export`

The backend builds a NetworkX `DiGraph`, as the notebook does. The API's visual edge list is derived from the deduplicated triples so that two different predicates between the same pair of nodes can both be drawn in the React graph view.

## Important limitations to understand for your project review

- **Rule-based extraction:** the relation extractor uses spaCy dependency parsing and hand-written patterns. It is not a transformer relation-extraction model.
- **Confidence is a heuristic:** every extracted triple inherits the notebook's fixed `0.80` value. Do not describe it as a trained or calibrated probability.
- **Query engine:** graph Q&A is rule-based pattern matching plus keyword fallback. It is not an LLM and only answers from extracted graph triples.
- **Entity resolution:** normalization and fuzzy string matching can incorrectly merge similar names or fail to resolve aliases.
- **Scanned PDFs:** this build extracts embedded PDF text. It does not run OCR on image-only/scanned pages.
- **Temporary sessions:** analyzed documents are held in backend memory, limited to the latest 12 sessions, and disappear when the API process restarts. This build does not yet use a persistent database or authentication.
- **Graph model:** NetworkX `DiGraph` stores one edge per ordered node pair. The visual React Flow layer draws relations from the triple list so predicate variants remain visible in the UI.

## Troubleshooting

**`Can't find model 'en_core_web_sm'`**

Run this inside the active backend virtual environment:

```bash
python -m spacy download en_core_web_sm
```

**Frontend says API offline**

Check that the FastAPI terminal is running on port 8000. Then refresh the browser.

**PowerShell blocks virtual environment activation**

Use Command Prompt and run `.venv\\Scripts\\activate.bat`, or adjust the PowerShell execution policy for the current user according to your institution's machine policy.

**PDF yields no text**

The current version extracts text layers, not scanned-image OCR. Convert the document to selectable text or add an OCR stage.

## Suggested next research-grade upgrades

1. Add persistent storage (PostgreSQL for documents and metadata, Neo4j for graph persistence).
2. Add coreference resolution to handle pronouns such as “he”, “she”, “it” and “the company”.
3. Evaluate extraction with manually annotated gold-standard triples and report precision, recall and F1.
4. Compare the rule-based baseline against a transformer relation-extraction model.
5. Add user authentication, per-user document isolation and a retention policy before hosting it for multiple users.


## Multilingual analysis with Gemini

Use the language menu in the app before analyzing a sample or uploading a file:

- **English** uses the local spaCy and rule-based pipeline.
- **Hindi** uses Gemini to extract Hindi entities and relations while preserving their original script.
- **Auto detect** asks Gemini to detect the source language and analyze it. Gemini handles other supported languages through this option as well.

The built-in **ISRO Hindi** sample includes a curated analysis and sample-question answers that work without Gemini. Other Hindi documents and uploads still require the backend Gemini configuration.

The Ask Your Graph panel accepts Hindi or English questions. Gemini selects relevant triples from the analyzed graph, replies in the question's language, and cites the source evidence IDs. The API key stays on the backend. Configure `GEMINI_API_KEY`, `LLM_PROVIDER=gemini`, and optionally `LLM_MODEL` in `backend/.env` (or the backend service environment). A backend restart is required after changing environment values.

Gemini multilingual analysis is limited to 120,000 extracted characters per document. It sends the selected document text to Gemini for analysis. The local lexicon sentiment, TF-IDF and LDA features remain English-only and are not presented as multilingual results. Avoid sending sensitive documents unless the provider's current data terms permit it.

## Rubric-aligned NLP capabilities

- **Vectorization:** a local smoothed TF-IDF baseline reports vocabulary size and salient terms for the analyzed document.
- **Sentiment:** a small transparent lexicon baseline reports per-sentence and document labels/scores. It is educational, not a trained or calibrated classifier.
- **Topics:** a compact collapsed-Gibbs LDA implementation suggests up to three topics across the latest in-memory analyzed documents (up to 12 stored sessions plus the document currently being analyzed). Short collections may not yield meaningful topics; sessions disappear when the backend restarts.
- **Grounded generative Q&A:** when configured, graph evidence is sent to Gemini and factual claims must cite triple IDs. English questions first use rule-matched evidence; multilingual questions use Gemini to select relevant graph triples. The API key is never sent to the browser. On request failure, English rule-based responses remain available.

### Gemini environment

Set these only in `backend/.env` locally and in the backend service environment in production (never in a `VITE_` variable): `GEMINI_API_KEY`, `LLM_PROVIDER=gemini`, and `LLM_MODEL=gemini-2.5-flash-lite`. Free-tier quotas can change. Do not send sensitive documents through the free tier; check the provider's current data terms.

### Demo evaluation

Run `python evaluate_rubric.py` from `backend` after installing the project dependencies and downloading `en_core_web_sm`. The script prints small hand-labelled sentiment and relation extraction metrics. This tiny demonstration set is not a statistically representative benchmark; expand and independently annotate it before making accuracy claims.

After analyzing a document, open **NLP Insights** to review sentiment, TF-IDF terms and topic suggestions. In **Ask Your Graph**, questions continue to use graph triples as grounding evidence; Gemini is optional.

## Generate the project poster

Install ReportLab if needed, then run the poster source script from the repository root:

```powershell
python -m pip install reportlab
python scripts/generate_knowledgegraph_poster.py
```

By default it writes `output/pdf/knowledgegraph_ai_poster.pdf`. Use `--output poster.pdf` to choose another destination. The MITAOE mark is loaded from `assets/mitaoe_logo.png`.
