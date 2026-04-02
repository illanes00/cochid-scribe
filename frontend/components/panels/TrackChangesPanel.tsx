'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Check,
  X,
  Clock,
  CheckCircle,
  XCircle,
  RefreshCw,
  ChevronDown,
  ChevronRight,
  Plus,
  Minus,
  Keyboard,
} from 'lucide-react';
import {
  TrackChange,
  TrackChangesListResponse,
  ChangeStatus,
  trackChangesApi,
} from '@/lib/api';

interface TrackChangesPanelProps {
  documentSlug: string;
  onChangeResolved?: () => void;
}

function timeAgo(dateStr: string): string {
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMin = Math.floor(diffMs / 60000);
  if (diffMin < 1) return 'just now';
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHr = Math.floor(diffMin / 60);
  if (diffHr < 24) return `${diffHr}h ago`;
  const diffDay = Math.floor(diffHr / 24);
  if (diffDay < 30) return `${diffDay}d ago`;
  return new Date(dateStr).toLocaleDateString();
}

/** Group changes by "section" based on their position in the document. */
function groupBySection(changes: TrackChange[]): Record<string, TrackChange[]> {
  const groups: Record<string, TrackChange[]> = {};
  changes.forEach((change) => {
    // Use position ranges to create rough sections
    const pos = change.position_start ?? 0;
    let section: string;
    if (pos < 500) section = 'Beginning';
    else if (pos < 2000) section = 'Early sections';
    else if (pos < 5000) section = 'Middle sections';
    else section = 'Later sections';

    if (!groups[section]) groups[section] = [];
    groups[section].push(change);
  });
  return groups;
}

