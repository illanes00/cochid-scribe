'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import {
  ChevronLeft,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search,
  FileText,
  Lightbulb,
  BookOpen,
} from 'lucide-react'
import * as d3 from 'd3'
import { GraphData, GraphNode, GraphEdge, graphApi } from '@/lib/api'

// Node colors by type
const NODE_COLORS: Record<string, string> = {
  note: '#3b82f6',      // blue
  document: '#22c55e',  // green
  claim: '#f59e0b',     // amber
  bib: '#8b5cf6',       // purple
}

// Node sizes by type
const NODE_SIZES: Record<string, number> = {
  note: 8,
  document: 10,
  claim: 6,
  bib: 7,
}

interface D3Node extends d3.SimulationNodeDatum {
  id: string
  type: 'note' | 'document' | 'claim' | 'bib'
  label: string
  metadata: Record<string, unknown>
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  type: string
}

export default function GraphPage() {
  const router = useRouter()
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Filter options
  const [showDocuments, setShowDocuments] = useState(true)
  const [showClaims, setShowClaims] = useState(false)
  const [showBib, setShowBib] = useState(true)

  // Load graph data
  const loadGraph = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await graphApi.getFullGraph(showDocuments, showClaims, showBib)
      setGraphData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph')
    } finally {
      setLoading(false)
    }
  }, [showDocuments, showClaims, showBib])

  useEffect(() => {
    loadGraph()
  }, [loadGraph])

  // Render D3 graph
  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return

    const svg = d3.select(svgRef.current)
    svg.selectAll('*').remove()

    const width = containerRef.current.clientWidth
    const height = containerRef.current.clientHeight

    // Create nodes and links
    const nodes: D3Node[] = graphData.nodes.map((n) => ({ ...n }))
    const links: D3Link[] = graphData.edges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
    }))

    // Create zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    // Create container group
    const g = svg.append('g')

    // Create simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink<D3Node, D3Link>(links).id((d) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(20))

    // Create links
    const link = g.append('g')
      .attr('class', 'links')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-opacity', 0.3)
      .attr('stroke-width', 1)

    // Create node groups
    const node = g.append('g')
      .attr('class', 'nodes')
      .selectAll<SVGGElement, D3Node>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer')
      .on('click', (event, d) => {
        event.stopPropagation()
        setSelectedNode(d)
      })

    // Add drag behavior
    const dragBehavior = d3.drag<SVGGElement, D3Node>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart()
        d.fx = d.x
        d.fy = d.y
      })
      .on('drag', (event, d) => {
        d.fx = event.x
        d.fy = event.y
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0)
        d.fx = null
        d.fy = null
      })

    node.call(dragBehavior as unknown as (selection: d3.Selection<SVGGElement, D3Node, SVGGElement, unknown>) => void)

    // Add circles to nodes
    node.append('circle')
      .attr('r', (d) => NODE_SIZES[d.type] || 8)
      .attr('fill', (d) => NODE_COLORS[d.type] || '#666')
      .attr('stroke', '#fff')
      .attr('stroke-width', 1.5)

    // Add labels to nodes
    node.append('text')
      .text((d) => d.label.length > 20 ? d.label.slice(0, 20) + '...' : d.label)
      .attr('x', (d) => (NODE_SIZES[d.type] || 8) + 4)
      .attr('y', 4)
      .attr('font-size', '10px')
      .attr('fill', '#666')

    // Update positions on tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x || 0)
        .attr('y1', (d) => (d.source as D3Node).y || 0)
        .attr('x2', (d) => (d.target as D3Node).x || 0)
        .attr('y2', (d) => (d.target as D3Node).y || 0)

      node.attr('transform', (d) => `translate(${d.x || 0},${d.y || 0})`)
    })

    // Click on background to deselect
    svg.on('click', () => setSelectedNode(null))

    // Cleanup
    return () => {
      simulation.stop()
    }
  }, [graphData])

  // Handle search
  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    if (!searchQuery.trim()) {
      loadGraph()
      return
    }

    try {
      setLoading(true)
      const data = await graphApi.search(searchQuery)
      setGraphData(data)
    } catch (err) {
      setError('Search failed')
    } finally {
      setLoading(false)
    }
  }

  // Navigate to entity
  function navigateToEntity(node: GraphNode) {
    const slug = node.metadata?.slug as string
    if (!slug) return

    switch (node.type) {
      case 'note':
        router.push(`/knowledge/${slug}`)
        break
      case 'document':
        router.push(`/editor/${slug}`)
        break
      default:
        break
    }
  }

  return (
    <div className="h-screen flex flex-col bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper flex-shrink-0">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link href="/knowledge" className="text-muted hover:text-ink">
              <ChevronLeft size={20} />
            </Link>
            <h1 className="text-lg font-semibold">Knowledge Graph</h1>
          </div>

          <div className="flex items-center gap-3">
            <form onSubmit={handleSearch} className="relative">
              <Search size={14} className="absolute left-2 top-1/2 -translate-y-1/2 text-muted" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search graph..."
                className="input text-sm pl-8 w-48"
              />
            </form>
            <button
              onClick={loadGraph}
              className="btn btn-sm"
              disabled={loading}
            >
              <RefreshCw size={14} className={loading ? 'animate-spin' : ''} />
            </button>
          </div>
        </div>
      </header>

      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Graph container */}
        <div ref={containerRef} className="flex-1 relative">
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-bg/80">
              <RefreshCw size={24} className="animate-spin text-muted" />
            </div>
          )}

          {error && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-c-red mb-4">{error}</p>
                <button onClick={loadGraph} className="btn">
                  Retry
                </button>
              </div>
            </div>
          )}

          {graphData && graphData.nodes.length === 0 && (
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <p className="text-muted mb-4">No nodes to display</p>
                <Link href="/knowledge" className="btn btn-primary">
                  Create Notes
                </Link>
              </div>
            </div>
          )}

          <svg
            ref={svgRef}
            width="100%"
            height="100%"
            style={{ display: graphData && graphData.nodes.length > 0 ? 'block' : 'none' }}
          />
        </div>

        {/* Sidebar */}
        <aside className="w-64 border-l border-line bg-paper flex-shrink-0 p-4 overflow-y-auto">
          {/* Legend */}
          <div className="mb-6">
            <h3 className="font-medium text-sm mb-2">Legend</h3>
            <div className="space-y-2">
              <LegendItem color={NODE_COLORS.note} icon={<Lightbulb size={12} />} label="Notes" />
              <LegendItem color={NODE_COLORS.document} icon={<FileText size={12} />} label="Documents" />
              <LegendItem color={NODE_COLORS.bib} icon={<BookOpen size={12} />} label="Bibliography" />
            </div>
          </div>

          {/* Filters */}
          <div className="mb-6">
            <h3 className="font-medium text-sm mb-2">Show</h3>
            <div className="space-y-2">
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showDocuments}
                  onChange={(e) => setShowDocuments(e.target.checked)}
                />
                Documents
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showBib}
                  onChange={(e) => setShowBib(e.target.checked)}
                />
                Bibliography
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={showClaims}
                  onChange={(e) => setShowClaims(e.target.checked)}
                />
                Claims
              </label>
            </div>
          </div>

          {/* Stats */}
          {graphData && (
            <div className="mb-6">
              <h3 className="font-medium text-sm mb-2">Stats</h3>
              <div className="text-sm text-muted space-y-1">
                <p>{graphData.nodes.length} nodes</p>
                <p>{graphData.edges.length} connections</p>
              </div>
            </div>
          )}

          {/* Selected node */}
          {selectedNode && (
            <div className="border-t border-line pt-4">
              <h3 className="font-medium text-sm mb-2">Selected</h3>
              <div className="p-3 bg-bg">
                <div className="flex items-center gap-2 mb-2">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: NODE_COLORS[selectedNode.type] }}
                  />
                  <span className="text-xs text-muted capitalize">{selectedNode.type}</span>
                </div>
                <p className="font-medium text-sm mb-2">{selectedNode.label}</p>
                {(selectedNode.type === 'note' || selectedNode.type === 'document') && (
                  <button
                    onClick={() => navigateToEntity(selectedNode)}
                    className="btn btn-sm btn-primary w-full"
                  >
                    Open
                  </button>
                )}
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  )
}

function LegendItem({
  color,
  icon,
  label,
}: {
  color: string
  icon: React.ReactNode
  label: string
}) {
  return (
    <div className="flex items-center gap-2 text-sm">
      <span
        className="w-3 h-3 rounded-full"
        style={{ backgroundColor: color }}
      />
      {icon}
      <span className="text-muted">{label}</span>
    </div>
  )
}
