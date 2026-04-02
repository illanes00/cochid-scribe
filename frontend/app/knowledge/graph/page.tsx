'use client';

import { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import {
  ChevronLeft,
  RefreshCw,
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search,
  X,
  ExternalLink,
  Filter,
} from 'lucide-react';
import * as d3 from 'd3';
import {
  GraphData,
  GraphNode,
  graphApi,
  commentsApi,
} from '@/lib/api';

// illanes v3 color palette — no border-radius, no shadows
const NODE_COLORS: Record<string, string> = {
  document: '#3763e0', // --c-blue
  claim: '#0b7e59', // --c-green
  comment: '#d97706', // --c-amber
  bib: '#6b7280', // gray-500
  note: '#7c3aed', // purple-600
};

const NODE_RADII: Record<string, number> = {
  document: 10,
  claim: 7,
  comment: 6,
  bib: 8,
  note: 9,
};

const TYPE_LABELS: Record<string, string> = {
  document: 'Document',
  claim: 'Claim',
  comment: 'Comment',
  bib: 'Bibliography',
  note: 'Note',
};

interface D3Node extends d3.SimulationNodeDatum {
  id: string;
  type: string;
  label: string;
  metadata: Record<string, unknown>;
}

interface D3Link extends d3.SimulationLinkDatum<D3Node> {
  type: string;
}

export default function GraphPage() {
  const router = useRouter();
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<D3Node | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [panelOpen, setPanelOpen] = useState(false);

  // Filters
  const [showDocuments, setShowDocuments] = useState(true);
  const [showClaims, setShowClaims] = useState(true);
  const [showComments, setShowComments] = useState(false);
  const [showBib, setShowBib] = useState(true);
  const [showNotes, setShowNotes] = useState(true);
  const [filtersOpen, setFiltersOpen] = useState(false);

  // Fetch graph data + enrich with additional sources
  const loadGraph = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Fetch the base graph
      const data = await graphApi.getFullGraph(
        showDocuments,
        showClaims,
        showBib,
      );

      // Enrich with comments if toggled on
      if (showComments && data.nodes.length > 0) {
        try {
          // Get document slugs from graph nodes
          const docNodes = data.nodes.filter((n) => n.type === 'document');
          for (const docNode of docNodes.slice(0, 10)) {
            const slug = docNode.metadata?.slug as string;
            if (!slug) continue;
            try {
              const comments = await commentsApi.list(slug);
              for (const comment of comments) {
                const commentNodeId = `comment-${comment.id}`;
                // Avoid duplicates
                if (data.nodes.some((n) => n.id === commentNodeId)) continue;
                data.nodes.push({
                  id: commentNodeId,
                  type: 'comment' as GraphNode['type'],
                  label:
                    comment.content.length > 40
                      ? comment.content.slice(0, 40) + '...'
                      : comment.content,
                  metadata: {
                    content: comment.content,
                    author: comment.author,
                    resolved: comment.resolved,
                    created_at: comment.created_at,
                    document_id: comment.document_id,
                  },
                });
                data.edges.push({
                  source: docNode.id,
                  target: commentNodeId,
                  type: 'has_comment',
                });
              }
            } catch {
              // skip if document comments fail
            }
          }
        } catch {
          // comments enrichment failed, continue with base graph
        }
      }

      setGraphData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load graph');
    } finally {
      setLoading(false);
    }
  }, [showDocuments, showClaims, showBib, showComments]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Zoom controls
  const handleZoomIn = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = d3.select(svgRef.current);
    zoomRef.current.scaleBy(svg.transition().duration(300), 1.4);
  }, []);

  const handleZoomOut = useCallback(() => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = d3.select(svgRef.current);
    zoomRef.current.scaleBy(svg.transition().duration(300), 0.7);
  }, []);

  const handleZoomFit = useCallback(() => {
    if (!svgRef.current || !zoomRef.current || !containerRef.current) return;
    const svg = d3.select(svgRef.current);
    svg
      .transition()
      .duration(500)
      .call(zoomRef.current.transform, d3.zoomIdentity);
  }, []);

  // Count nodes by type
  const nodeStats = useMemo(() => {
    if (!graphData) return {};
    const stats: Record<string, number> = {};
    for (const node of graphData.nodes) {
      stats[node.type] = (stats[node.type] || 0) + 1;
    }
    return stats;
  }, [graphData]);

  // Render D3 graph
  useEffect(() => {
    if (!graphData || !svgRef.current || !containerRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    if (graphData.nodes.length === 0) return;

    // Filter nodes by visibility
    const visibleTypes = new Set<string>();
    if (showDocuments) visibleTypes.add('document');
    if (showClaims) visibleTypes.add('claim');
    if (showComments) visibleTypes.add('comment');
    if (showBib) visibleTypes.add('bib');
    if (showNotes) visibleTypes.add('note');

    const filteredNodes = graphData.nodes.filter((n) =>
      visibleTypes.has(n.type),
    );
    const filteredNodeIds = new Set(filteredNodes.map((n) => n.id));
    const filteredEdges = graphData.edges.filter(
      (e) => filteredNodeIds.has(e.source) && filteredNodeIds.has(e.target),
    );

    // Build adjacency for neighbor highlighting
    const adjacency = new Map<string, Set<string>>();
    for (const edge of filteredEdges) {
      if (!adjacency.has(edge.source))
        adjacency.set(edge.source, new Set<string>());
      if (!adjacency.has(edge.target))
        adjacency.set(edge.target, new Set<string>());
      adjacency.get(edge.source)!.add(edge.target);
      adjacency.get(edge.target)!.add(edge.source);
    }

    // Create D3 data copies
    const nodes: D3Node[] = filteredNodes.map((n) => ({ ...n }));
    const links: D3Link[] = filteredEdges.map((e) => ({
      source: e.source,
      target: e.target,
      type: e.type,
    }));

    // Zoom behavior
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.05, 6])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    zoomRef.current = zoom;
    svg.call(zoom);

    // Container group
    const g = svg.append('g');

    // Arrow marker defs
    const defs = svg.append('defs');

    // Arrow markers per edge type
    const markerTypes = [
      'default',
      'references',
      'cites',
      'has_claim',
      'has_comment',
    ];
    for (const mType of markerTypes) {
      defs
        .append('marker')
        .attr('id', `arrow-${mType}`)
        .attr('viewBox', '0 -4 8 8')
        .attr('refX', 16)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-3L7,0L0,3')
        .attr('fill', '#a9b3c2');
    }

    // Force simulation
    const simulation = d3
      .forceSimulation(nodes)
      .force(
        'link',
        d3
          .forceLink<D3Node, D3Link>(links)
          .id((d) => d.id)
          .distance(100),
      )
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force(
        'collision',
        d3.forceCollide<D3Node>().radius((d) => (NODE_RADII[d.type] || 8) + 6),
      )
      .force('x', d3.forceX(width / 2).strength(0.03))
      .force('y', d3.forceY(height / 2).strength(0.03));

    // Edges
    const linkGroup = g.append('g').attr('class', 'links');
    const link = linkGroup
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#d5dbe3')
      .attr('stroke-opacity', 0.6)
      .attr('stroke-width', 1)
      .attr('marker-end', (d) => `url(#arrow-${d.type || 'default'})`);

    // Edge labels (subtle)
    const edgeLabelGroup = g.append('g').attr('class', 'edge-labels');
    const edgeLabel = edgeLabelGroup
      .selectAll('text')
      .data(links)
      .join('text')
      .text((d) => {
        const t = d.type || '';
        return t.replace(/_/g, ' ');
      })
      .attr('font-size', '8px')
      .attr('font-family', "'IBM Plex Sans', system-ui, sans-serif")
      .attr('fill', '#a9b3c2')
      .attr('text-anchor', 'middle')
      .attr('dy', -4)
      .attr('opacity', 0);

    // Node groups
    const nodeGroup = g.append('g').attr('class', 'nodes');
    const node = nodeGroup
      .selectAll<SVGGElement, D3Node>('g')
      .data(nodes)
      .join('g')
      .attr('cursor', 'pointer');

    // Node circles
    node
      .append('circle')
      .attr('r', (d) => NODE_RADII[d.type] || 8)
      .attr('fill', (d) => NODE_COLORS[d.type] || '#6b7280')
      .attr('stroke', 'var(--paper, #ffffff)')
      .attr('stroke-width', 2)
      .style('transition', 'r 0.15s ease');

    // Node labels
    node
      .append('text')
      .text((d) =>
        d.label.length > 24 ? d.label.slice(0, 24) + '...' : d.label,
      )
      .attr('x', (d) => (NODE_RADII[d.type] || 8) + 5)
      .attr('y', 4)
      .attr('font-size', '11px')
      .attr('font-family', "'IBM Plex Sans', system-ui, sans-serif")
      .attr('fill', 'var(--muted, #4b5563)')
      .attr('pointer-events', 'none');

    // Highlight logic
    function highlightNode(nodeId: string | null) {
      if (!nodeId) {
        // Reset all
        node.select('circle').attr('opacity', 1);
        node.select('text').attr('opacity', 1);
        link.attr('stroke-opacity', 0.6).attr('stroke', '#d5dbe3');
        edgeLabel.attr('opacity', 0);
        return;
      }

      const neighbors = adjacency.get(nodeId) || new Set<string>();

      node
        .select('circle')
        .attr('opacity', (d) =>
          d.id === nodeId || neighbors.has(d.id) ? 1 : 0.15,
        );
      node
        .select('text')
        .attr('opacity', (d) =>
          d.id === nodeId || neighbors.has(d.id) ? 1 : 0.1,
        );

      link
        .attr('stroke-opacity', (d) => {
          const s = (d.source as D3Node).id;
          const t = (d.target as D3Node).id;
          return s === nodeId || t === nodeId ? 0.8 : 0.05;
        })
        .attr('stroke', (d) => {
          const s = (d.source as D3Node).id;
          const t = (d.target as D3Node).id;
          return s === nodeId || t === nodeId ? '#a9b3c2' : '#d5dbe3';
        });

      edgeLabel.attr('opacity', (d) => {
        const s = (d.source as D3Node).id;
        const t = (d.target as D3Node).id;
        return s === nodeId || t === nodeId ? 0.8 : 0;
      });
    }

    // Interactions
    node
      .on('mouseenter', (_event, d) => {
        highlightNode(d.id);
        d3.select(_event.currentTarget as SVGGElement)
          .select('circle')
          .transition()
          .duration(150)
          .attr('r', (NODE_RADII[d.type] || 8) + 3);
      })
      .on('mouseleave', (_event, d) => {
        highlightNode(null);
        d3.select(_event.currentTarget as SVGGElement)
          .select('circle')
          .transition()
          .duration(150)
          .attr('r', NODE_RADII[d.type] || 8);
      })
      .on('click', (event, d) => {
        event.stopPropagation();
        setSelectedNode(d);
        setPanelOpen(true);
      });

    // Drag behavior
    const dragBehavior = d3
      .drag<SVGGElement, D3Node>()
      .on('start', (event, d) => {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
      })
      .on('drag', (event, d) => {
        d.fx = event.x;
        d.fy = event.y;
      })
      .on('end', (event, d) => {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
      });

    node.call(
      dragBehavior as unknown as (
        selection: d3.Selection<SVGGElement, D3Node, SVGGElement, unknown>,
      ) => void,
    );

    // Click on background deselects
    svg.on('click', () => {
      setSelectedNode(null);
      setPanelOpen(false);
    });

    // Tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d) => (d.source as D3Node).x || 0)
        .attr('y1', (d) => (d.source as D3Node).y || 0)
        .attr('x2', (d) => (d.target as D3Node).x || 0)
        .attr('y2', (d) => (d.target as D3Node).y || 0);

      edgeLabel
        .attr(
          'x',
          (d) =>
            (((d.source as D3Node).x || 0) + ((d.target as D3Node).x || 0)) /
            2,
        )
        .attr(
          'y',
          (d) =>
            (((d.source as D3Node).y || 0) + ((d.target as D3Node).y || 0)) /
            2,
        );

      node.attr(
        'transform',
        (d) => `translate(${d.x || 0},${d.y || 0})`,
      );
    });

    // Initial zoom to fit
    simulation.on('end', () => {
      // Auto-fit after stabilization
      const bounds = g.node()?.getBBox();
      if (bounds && bounds.width > 0 && bounds.height > 0) {
        const padding = 60;
        const scale = Math.min(
          width / (bounds.width + padding * 2),
          height / (bounds.height + padding * 2),
          1.5,
        );
        const tx = width / 2 - (bounds.x + bounds.width / 2) * scale;
        const ty = height / 2 - (bounds.y + bounds.height / 2) * scale;
        svg
          .transition()
          .duration(500)
          .call(
            zoom.transform,
            d3.zoomIdentity.translate(tx, ty).scale(scale),
          );
      }
    });

    return () => {
      simulation.stop();
    };
  }, [graphData, showDocuments, showClaims, showComments, showBib, showNotes]);

  // Search handler
  async function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    if (!searchQuery.trim()) {
      loadGraph();
      return;
    }
    try {
      setLoading(true);
      const data = await graphApi.search(searchQuery);
      setGraphData(data);
    } catch {
      setError('Search failed');
    } finally {
      setLoading(false);
    }
  }

  // Navigate to entity
  function navigateToEntity(node: D3Node) {
    const slug = node.metadata?.slug as string;
    if (!slug) return;
    switch (node.type) {
      case 'note':
        router.push(`/knowledge/${slug}`);
        break;
      case 'document':
        router.push(`/editor/${slug}`);
        break;
      default:
        break;
    }
  }

  // Get connected node count
  function getConnectedCount(nodeId: string): number {
    if (!graphData) return 0;
    return graphData.edges.filter(
      (e) => e.source === nodeId || e.target === nodeId,
    ).length;
  }

  return (
    <div className="flex h-screen flex-col" style={{ background: 'var(--bg)' }}>
      {/* Header */}
      <header
        className="flex-shrink-0"
        style={{
          borderBottom: '1px solid var(--line)',
          background: 'var(--paper)',
        }}
      >
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-4">
            <Link
              href="/knowledge"
              className="hover:text-ink"
              style={{ color: 'var(--muted)' }}
            >
              <ChevronLeft size={20} />
            </Link>
            <h1 className="text-lg font-semibold">Knowledge Graph</h1>
            {graphData && (
              <span
                className="text-xs"
                style={{ color: 'var(--muted)' }}
              >
                {graphData.nodes.length} nodes / {graphData.edges.length}{' '}
                edges
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <form onSubmit={handleSearch} className="relative">
              <Search
                size={14}
                className="absolute left-2 top-1/2 -translate-y-1/2"
                style={{ color: 'var(--muted)' }}
              />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search graph..."
                className="input text-sm"
                style={{ paddingLeft: '2rem', width: '14rem' }}
              />
            </form>

            <button
              onClick={() => setFiltersOpen(!filtersOpen)}
              className="btn btn-sm"
              style={{
                borderColor: filtersOpen
                  ? 'var(--c-blue)'
                  : 'var(--line)',
              }}
              title="Toggle filters"
            >
              <Filter size={14} />
            </button>

            <div
              style={{
                width: '1px',
                height: '20px',
                background: 'var(--line)',
              }}
            />

            <button
              onClick={handleZoomIn}
              className="btn btn-sm"
              title="Zoom in"
            >
              <ZoomIn size={14} />
            </button>
            <button
              onClick={handleZoomOut}
              className="btn btn-sm"
              title="Zoom out"
            >
              <ZoomOut size={14} />
            </button>
            <button
              onClick={handleZoomFit}
              className="btn btn-sm"
              title="Fit to view"
            >
              <Maximize2 size={14} />
            </button>

            <div
              style={{
                width: '1px',
                height: '20px',
                background: 'var(--line)',
              }}
            />

            <button
              onClick={loadGraph}
              className="btn btn-sm"
              disabled={loading}
            >
              <RefreshCw
                size={14}
                className={loading ? 'animate-spin' : ''}
              />
            </button>
          </div>
        </div>

        {/* Filters bar */}
        {filtersOpen && (
          <div
            className="flex items-center gap-4 px-4 py-2"
            style={{
              borderTop: '1px solid var(--line)',
              background: 'var(--bg)',
            }}
          >
            <span
              className="text-xs font-semibold uppercase"
              style={{ color: 'var(--muted)', letterSpacing: '0.05em' }}
            >
              Show
            </span>
            <FilterToggle
              checked={showNotes}
              onChange={setShowNotes}
              color={NODE_COLORS.note}
              label="Notes"
              count={nodeStats.note}
            />
            <FilterToggle
              checked={showDocuments}
              onChange={setShowDocuments}
              color={NODE_COLORS.document}
              label="Documents"
              count={nodeStats.document}
            />
            <FilterToggle
              checked={showClaims}
              onChange={setShowClaims}
              color={NODE_COLORS.claim}
              label="Claims"
              count={nodeStats.claim}
            />
            <FilterToggle
              checked={showComments}
              onChange={setShowComments}
              color={NODE_COLORS.comment}
              label="Comments"
              count={nodeStats.comment}
            />
            <FilterToggle
              checked={showBib}
              onChange={setShowBib}
              color={NODE_COLORS.bib}
              label="Bibliography"
              count={nodeStats.bib}
            />
          </div>
        )}
      </header>

      {/* Main area */}
      <div className="relative flex flex-1 overflow-hidden">
        {/* Graph canvas */}
        <div ref={containerRef} className="relative flex-1">
          {loading && (
            <div
              className="absolute inset-0 z-10 flex items-center justify-center"
              style={{ background: 'rgba(246, 247, 248, 0.85)' }}
            >
              <div className="flex items-center gap-3">
                <RefreshCw
                  size={20}
                  className="animate-spin"
                  style={{ color: 'var(--muted)' }}
                />
                <span
                  className="text-sm"
                  style={{ color: 'var(--muted)' }}
                >
                  Loading graph...
                </span>
              </div>
            </div>
          )}

          {error && (
            <div className="absolute inset-0 z-10 flex items-center justify-center">
              <div className="text-center">
                <p
                  className="mb-4 text-sm"
                  style={{ color: 'var(--c-red)' }}
                >
                  {error}
                </p>
                <button onClick={loadGraph} className="btn">
                  Retry
                </button>
              </div>
            </div>
          )}

          {graphData && graphData.nodes.length === 0 && !loading && (
            <div className="absolute inset-0 z-10 flex items-center justify-center">
              <div className="text-center">
                <p
                  className="mb-2 text-sm"
                  style={{ color: 'var(--muted)' }}
                >
                  No nodes to display.
                </p>
                <p
                  className="mb-4 text-xs"
                  style={{ color: 'var(--muted)' }}
                >
                  Create notes and documents to build your knowledge graph.
                </p>
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
            style={{
              display:
                graphData && graphData.nodes.length > 0 ? 'block' : 'none',
              cursor: 'grab',
            }}
          />

          {/* Bottom-left legend */}
          <div
            className="absolute bottom-4 left-4 z-10 flex flex-col gap-1 p-3"
            style={{
              background: 'var(--paper)',
              border: '1px solid var(--line)',
            }}
          >
            <span
              className="mb-1 text-xs font-semibold uppercase"
              style={{ color: 'var(--muted)', letterSpacing: '0.05em' }}
            >
              Legend
            </span>
            {Object.entries(NODE_COLORS).map(([type, color]) => (
              <div key={type} className="flex items-center gap-2">
                <span
                  style={{
                    width: 10,
                    height: 10,
                    background: color,
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span
                  className="text-xs"
                  style={{ color: 'var(--muted)' }}
                >
                  {TYPE_LABELS[type] || type}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Detail panel */}
        {panelOpen && selectedNode && (
          <aside
            className="flex-shrink-0 overflow-y-auto"
            style={{
              width: '320px',
              borderLeft: '1px solid var(--line)',
              background: 'var(--paper)',
            }}
          >
            {/* Panel header */}
            <div
              className="flex items-center justify-between p-4"
              style={{ borderBottom: '1px solid var(--line)' }}
            >
              <div className="flex items-center gap-2">
                <span
                  style={{
                    width: 12,
                    height: 12,
                    background:
                      NODE_COLORS[selectedNode.type] || '#6b7280',
                    display: 'inline-block',
                    flexShrink: 0,
                  }}
                />
                <span
                  className="text-xs font-semibold uppercase"
                  style={{
                    color: NODE_COLORS[selectedNode.type] || '#6b7280',
                    letterSpacing: '0.05em',
                  }}
                >
                  {TYPE_LABELS[selectedNode.type] || selectedNode.type}
                </span>
              </div>
              <button
                onClick={() => {
                  setSelectedNode(null);
                  setPanelOpen(false);
                }}
                className="btn btn-sm"
                style={{ border: 'none', padding: '2px' }}
              >
                <X size={16} />
              </button>
            </div>

            {/* Panel content */}
            <div className="p-4">
              <h3
                className="mb-3 text-base font-semibold"
                style={{ lineHeight: 1.3 }}
              >
                {selectedNode.label}
              </h3>

              {/* Metadata */}
              <NodeMetadata metadata={selectedNode.metadata} />

              {/* Connections */}
              <div
                className="mb-4 pt-3"
                style={{ borderTop: '1px solid var(--line)' }}
              >
                <span
                  className="text-xs font-semibold uppercase"
                  style={{
                    color: 'var(--muted)',
                    letterSpacing: '0.05em',
                  }}
                >
                  Connections
                </span>
                <p className="mt-1 text-sm" style={{ color: 'var(--ink)' }}>
                  {getConnectedCount(selectedNode.id)} linked{' '}
                  {getConnectedCount(selectedNode.id) === 1
                    ? 'node'
                    : 'nodes'}
                </p>
              </div>

              {/* Tags */}
              <NodeTags tags={selectedNode.metadata?.tags} />

              {/* Action buttons */}
              {(selectedNode.type === 'note' ||
                selectedNode.type === 'document') &&
                Boolean(selectedNode.metadata?.slug) && (
                  <div
                    className="pt-3"
                    style={{ borderTop: '1px solid var(--line)' }}
                  >
                    <button
                      onClick={() => navigateToEntity(selectedNode)}
                      className="btn btn-primary flex w-full items-center justify-center gap-2"
                    >
                      <ExternalLink size={14} />
                      Open{' '}
                      {selectedNode.type === 'note'
                        ? 'Note'
                        : 'Document'}
                    </button>
                  </div>
                )}
            </div>
          </aside>
        )}
      </div>
    </div>
  );
}

// -- Sub-components --

function FilterToggle({
  checked,
  onChange,
  color,
  label,
  count,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  color: string;
  label: string;
  count?: number;
}) {
  return (
    <label
      className="flex cursor-pointer select-none items-center gap-2 text-sm"
      style={{ color: checked ? 'var(--ink)' : 'var(--muted)' }}
    >
      <span
        style={{
          width: 10,
          height: 10,
          background: checked ? color : 'var(--line)',
          display: 'inline-block',
          flexShrink: 0,
          border: `1px solid ${checked ? color : 'var(--line-strong)'}`,
        }}
      />
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked)}
        className="sr-only"
      />
      <span className="text-xs font-medium">{label}</span>
      {count !== undefined && count > 0 && (
        <span
          className="text-xs"
          style={{ color: 'var(--muted)' }}
        >
          {count}
        </span>
      )}
    </label>
  );
}

function MetaRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-baseline justify-between gap-2">
      <span
        className="flex-shrink-0 text-xs"
        style={{ color: 'var(--muted)' }}
      >
        {label}
      </span>
      <span
        className="text-right text-xs font-medium"
        style={{ color: 'var(--ink)' }}
      >
        {value}
      </span>
    </div>
  );
}

function NodeMetadata({ metadata }: { metadata: Record<string, unknown> }) {
  const slug = metadata?.slug as string | undefined;
  const author = metadata?.author as string | undefined;
  const year = metadata?.year as number | undefined;
  const noteType = metadata?.note_type as string | undefined;
  const claimType = metadata?.claim_type as string | undefined;
  const status = metadata?.status as string | undefined;
  const resolved = metadata?.resolved as boolean | undefined;
  const content = metadata?.content as string | undefined;
  const createdAt = metadata?.created_at as string | undefined;

  return (
    <div className="mb-4 space-y-2">
      {slug && <MetaRow label="Slug" value={slug} />}
      {author && <MetaRow label="Author" value={author} />}
      {year && <MetaRow label="Year" value={String(year)} />}
      {noteType && <MetaRow label="Type" value={noteType} />}
      {claimType && <MetaRow label="Claim Type" value={claimType} />}
      {status && <MetaRow label="Status" value={status} />}
      {resolved !== undefined && (
        <MetaRow label="Resolved" value={resolved ? 'Yes' : 'No'} />
      )}
      {content && (
        <div className="mt-3">
          <span
            className="text-xs font-semibold uppercase"
            style={{ color: 'var(--muted)', letterSpacing: '0.05em' }}
          >
            Content
          </span>
          <p
            className="mt-1 text-sm"
            style={{ color: 'var(--ink)', lineHeight: 1.5 }}
          >
            {content.slice(0, 300)}
            {content.length > 300 && '...'}
          </p>
        </div>
      )}
      {createdAt && (
        <MetaRow
          label="Created"
          value={new Date(createdAt).toLocaleDateString()}
        />
      )}
    </div>
  );
}

function NodeTags({ tags }: { tags: unknown }) {
  if (!Array.isArray(tags) || tags.length === 0) return null;
  const tagList = tags as string[];
  return (
    <div
      className="mb-4 pt-3"
      style={{ borderTop: '1px solid var(--line)' }}
    >
      <span
        className="text-xs font-semibold uppercase"
        style={{ color: 'var(--muted)', letterSpacing: '0.05em' }}
      >
        Tags
      </span>
      <div className="mt-2 flex flex-wrap gap-1">
        {tagList.map((tag) => (
          <span key={tag} className="pill pill-info">
            {tag}
          </span>
        ))}
      </div>
    </div>
  );
}