export function TrackChangesPanel({
  documentSlug,
  onChangeResolved,
}: TrackChangesPanelProps) {
  const [data, setData] = useState<TrackChangesListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ChangeStatus | 'all'>(
    'all',
  );
  const [resolving, setResolving] = useState<string | null>(null);
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [collapsedSections, setCollapsedSections] = useState<Set<string>>(
    new Set(),
  );
  const [showShortcuts, setShowShortcuts] = useState(false);

  const loadChanges = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const status = statusFilter === 'all' ? undefined : statusFilter;
      const result = await trackChangesApi.list(documentSlug, status);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load changes');
    } finally {
      setLoading(false);
    }
  }, [documentSlug, statusFilter]);

  useEffect(() => {
    loadChanges();
  }, [loadChanges]);

  const handleResolve = async (
    changeId: string,
    action: 'accept' | 'reject',
  ) => {
    setResolving(changeId);
    try {
      await trackChangesApi.resolve(documentSlug, changeId, action);
      await loadChanges();
      onChangeResolved?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to resolve change');
    } finally {
      setResolving(null);
    }
  };

  const handleAcceptAll = async () => {
    if (!confirm('Accept all pending changes?')) return;
    setLoading(true);
    try {
      await trackChangesApi.acceptAll(documentSlug);
      await loadChanges();
      onChangeResolved?.();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to accept all changes',
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRejectAll = async () => {
    if (!confirm('Reject all pending changes?')) return;
    setLoading(true);
    try {
      await trackChangesApi.rejectAll(documentSlug);
      await loadChanges();
      onChangeResolved?.();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Failed to reject all changes',
      );
    } finally {
      setLoading(false);
    }
  };

  // Group changes by section
  const sections = useMemo(() => {
    if (!data?.changes) return {};
    return groupBySection(data.changes);
  }, [data]);

  const sectionKeys = useMemo(() => Object.keys(sections), [sections]);

  // Flat list of all visible changes for keyboard navigation
  const flatChanges = useMemo(() => {
    if (!data?.changes) return [];
    return data.changes;
  }, [data]);

  // Keyboard shortcuts
  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      // Only when this panel is likely visible (no modal, no input focused)
      const target = e.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT'
      )
        return;
      if (!flatChanges.length) return;

      const current = flatChanges[selectedIndex];

      if (e.key === 'j' || e.key === 'ArrowDown') {
        e.preventDefault();
        setSelectedIndex((i) => Math.min(i + 1, flatChanges.length - 1));
      } else if (e.key === 'k' || e.key === 'ArrowUp') {
        e.preventDefault();
        setSelectedIndex((i) => Math.max(i - 1, 0));
      } else if (e.key === 'a' && current?.status === 'pending') {
        e.preventDefault();
        handleResolve(current.change_id, 'accept');
      } else if (e.key === 'r' && current?.status === 'pending') {
        e.preventDefault();
        handleResolve(current.change_id, 'reject');
      }
    }

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [flatChanges, selectedIndex]);

  function toggleSection(section: string) {
    setCollapsedSections((prev) => {
      const next = new Set(prev);
      if (next.has(section)) {
        next.delete(section);
      } else {
        next.add(section);
      }
      return next;
    });
  }

  const getStatusIcon = (status: ChangeStatus) => {
    switch (status) {
      case 'pending':
        return <Clock size={12} className="text-c-amber" />;
      case 'accepted':
        return <CheckCircle size={12} className="text-c-green" />;
      case 'rejected':
        return <XCircle size={12} className="text-c-red" />;
    }
  };

  if (loading && !data) {
    return (
      <div className="p-4 text-center text-muted text-sm">
        <RefreshCw size={16} className="animate-spin mx-auto mb-2" />
        Loading changes...
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-c-red text-sm mb-2">{error}</div>
        <button onClick={loadChanges} className="btn btn-sm">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <h3 className="font-medium text-sm text-ink">Track Changes</h3>
            {data && (
              <span className="text-xs text-muted">({data.total})</span>
            )}
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={() => setShowShortcuts((v) => !v)}
              className="p-1 hover:bg-bg text-muted"
              title="Keyboard shortcuts"
            >
              <Keyboard size={12} />
            </button>
            <button
              onClick={loadChanges}
              className="p-1 hover:bg-bg text-muted"
              title="Refresh"
            >
              <RefreshCw
                size={12}
                className={loading ? 'animate-spin' : ''}
              />
            </button>
          </div>
        </div>

        {/* Status counts */}
        {data && (
          <div className="flex gap-3 text-xs">
            <span className="flex items-center gap-1 text-c-amber">
              <Clock size={10} />
              {data.pending_count} pending
            </span>
            <span className="flex items-center gap-1 text-c-green">
              <CheckCircle size={10} />
              {data.accepted_count}
            </span>
            <span className="flex items-center gap-1 text-c-red">
              <XCircle size={10} />
              {data.rejected_count}
            </span>
          </div>
        )}
      </div>

      {/* Keyboard shortcuts tooltip */}
      {showShortcuts && (
        <div className="px-3 py-2 border-b border-line bg-bg text-xs text-muted space-y-1">
          <div className="flex justify-between">
            <span>Navigate</span>
            <span className="font-mono">j / k</span>
          </div>
          <div className="flex justify-between">
            <span>Accept selected</span>
            <span className="font-mono">a</span>
          </div>
          <div className="flex justify-between">
            <span>Reject selected</span>
            <span className="font-mono">r</span>
          </div>
        </div>
      )}

      {/* Filter */}
      <div className="p-2 border-b border-line flex gap-1">
        {(
          ['all', 'pending', 'accepted', 'rejected'] as (
            | ChangeStatus
            | 'all'
          )[]
        ).map((f) => (
          <button
            key={f}
            onClick={() => setStatusFilter(f)}
            className={`px-2 py-1 text-xs ${
              statusFilter === f
                ? 'bg-ink text-paper'
                : 'text-muted hover:bg-bg'
            }`}
          >
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Bulk actions */}
      {data && data.pending_count > 0 && (
        <div className="p-2 border-b border-line flex gap-2">
          <button
            onClick={handleAcceptAll}
            className="btn btn-sm btn-success flex-1 text-xs flex items-center justify-center gap-1"
            disabled={loading}
          >
            <Check size={10} />
            Accept All ({data.pending_count})
          </button>
          <button
            onClick={handleRejectAll}
            className="btn btn-sm btn-danger flex-1 text-xs flex items-center justify-center gap-1"
            disabled={loading}
          >
            <X size={10} />
            Reject All
          </button>
        </div>
      )}

      {/* Changes list grouped by section */}
      <div className="flex-1 overflow-auto">
        {!data?.changes.length ? (
          <div className="p-6 text-center">
            <CheckCircle size={24} className="mx-auto text-muted mb-2" />
            <p className="text-sm text-muted">No tracked changes</p>
            <p className="text-xs text-muted mt-1">
              Changes from reviewers and AI suggestions will appear here.
            </p>
          </div>
        ) : (
          <div>
            {sectionKeys.map((section) => {
              const sectionChanges = sections[section];
              const collapsed = collapsedSections.has(section);
              const pendingInSection = sectionChanges.filter(
                (c) => c.status === 'pending',
              ).length;

              return (
                <div key={section}>
                  {/* Section header */}
                  {sectionKeys.length > 1 && (
                    <button
                      className="w-full flex items-center gap-2 px-3 py-1.5 bg-bg border-b border-line hover:bg-line/30 text-left"
                      onClick={() => toggleSection(section)}
                    >
                      {collapsed ? (
                        <ChevronRight size={10} className="text-muted" />
                      ) : (
                        <ChevronDown size={10} className="text-muted" />
                      )}
                      <span className="text-xs text-muted">{section}</span>
                      <span className="text-xs text-muted">
                        ({sectionChanges.length})
                      </span>
                      {pendingInSection > 0 && (
                        <span className="text-xs text-c-amber ml-auto">
                          {pendingInSection} pending
                        </span>
                      )}
                    </button>
                  )}

                  {/* Changes in section */}
                  {!collapsed &&
                    sectionChanges.map((change) => {
                      const isSelected =
                        flatChanges[selectedIndex]?.change_id ===
                        change.change_id;
                      const isInsert = change.change_type === 'insert';

                      return (
                        <div
                          key={change.change_id}
                          className={`border-b border-line ${
                            isSelected
                              ? 'border-l-2 border-l-c-blue bg-bg/50'
                              : ''
                          }`}
                        >
                          <div className="p-3">
                            {/* Header row */}
                            <div className="flex items-center justify-between mb-1.5">
                              <div className="flex items-center gap-2">
                                {getStatusIcon(change.status)}
                                <span
                                  className={`flex items-center gap-1 text-xs font-medium ${
                                    isInsert ? 'text-c-green' : 'text-c-red'
                                  }`}
                                >
                                  {isInsert ? (
                                    <Plus size={10} />
                                  ) : (
                                    <Minus size={10} />
                                  )}
                                  {isInsert ? 'Insert' : 'Delete'}
                                </span>
                              </div>
                              <span className="text-xs text-muted">
                                {timeAgo(change.created_at)}
                              </span>
                            </div>

                            {/* Content with inline context */}
                            {change.content && (
                              <div className="text-sm mt-1">
                                <div
                                  className={`px-2 py-1.5 border-l-2 ${
                                    isInsert
                                      ? 'border-l-c-green bg-c-green/5'
                                      : 'border-l-c-red bg-c-red/5 line-through'
                                  }`}
                                >
                                  <span
                                    className={
                                      isInsert ? 'text-ink' : 'text-c-red'
                                    }
                                  >
                                    {change.content.length > 150
                                      ? `${change.content.substring(0, 150)}...`
                                      : change.content}
                                  </span>
                                </div>
                              </div>
                            )}

                            {/* Author */}
                            {change.author_name && (
                              <div className="text-xs text-muted mt-1.5">
                                by {change.author_name}
                              </div>
                            )}

                            {/* Resolution info */}
                            {change.status !== 'pending' &&
                              change.resolved_at && (
                                <div className="text-xs text-muted mt-1">
                                  {change.status === 'accepted'
                                    ? 'Accepted'
                                    : 'Rejected'}
                                  {change.resolved_by &&
                                    ` by ${change.resolved_by}`}{' '}
                                  {timeAgo(change.resolved_at)}
                                </div>
                              )}

                            {/* Actions for pending */}
                            {change.status === 'pending' && (
                              <div className="flex gap-2 mt-2">
                                <button
                                  onClick={() =>
                                    handleResolve(change.change_id, 'accept')
                                  }
                                  className="btn btn-sm btn-success text-xs flex items-center gap-1"
                                  disabled={resolving === change.change_id}
                                  title="Accept (a)"
                                >
                                  <Check size={10} />
                                  Accept
                                </button>
                                <button
                                  onClick={() =>
                                    handleResolve(change.change_id, 'reject')
                                  }
                                  className="btn btn-sm btn-danger text-xs flex items-center gap-1"
                                  disabled={resolving === change.change_id}
                                  title="Reject (r)"
                                >
                                  <X size={10} />
                                  Reject
                                </button>
                              </div>
                            )}
                          </div>
                        </div>
                      );
                    })}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
