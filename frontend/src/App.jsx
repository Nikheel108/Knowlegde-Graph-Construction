import { useEffect, useMemo, useState } from 'react'
import {
  Activity, ArrowDownRight, ArrowUpRight, BrainCircuit, CheckCircle2, ChevronDown,
  CircleHelp, Clock3, Command, Download, FileText, Filter, GitBranch, Globe2,
  Layers3, LayoutDashboard, LoaderCircle, Network, PanelLeftClose, Plus, Search,
  ShieldCheck, Sparkles, Upload, Users, X, Zap, Database, FileJson, FileSpreadsheet,
  Workflow, MessageSquareText, RefreshCw, AlertCircle, ExternalLink, Menu,
} from 'lucide-react'
import {
  Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer,
  Tooltip, XAxis, YAxis,
} from 'recharts'
import { api, API_BASE, getErrorMessage } from './api'
import GraphView from './components/GraphView'

const SAMPLE_QUESTIONS = ['Who founded Tesla?', 'Where is Apple headquartered?', 'What did Google acquire?', 'Who is the CEO of Apple?']
const NAV = [
  { id: 'overview', label: 'Overview', icon: LayoutDashboard, group: 'WORKSPACE' },
  { id: 'graph', label: 'Knowledge Graph', icon: Network, group: 'WORKSPACE' },
  { id: 'entities', label: 'Entities', icon: Users, group: 'EXPLORE' },
  { id: 'relations', label: 'Relations', icon: GitBranch, group: 'EXPLORE' },
  { id: 'insights', label: 'NLP Insights', icon: Sparkles, group: 'EXPLORE' },
  { id: 'ask', label: 'Ask Your Graph', icon: MessageSquareText, group: 'INTELLIGENCE' },
  { id: 'exports', label: 'Export Center', icon: Download, group: 'INTELLIGENCE' },
]
const COLORS = ['#71a7ee', '#7ccdb9', '#c5a5f1', '#f3bd72', '#e58e9c', '#6dc6db', '#a8b8ca']

function formatNumber(value) { return Number(value || 0).toLocaleString('en-IN') }
function initial(name = '') { return name.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() }
function shortDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })
}

