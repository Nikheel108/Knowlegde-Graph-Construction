import { useMemo } from 'react'
import { ReactFlow, Background, Controls, MiniMap, Panel, Handle, Position } from '@xyflow/react'
import dagre from 'dagre'
import { Network, ZoomIn } from 'lucide-react'

function KnowledgeNode({ data, selected }) {
  return (
    <div className={`kg-node ${selected ? 'selected' : ''}`}>
      <Handle type="target" position={Position.Left} />
      <div className="kg-node-top"><span className="kg-node-dot" />{data.type || 'ENTITY'}</div>
      <div className="kg-node-name">{data.label}</div>
      <div className="kg-node-meta">{data.degree} connections</div>
      <Handle type="source" position={Position.Right} />
    </div>
  )
}
const nodeTypes = { knowledge: KnowledgeNode }

function layoutGraph(nodes, edges, direction = 'LR') {
  const graph = new dagre.graphlib.Graph()
  graph.setDefaultEdgeLabel(() => ({}))
  graph.setGraph({ rankdir: direction, nodesep: 62, ranksep: 110, marginx: 40, marginy: 36 })
  nodes.forEach((node) => graph.setNode(node.id, { width: 205, height: 98 }))
  edges.forEach((edge) => graph.setEdge(edge.source, edge.target))
  dagre.layout(graph)
  return {
    nodes: nodes.map((node) => {
      const pos = graph.node(node.id) || { x: 0, y: 0 }
      return { ...node, position: { x: pos.x - 102, y: pos.y - 49 } }
    }),
    edges: edges.map((edge) => ({
      ...edge,
      type: 'smoothstep',
      animated: false,
      label: edge.label,
      labelStyle: { fill: '#9caec4', fontSize: 10, fontWeight: 600 },
      labelBgStyle: { fill: '#101a2b', fillOpacity: 0.94 },
      style: { stroke: '#5e7899', strokeWidth: 1.5 },
      markerEnd: { type: 'arrowclosed', color: '#5e7899', width: 16, height: 16 },
    })),
  }
}

export default function GraphView({ data, query, onNodeSelect }) {
  const graphData = useMemo(() => {
    const rawNodes = (data?.nodes || []).filter((node) => !query || node.name.toLowerCase().includes(query.toLowerCase()))
    const keep = new Set(rawNodes.map((node) => node.id))
    const rawEdges = (data?.edges || []).filter((edge) => keep.has(edge.source) && keep.has(edge.target))
      .map((edge) => ({ id: edge.id, source: edge.source, target: edge.target, label: edge.label, data: edge }))
    const nodes = rawNodes.map((node) => ({
      id: node.id, type: 'knowledge', data: { label: node.name, type: node.type, degree: node.degree, original: node },
      style: { width: 205 },
    }))
    return layoutGraph(nodes, rawEdges)
  }, [data, query])

  if (!graphData.nodes.length) return <div className="graph-empty"><Network size={32} /><strong>No graph nodes to display</strong><span>Analyze a document with extractable relationships to build the graph.</span></div>

  return (
    <div className="graph-shell">
      <ReactFlow
        nodes={graphData.nodes}
        edges={graphData.edges}
        nodeTypes={nodeTypes}
        fitView
        fitViewOptions={{ padding: 0.22, maxZoom: 1.2 }}
        minZoom={0.15}
        maxZoom={2.2}
        onNodeClick={(_, node) => onNodeSelect?.(node.data.original)}
        proOptions={{ hideAttribution: true }}
      >
        <Background color="#263852" gap={22} size={1} />
        <Controls position="bottom-left" />
        <MiniMap pannable zoomable nodeColor="#4b82ba" maskColor="rgba(6, 13, 24, .72)" />
        <Panel position="top-right" className="graph-hint"><ZoomIn size={13} /> Scroll to zoom · drag to explore</Panel>
      </ReactFlow>
    </div>
  )
}