export default function App() {
  const [page, setPage] = useState('overview')
  const [data, setData] = useState(null)
  const [documents, setDocuments] = useState([])
  const [sampleDocuments, setSampleDocuments] = useState([])
  const [selectedSample, setSelectedSample] = useState('technology_companies')
  const [apiStatus, setApiStatus] = useState('checking')
  const [modelReady, setModelReady] = useState(false)
  const [busy, setBusy] = useState(false)
  const [busyMessage, setBusyMessage] = useState('Analyzing document...')
  const [error, setError] = useState('')
  const [globalSearch, setGlobalSearch] = useState('')
  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [theme, setTheme] = useState('dark')
  const [entityFilter, setEntityFilter] = useState('All types')
  const [relationFilter, setRelationFilter] = useState('All relations')
  const [relationSearch, setRelationSearch] = useState('')
  const [selectedEntity, setSelectedEntity] = useState(null)
  const [selectedTriple, setSelectedTriple] = useState(null)
  const [question, setQuestion] = useState('')
  const [queryResult, setQueryResult] = useState(null)
  const [queryBusy, setQueryBusy] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const refreshDocuments = async () => {
    try { const response = await api.get('/api/documents'); setDocuments(response.data) } catch { /* API banner handles connectivity */ }
  }

  useEffect(() => {
    api.get('/api/health').then(({ data: health }) => {
      setApiStatus('online'); setModelReady(Boolean(health.model_ready))
    }).catch(() => setApiStatus('offline'))
    refreshDocuments()
    api.get('/api/sample-documents').then(({ data: samples }) => {
      setSampleDocuments(samples)
      if (samples?.length) setSelectedSample(samples[0].id)
    }).catch(() => { /* sample library appears once the API is available */ })
  }, [])

  const loadResult = (result) => {
    setData(result); setPage('overview'); setError(''); setGlobalSearch('')
    setSelectedEntity(null); setSelectedTriple(null); setQueryResult(null); setQuestion('')
    refreshDocuments()
  }

  const analyzeSample = async (sampleId = selectedSample) => {
    if (!sampleId) { setError('Choose a sample document first.'); return }
    setBusy(true); setBusyMessage('Analyzing the selected sample document...'); setError('')
    try { const response = await api.post(`/api/analyze-sample/${sampleId}`); loadResult(response.data) }
    catch (err) { setError(getErrorMessage(err)) }
    finally { setBusy(false) }
  }

  const analyzeFile = async (file) => {
    if (!file) return
    const extension = file.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx', 'txt'].includes(extension)) { setError('Please choose a PDF, DOCX or TXT file.'); return }
    if (file.size > 20 * 1024 * 1024) { setError('Maximum upload size is 20 MB.'); return }
    const body = new FormData(); body.append('file', file)
    setBusy(true); setBusyMessage(`Processing ${file.name}...`); setError('')
    try { const response = await api.post('/api/analyze', body, { headers: { 'Content-Type': 'multipart/form-data' } }); loadResult(response.data) }
    catch (err) { setError(getErrorMessage(err)) }
    finally { setBusy(false) }
  }

  const runQuery = async (value = question) => {
    if (!data || !value.trim()) return
    setQuestion(value); setQueryBusy(true); setQueryResult(null)
    try { const response = await api.post(`/api/documents/${data.id}/query`, { question: value }); setQueryResult(response.data) }
    catch (err) { setQueryResult({ answer: getErrorMessage(err), matches: [] }) }
    finally { setQueryBusy(false) }
  }

  const downloadExport = async (format) => {
    if (!data) return
    try {
      const response = await api.get(`/api/documents/${data.id}/export/${format}`, { responseType: 'blob' })
      const blobUrl = URL.createObjectURL(response.data)
      const link = document.createElement('a'); link.href = blobUrl
      link.download = `${(data.filename || 'knowledge_graph').replace(/\.[^.]+$/, '')}_${format === 'graphml' ? 'graph' : 'triples'}.${format}`
      document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(blobUrl)
    } catch (err) { setError(getErrorMessage(err)) }
  }

  const entityTypes = useMemo(() => ['All types', ...new Set((data?.entities || []).map((entity) => entity.type))], [data])
  const filteredEntities = useMemo(() => (data?.entities || []).filter((entity) =>
    (entityFilter === 'All types' || entity.type === entityFilter) &&
    (!globalSearch || entity.text.toLowerCase().includes(globalSearch.toLowerCase()))), [data, entityFilter, globalSearch])
  const filteredTriples = useMemo(() => (data?.triples || []).filter((triple) =>
    (relationFilter === 'All relations' || triple.predicate === relationFilter) &&
    (!relationSearch || `${triple.subject} ${triple.predicate} ${triple.object} ${triple.sentence}`.toLowerCase().includes(relationSearch.toLowerCase()))), [data, relationFilter, relationSearch])
  const navGroups = [...new Set(NAV.map((item) => item.group))]

  const renderPageTitle = () => {
    const current = NAV.find((item) => item.id === page)
    const titles = {
      overview: ['Command center', 'A live view of your document intelligence workspace.'],
      graph: ['Knowledge graph explorer', 'Explore entities, directed relationships and their evidence.'],
      entities: ['Entity intelligence', 'Inspect named entities extracted from the source document.'],
      relations: ['Relation explorer', 'Review subject–predicate–object triples and supporting evidence.'],
      insights: ['NLP insights', 'Review sentiment, TF-IDF terms and document topics.'],
      ask: ['Ask your graph', 'Get evidence-backed answers from the relationships in your document.'],
      exports: ['Export center', 'Take your extracted graph data into other analysis tools.'],
    }
    return <div className="page-heading"><div><div className="eyebrow">{current?.group || 'WORKSPACE'}</div><h1>{titles[page][0]}</h1><p>{titles[page][1]}</p></div>{data && <div className="source-chip"><FileText size={14}/><span>{data.filename}</span><span className="source-dot"/></div>}</div>
  }

  const renderOverview = () => {
    if (!data) return <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile} />
    return <>
      <div className="metric-grid">
        <MetricCard icon={Users} label="Entities" value={formatNumber(data.entity_count)} note={`${formatNumber(data.entity_mention_count)} mentions`} accent="blue" />
        <MetricCard icon={GitBranch} label="Relations" value={formatNumber(data.relation_count)} note={`${formatNumber(data.raw_triple_count)} raw triples`} accent="purple" />
        <MetricCard icon={FileText} label="Sentences" value={formatNumber(data.sentence_count)} note={`${formatNumber(data.source_chars)} characters`} accent="teal" />
        <MetricCard icon={Activity} label="Graph density" value={`${(data.graph_density * 100).toFixed(1)}%`} note={`${formatNumber(data.graph_edge_count)} unique graph edges`} accent="amber" />
      </div>
      <div className="overview-grid">
        <section className="panel chart-panel"><PanelTitle title="Entity distribution" sub="Named entities detected by spaCy" action="NER" />
          {data.entity_types?.length ? <div className="chart-flex"><div className="donut-wrap"><ResponsiveContainer width="100%" height={220}><PieChart><Pie data={data.entity_types} dataKey="count" nameKey="type" innerRadius={64} outerRadius={88} paddingAngle={3} stroke="none">{data.entity_types.map((item, index) => <Cell key={item.type} fill={COLORS[index % COLORS.length]} />)}</Pie><Tooltip contentStyle={tooltipStyle}/></PieChart></ResponsiveContainer><div className="donut-center"><strong>{formatNumber(data.entity_mention_count)}</strong><span>mentions</span></div></div><div className="legend-list">{data.entity_types.slice(0, 7).map((item, index) => <div className="legend-row" key={item.type}><span className="legend-dot" style={{ background: COLORS[index % COLORS.length] }}/><span>{item.type}</span><strong>{item.count}</strong></div>)}</div></div> : <EmptyState title="No named entities detected" detail="Try a document containing people, organizations or locations." />}
        </section>
        <section className="panel chart-panel"><PanelTitle title="Relationship patterns" sub="Most common extracted predicates" action="SPO" />
          {data.relation_types?.length ? <ResponsiveContainer width="100%" height={245}><BarChart data={data.relation_types.slice(0, 7)} layout="vertical" margin={{ top: 8, right: 12, left: 14, bottom: 4 }}><CartesianGrid strokeDasharray="3 3" stroke="#26364b" horizontal={false}/><XAxis type="number" allowDecimals={false} tick={{ fill: '#8192a9', fontSize: 11 }} axisLine={false} tickLine={false}/><YAxis type="category" dataKey="type" width={122} tick={{ fill: '#b2c0d2', fontSize: 10 }} axisLine={false} tickLine={false}/><Tooltip contentStyle={tooltipStyle}/><Bar dataKey="count" fill="#6e9fe0" radius={[0, 5, 5, 0]} barSize={16}/></BarChart></ResponsiveContainer> : <EmptyState title="No relationships extracted" detail="The selected document may not contain supported subject–verb–object structures." />}
        </section>
        <section className="panel table-panel"><PanelTitle title="High-connectivity entities" sub="Entities with the most graph connections" action="TOP NODES" /><div className="top-entity-list">{(data.top_entities || []).slice(0, 6).map((entity, index) => <button className="top-entity-row" key={entity.id} onClick={() => { setSelectedEntity(entity); setPage('entities') }}><span className="rank-num">0{index + 1}</span><span className="avatar-mini">{initial(entity.name)}</span><span className="entity-name-wrap"><strong>{entity.name}</strong><small>{entity.type}</small></span><span className="connection-count">{entity.degree}<small>links</small></span><ArrowUpRight size={15} className="muted-icon"/></button>)}</div></section>
        <section className="panel table-panel"><PanelTitle title="Recent extracted relations" sub="A quick look at the evidence layer" action="LATEST" /><div className="mini-triples">{(data.triples || []).slice(0, 5).map((triple) => <button className="mini-triple" key={triple.id} onClick={() => { setSelectedTriple(triple); setPage('relations') }}><div className="mini-triple-main"><strong>{triple.subject}</strong><span className="relation-pill">{triple.predicate}</span><strong>{triple.object}</strong></div><div className="mini-triple-sub"><span><FileText size={11}/>{`Sentence ${triple.sentence_index + 1}`}</span><span>{Math.round(triple.confidence * 100)}% heuristic score</span></div></button>)}</div></section>
      </div>
      <div className="footnote"><ShieldCheck size={14}/> Relation confidence is currently the notebook's fixed 0.80 heuristic, not a calibrated probability. <button onClick={() => setPage('relations')}>Review extracted evidence <ArrowUpRight size={13}/></button></div>
    </>
  }

  const renderInsights = () => data ? <div className="nlp-insights"><section className="panel insight-card"><h2>Sentiment baseline</h2><p>Document tone: <strong>{data.sentiment?.label || 'neutral'}</strong> · score {data.sentiment?.score ?? 0}</p><small>Lexicon baseline, not a trained or calibrated sentiment model.</small><div className="sentiment-rows">{(data.sentences || []).map((sentence) => <div key={sentence.index}><span>{sentence.index + 1}. {sentence.text}</span><b>{sentence.sentiment?.label}</b></div>)}</div></section><section className="panel insight-card"><h2>TF-IDF terms</h2><p>{data.vectorization?.vocabulary_size || 0} terms across {data.vectorization?.document_count || 0} sentences</p><div className="insight-terms">{(data.vectorization?.top_terms || []).map((term) => <span key={term.term}>{term.term} <b>{term.score}</b></span>)}</div></section><section className="panel insight-card"><h2>Topic modeling · LDA</h2><p>Topics are estimated from this document’s sentences; short documents may produce weak topics.</p><div className="topic-list">{(data.topics || []).map((topic) => <article key={topic.topic}><strong>Topic {topic.topic}</strong><span>{topic.terms.join(' · ') || 'Insufficient terms'}</span><small>Documents: {topic.documents.map((item) => `${item.filename} (${Math.round(item.weight * 100)}%)`).join(', ') || 'No strong document assignments'}</small></article>)}{!data.topics?.length && <span>Not enough text to estimate topics.</span>}</div></section></div> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>

  const renderGraph = () => <>
    {data ? <><div className="toolbar-row"><div className="inline-search"><Search size={15}/><input placeholder="Find an entity in the graph..." value={globalSearch} onChange={(e) => setGlobalSearch(e.target.value)}/>{globalSearch && <button onClick={() => setGlobalSearch('')}><X size={14}/></button>}</div><div className="graph-stats"><span><i className="status-dot"/>{data.entity_count} nodes</span><span>· {data.relation_count} relations</span></div></div><div className="graph-panel"><div className="graph-panel-head"><div><strong>Entity relationship map</strong><span>Directed links are labeled with extracted predicates</span></div><span className="live-tag"><span/>INTERACTIVE</span></div><GraphView data={data} query={globalSearch} onNodeSelect={setSelectedEntity}/></div>{selectedEntity && <div className="selection-bar"><div className="selection-avatar">{initial(selectedEntity.name)}</div><div><strong>{selectedEntity.name}</strong><span>{selectedEntity.type} · {selectedEntity.degree} graph connections</span></div><button onClick={() => { setGlobalSearch(selectedEntity.name); setPage('relations'); setRelationSearch(selectedEntity.name) }}>View related triples <ArrowUpRight size={14}/></button><button className="icon-btn" onClick={() => setSelectedEntity(null)}><X size={16}/></button></div>}</> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>}</>

  const renderEntities = () => data ? <>
    <div className="toolbar-row"><div className="inline-search"><Search size={15}/><input placeholder="Search entity name..." value={globalSearch} onChange={(e) => setGlobalSearch(e.target.value)}/></div><div className="filter-select"><Filter size={14}/><select value={entityFilter} onChange={(e) => setEntityFilter(e.target.value)}>{entityTypes.map((type) => <option key={type}>{type}</option>)}</select><ChevronDown size={13}/></div><div className="result-count">{filteredEntities.length} mentions</div></div>
    <div className="panel entity-table-panel"><div className="table-head"><span>ENTITY MENTION</span><span>TYPE</span><span>SOURCE SENTENCE</span><span>POSITION</span></div>{filteredEntities.map((entity) => <button className="entity-table-row" key={entity.id} onClick={() => { setSelectedEntity(entity); setRelationSearch(entity.text); setPage('relations') }}><span className="entity-cell"><span className="avatar-mini">{initial(entity.text)}</span><strong>{entity.text}</strong></span><span><span className="type-tag">{entity.type}</span></span><span className="sentence-cell">{entity.sentence}</span><span className="position-cell">#{entity.sentence_index + 1} <ArrowUpRight size={13}/></span></button>)}{!filteredEntities.length && <EmptyState title="No matching entities" detail="Change the search phrase or entity type filter."/>}</div>
  </> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>

  const renderRelations = () => data ? <>
    <div className="toolbar-row"><div className="inline-search"><Search size={15}/><input placeholder="Search subject, predicate, object or evidence..." value={relationSearch} onChange={(e) => setRelationSearch(e.target.value)}/></div><div className="filter-select"><Filter size={14}/><select value={relationFilter} onChange={(e) => setRelationFilter(e.target.value)}><option>All relations</option>{data.relation_types.map((item) => <option key={item.type}>{item.type}</option>)}</select><ChevronDown size={13}/></div><div className="result-count">{filteredTriples.length} triples</div></div>
    <div className="panel relation-list">{filteredTriples.map((triple, index) => <button className={`relation-card ${selectedTriple?.id === triple.id ? 'expanded' : ''}`} key={triple.id} onClick={() => setSelectedTriple(selectedTriple?.id === triple.id ? null : triple)}><div className="relation-card-top"><span className="relation-index">R{String(index + 1).padStart(3, '0')}</span><span className="triple-visual"><strong>{triple.subject}</strong><span className="triple-arrow"><span>{triple.predicate}</span><ArrowDownRight size={15}/></span><strong>{triple.object}</strong></span><span className="confidence-tag">{Math.round(triple.confidence * 100)}% heuristic</span></div><div className="relation-evidence"><span><FileText size={12}/> {triple.source}</span><span>Sentence {triple.sentence_index + 1}</span></div>{selectedTriple?.id === triple.id && <div className="evidence-expanded"><div className="eyebrow">SOURCE EVIDENCE</div><p>“{triple.sentence}”</p><div className="evidence-meta">Extraction method: rule-based dependency parsing · Score: {triple.confidence.toFixed(2)} (heuristic)</div></div>}</button>)}{!filteredTriples.length && <EmptyState title="No matching relationships" detail="Try a different keyword or predicate filter."/>}</div>
  </> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>

  const renderAsk = () => data ? <div className="ask-layout"><section className="ask-main"><div className="ask-intro"><div className="ask-orb"><BrainCircuit size={28}/></div><div><div className="eyebrow">GRAPH-POWERED ANSWERS</div><h2>What would you like to know?</h2><p>Ask questions about entities and relationships found in <strong>{data.filename}</strong>.</p></div></div><form className="question-form" onSubmit={(e) => { e.preventDefault(); runQuery() }}><textarea rows={3} placeholder="e.g. Who founded Tesla?" value={question} onChange={(e) => setQuestion(e.target.value)}/><div className="question-form-bottom"><span><Sparkles size={13}/> Answers include source evidence</span><button className="btn-primary" disabled={queryBusy || !question.trim()}>{queryBusy ? <LoaderCircle className="spin" size={16}/> : <Sparkles size={15}/>} Ask graph</button></div></form><div className="suggestion-title">TRY A SUGGESTED QUESTION</div><div className="suggestion-grid">{(data.suggested_questions?.length ? data.suggested_questions : SAMPLE_QUESTIONS).map((item) => <button key={item} onClick={() => runQuery(item)}>{item}<ArrowUpRight size={13}/></button>)}</div>{queryResult && <div className="answer-block"><div className="answer-heading"><div className="answer-check"><CheckCircle2 size={17}/></div><div><strong>Knowledge graph response</strong><span>{queryResult.matched_by || 'Query'} · {queryResult.matches?.length || 0} evidence match(es)</span></div></div><p className="answer-summary">{queryResult.answer}</p>{queryResult.llm_used && <p className="llm-notice">Gemini answer · cited evidence IDs are validated below.</p>}{queryResult.llm_notice && <p className="llm-notice">{queryResult.llm_notice} Showing the rule-based result.</p>}{queryResult.matches?.map((match) => <div className="answer-evidence" key={match.id}><div className="answer-triple"><strong>{match.subject}</strong><span>{match.predicate}</span><strong>{match.object}</strong></div><blockquote>“{match.sentence}”</blockquote><div className="answer-source"><span><FileText size={12}/>{match.source}</span><span>Sentence {match.sentence_index + 1}</span></div></div>)}</div>}</section><aside className="ask-side panel"><div className="eyebrow">QUERY CAPABILITIES</div><h3>What can it answer?</h3><div className="capability-row"><div className="capability-icon"><Users size={16}/></div><div><strong>Who did what?</strong><span>Find people or entities linked to an action.</span></div></div><div className="capability-row"><div className="capability-icon"><Globe2 size={16}/></div><div><strong>Where is it?</strong><span>Look up location and headquarters relations.</span></div></div><div className="capability-row"><div className="capability-icon"><GitBranch size={16}/></div><div><strong>What is connected?</strong><span>Search by subject, predicate or object.</span></div></div><div className="capability-note"><ShieldCheck size={15}/> Gemini answers are checked against graph evidence; rule-based answers remain the fallback.</div></aside></div> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>

  const renderExports = () => data ? <><div className="export-intro panel"><div className="export-icon"><Database size={24}/></div><div><h2>Your graph data is ready</h2><p>Export extracted triples and graph structure from <strong>{data.filename}</strong>.</p></div><span className="live-tag"><span/>READY</span></div><div className="export-grid"><ExportCard icon={FileSpreadsheet} title="CSV triples" subtitle="Open in Excel, Google Sheets or BI tools." detail={`${data.relation_count} rows · 8 fields`} action="Download CSV" onClick={() => downloadExport('csv')}/><ExportCard icon={FileJson} title="JSON triples" subtitle="Structured relationship objects with source metadata." detail="UTF-8 · Full metadata" action="Download JSON" onClick={() => downloadExport('json')}/><ExportCard icon={Workflow} title="GraphML" subtitle="Import the directed graph into Gephi, Cytoscape or other graph tools." detail={`${data.entity_count} nodes · ${data.graph_edge_count} edges`} action="Download GraphML" onClick={() => downloadExport('graphml')}/></div><div className="panel export-note"><ShieldCheck size={17}/><div><strong>Source attribution included</strong><span>Each exported triple carries its source filename, sentence index, original source sentence and the notebook's heuristic confidence score.</span></div></div></> : <WelcomeScreen samples={sampleDocuments} selectedSample={selectedSample} onSelectSample={setSelectedSample} onSample={analyzeSample} busy={busy} onUpload={analyzeFile}/>

  const pageContent = { overview: renderOverview, graph: renderGraph, entities: renderEntities, relations: renderRelations, insights: renderInsights, ask: renderAsk, exports: renderExports }

  return (
    <div className={`app-shell ${theme}`} onDragOver={(e) => { e.preventDefault(); setDragActive(true) }} onDragLeave={(e) => { if (e.target === e.currentTarget) setDragActive(false) }} onDrop={(e) => { e.preventDefault(); setDragActive(false); analyzeFile(e.dataTransfer.files?.[0]) }}>
      {dragActive && <div className="drop-overlay"><div><Upload size={34}/><strong>Drop your document to analyze</strong><span>PDF, DOCX or TXT · Maximum 20 MB</span></div></div>}
      <aside className={`sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <div className="brand"><div className="brand-mark"><BrainCircuit size={20}/></div>{sidebarOpen && <div className="brand-name"><strong>KnowledgeGraph<span>AI</span></strong><small>INTELLIGENCE STUDIO</small></div>}<button className="collapse-btn" onClick={() => setSidebarOpen(!sidebarOpen)} title="Toggle sidebar"><PanelLeftClose size={16}/></button></div>
        {sidebarOpen && <><button className="workspace-picker"><div className="workspace-avatar">KG</div><div><strong>Research workspace</strong><small>Personal environment</small></div><ChevronDown size={14}/></button><div className="sidebar-nav">{navGroups.map((group) => <div className="nav-group" key={group}><div className="nav-label">{group}</div>{NAV.filter((item) => item.group === group).map((item) => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} onClick={() => setPage(item.id)}><item.icon size={17}/><span>{item.label}</span>{item.id === 'ask' && <span className="nav-new">AI</span>}</button>)}</div>)}</div><div className="sidebar-bottom"><div className="sidebar-status"><span className={apiStatus === 'online' && modelReady ? 'status-green' : 'status-amber'}/><div><strong>{apiStatus === 'offline' ? 'API offline' : modelReady ? 'Systems operational' : 'Model setup required'}</strong><small>{apiStatus === 'offline' ? 'Start backend server' : modelReady ? 'NLP model available' : 'Install spaCy model'}</small></div></div><div className="profile-row"><div className="profile-avatar">KG</div><div><strong>KnowledgeGraph AI</strong><small>Local instance</small></div><span className="profile-dots">•••</span></div></div></>}
      </aside>
      <main className="main-area">
        <header className="topbar"><div className="topbar-left"><button className="mobile-menu icon-btn" onClick={() => setSidebarOpen(!sidebarOpen)}><Menu size={18}/></button><div className="breadcrumb"><span>Workspace</span><span>/</span><strong>{NAV.find((item) => item.id === page)?.label || 'Overview'}</strong></div></div><div className="topbar-actions"><div className="global-search"><Search size={15}/><input placeholder="Search entities..." value={globalSearch} onChange={(e) => { setGlobalSearch(e.target.value); if (e.target.value) setPage('entities') }}/><kbd>⌘ K</kbd></div><span className={`api-indicator ${apiStatus}`}><i/>API {apiStatus === 'online' ? 'Connected' : apiStatus === 'offline' ? 'Offline' : 'Checking'}</span><button className="icon-btn" title="Toggle theme" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}><Zap size={17}/></button><button className="sample-switch-btn" onClick={() => { setData(null); setPage('overview'); setError(''); setQueryResult(null) }}><Layers3 size={14}/> Sample documents</button><label className="btn-upload"><Upload size={15}/> Upload document<input type="file" accept=".pdf,.docx,.txt" onChange={(e) => analyzeFile(e.target.files?.[0])} hidden/></label></div></header>
        <div className="content-area">{renderPageTitle()}{error && <div className="error-banner"><AlertCircle size={16}/><span>{error}</span><button onClick={() => setError('')}><X size={15}/></button></div>}{busy && <div className="processing-banner"><LoaderCircle size={16} className="spin"/><span>{busyMessage}</span><span className="processing-sub">spaCy NLP pipeline running</span></div>}{pageContent[page]()}</div>
        <footer className="app-footer"><span>KnowledgeGraph AI <b>·</b> Local analysis workspace</span><span><span className={modelReady ? 'footer-dot online' : 'footer-dot'}/>{modelReady ? 'NLP model ready' : 'NLP model not detected'} <b>·</b> <a href={`${API_BASE}/docs`} target="_blank" rel="noreferrer">API docs <ExternalLink size={11}/></a></span></footer>
      </main>
    </div>
  )
}

const tooltipStyle = { background: '#101a2b', border: '1px solid #30435d', borderRadius: 10, color: '#e8eef8', fontSize: 12 }

function MetricCard({ icon: Icon, label, value, note, accent }) {
  return <div className="metric-card"><div className={`metric-icon ${accent}`}><Icon size={18}/></div><div className="metric-label">{label}</div><div className="metric-value">{value}</div><div className="metric-note"><span className="metric-trend"><ArrowUpRight size={12}/></span>{note}</div></div>
}
function PanelTitle({ title, sub, action }) { return <div className="panel-title"><div><h3>{title}</h3><p>{sub}</p></div><span className="panel-action">{action}</span></div> }
function EmptyState({ title, detail }) { return <div className="empty-state"><div className="empty-icon"><Layers3 size={20}/></div><strong>{title}</strong><span>{detail}</span></div> }
function ExportCard({ icon: Icon, title, subtitle, detail, action, onClick }) { return <div className="panel export-card"><div className="export-card-icon"><Icon size={22}/></div><h3>{title}</h3><p>{subtitle}</p><div className="export-card-footer"><span className="export-detail">{detail}</span><button className="btn-secondary" onClick={onClick}><Download size={14}/>{action}</button></div></div> }
function WelcomeScreen({ samples, selectedSample, onSelectSample, onSample, busy, onUpload }) {
  const selected = samples.find((sample) => sample.id === selectedSample)
  return <div className="welcome-wrap"><div className="welcome-card"><div className="welcome-orb"><BrainCircuit size={34}/><span/></div><div className="eyebrow">DOCUMENT INTELLIGENCE PLATFORM</div><h2>Turn your documents into<br/><span>connected knowledge.</span></h2><p>Choose a ready-made sample document or upload your own file. The selected document will be processed by your NLP pipeline and become available in Ask Your Graph.</p>
    <div className="sample-library">
      <div className="sample-library-heading"><div><strong>Explore sample documents</strong><span>Preloaded learning documents · no upload required</span></div><span className="sample-library-count">{samples.length || 0} SAMPLES</span></div>
      <select className="sample-select" value={selectedSample} onChange={(e) => onSelectSample(e.target.value)} disabled={!samples.length || busy}>
        {samples.length ? samples.map((sample) => <option key={sample.id} value={sample.id}>{sample.title} · {sample.category}</option>) : <option value="">Loading sample library...</option>}
      </select>
      {selected && <>
        <div className="sample-description"><span>{selected.category}</span><p>{selected.description}</p><small>{selected.characters.toLocaleString()} characters · TXT document</small></div>
        <div className="sample-preview"><div><FileText size={13}/> DOCUMENT PREVIEW</div><pre>{selected.preview}</pre></div>
        <div className="sample-question-preview"><span>EXAMPLE QUESTIONS YOU CAN ASK</span><div>{selected.questions.slice(0, 4).map((item) => <span key={item}>{item}</span>)}</div></div>
        <div className="sample-actions"><button className="sample-button sample-download" onClick={() => window.open(`${API_BASE}/api/sample-documents/${selected.id}/download`, '_blank', 'noopener,noreferrer')} disabled={busy}><Download size={14}/> Download TXT</button><button className="btn-primary sample-analyze" onClick={() => onSample(selected.id)} disabled={busy}>{busy ? <LoaderCircle size={15} className="spin"/> : <Sparkles size={15}/>} Analyze this document</button></div>
      </>}
    </div>
    <div className="upload-divider"><span>OR USE YOUR OWN DOCUMENT</span></div>
    <label className="welcome-upload"><Upload size={17}/> Choose PDF, DOCX or TXT<input type="file" accept=".pdf,.docx,.txt" hidden onChange={(e) => onUpload(e.target.files?.[0])}/></label>
    <div className="format-row"><span>SUPPORTED FORMATS</span><div><b>PDF</b><b>DOCX</b><b>TXT</b><small>Up to 20 MB</small></div></div>
  </div><div className="welcome-features"><div><Network size={18}/><strong>Graph exploration</strong><span>Visualize how entities connect.</span></div><div><ShieldCheck size={18}/><strong>Evidence-backed</strong><span>Trace relations to source sentences.</span></div><div><MessageSquareText size={18}/><strong>Natural-language Q&A</strong><span>Ask questions about extracted facts.</span></div></div></div>
}
