'use client';

import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Database,
  BookOpen,
  Beaker,
  Layers,
  Check,
  X,
  AlertCircle,
  RotateCcw,
  FileText,
  ChevronDown,
  ChevronRight,
  Shield,
  ShieldCheck,
  ShieldX,
  ShieldAlert,
} from 'lucide-react';
import { Claim, claimsApi, llmApi } from '@/lib/api';

interface ClaimsPanelProps {
  documentSlug: string;
  onClaimClick?: (
    claimId: string,
    claimText?: string,
    startOffset?: number | null,
    endOffset?: number | null,
  ) => void;
  activeClaimId?: string | null;
}

type ClaimType = 'DATA' | 'LITERATURE' | 'MIXED' | 'HYPOTHESIS';
type ClaimStatus = 'draft' | 'verified' | 'rejected' | 'needs_revision';
type FilterMode = 'all' | ClaimStatus;

const TYPE_CONFIG: Record<
  ClaimType,
  { label: string; icon: typeof Database; colorClass: string; bgClass: string }
> = {
  DATA: {
    label: 'Data',
    icon: Database,
    colorClass: 'text-c-blue',
    bgClass: 'bg-c-blue/10',
  },
  LITERATURE: {
    label: 'Literature',
    icon: BookOpen,
    colorClass: 'text-purple-700 dark:text-purple-400',
    bgClass: 'bg-purple-100 dark:bg-purple-900/20',
  },
  MIXED: {
    label: 'Mixed',
    icon: Layers,
    colorClass: 'text-c-amber',
    bgClass: 'bg-c-amber/10',
  },
  HYPOTHESIS: {
    label: 'Hypothesis',
    icon: Beaker,
    colorClass: 'text-c-green',
    bgClass: 'bg-c-green/10',
  },
};

const STATUS_CONFIG: Record<
  ClaimStatus,
  { label: string; icon: typeof Shield; colorClass: string }
> = {
  draft: { label: 'Draft', icon: Shield, colorClass: 'text-muted' },
  verified: {
    label: 'Verified',
    icon: ShieldCheck,
    colorClass: 'text-c-green',
  },
  rejected: { label: 'Rejected', icon: ShieldX, colorClass: 'text-c-red' },
  needs_revision: {
    label: 'Needs Revision',
    icon: ShieldAlert,
    colorClass: 'text-c-amber',
  },
};

function evidenceStrength(claim: Claim): {
  level: 'strong' | 'moderate' | 'weak' | 'none';
  label: string;
} {
  const count = claim.evidence?.length || 0;
  const sources = claim.source_sentences?.length || 0;
  const total = count + sources;
  if (total >= 3) return { level: 'strong', label: 'Strong evidence' };
  if (total >= 1) return { level: 'moderate', label: 'Some evidence' };
  return { level: 'weak', label: 'No evidence' };
}

const STRENGTH_COLORS: Record<string, string> = {
  strong: 'bg-c-green',
  moderate: 'bg-c-amber',
  weak: 'bg-c-red',
  none: 'bg-muted',
};

export function ClaimsPanel({
  documentSlug,
  onClaimClick,
  activeClaimId = null,
}: ClaimsPanelProps) {
  const [claims, setClaims] = useState<Claim[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<FilterMode>('all');
  const [extracting, setExtracting] = useState(false);
  const [extractError, setExtractError] = useState<string | null>(null);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(
    new Set(),
  );

  const loadClaims = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await claimsApi.listByDocument(documentSlug);
      setClaims(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load claims');
    } finally {
      setLoading(false);
    }
  }, [documentSlug]);

  useEffect(() => {
    loadClaims();
  }, [loadClaims]);

  async function handleVerify(claimId: string) {
    try {
      const updated = await claimsApi.verify(claimId);
      setClaims((prev) =>
        prev.map((c) => (c.claim_id === claimId ? updated : c)),
      );
    } catch (err) {
      console.error('Failed to verify claim:', err);
    }
  }

  async function handleDelete(claimId: string) {
    if (!confirm('Delete this claim?')) return;
    try {
      await claimsApi.delete(claimId);
      setClaims((prev) => prev.filter((c) => c.claim_id !== claimId));
    } catch (err) {
      console.error('Failed to delete claim:', err);
    }
  }

  async function handleExtractClaims() {
    try {
      if (!documentSlug || documentSlug === 'new') return;
      setExtracting(true);
      setExtractError(null);
      await llmApi.extractClaimsForDocument(documentSlug);
      await loadClaims();
    } catch (err) {
      setExtractError(
        err instanceof Error ? err.message : 'Failed to extract claims',
      );
    } finally {
      setExtracting(false);
    }
  }

  function toggleGroup(type: string) {
    setCollapsedGroups((prev) => {
      const next = new Set(prev);
      if (next.has(type)) {
        next.delete(type);
      } else {
        next.add(type);
      }
      return next;
    });
  }

  // Stats
  const stats = useMemo(
    () => ({
      total: claims.length,
      verified: claims.filter((c) => c.status === 'verified').length,
      draft: claims.filter((c) => c.status === 'draft').length,
      rejected: claims.filter((c) => c.status === 'rejected').length,
      needs_revision: claims.filter((c) => c.status === 'needs_revision')
        .length,
    }),
    [claims],
  );

  // Filter, then group by type
  const filteredClaims =
    filter === 'all' ? claims : claims.filter((c) => c.status === filter);

  const groupedClaims = useMemo(() => {
    const groups: Record<ClaimType, Claim[]> = {
      DATA: [],
      LITERATURE: [],
      MIXED: [],
      HYPOTHESIS: [],
    };
    filteredClaims.forEach((claim) => {
      const type = claim.claim_type as ClaimType;
      if (groups[type]) {
        groups[type].push(claim);
      }
    });
    return groups;
  }, [filteredClaims]);

  const activeTypes = (Object.keys(groupedClaims) as ClaimType[]).filter(
    (type) => groupedClaims[type].length > 0,
  );

  if (loading) {
    return <div className="p-4 text-muted text-sm">Loading claims...</div>;
  }

  if (error) {
    return (
      <div className="p-4">
        <div className="text-c-red text-sm">{error}</div>
        <button onClick={loadClaims} className="mt-2 text-xs underline">
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <FileText size={14} className="text-muted" />
            <h2 className="font-medium text-ink text-sm">Claims</h2>
            <span className="text-xs text-muted">({stats.total})</span>
          </div>
        </div>

        {/* Stats row */}
        {stats.total > 0 && (
          <div className="flex items-center gap-3 mt-2 text-xs">
            <span className="flex items-center gap-1 text-c-green">
              <ShieldCheck size={10} />
              {stats.verified}
            </span>
            <span className="flex items-center gap-1 text-muted">
              <Shield size={10} />
              {stats.draft}
            </span>
            {stats.needs_revision > 0 && (
              <span className="flex items-center gap-1 text-c-amber">
                <ShieldAlert size={10} />
                {stats.needs_revision}
              </span>
            )}
            <span className="flex items-center gap-1 text-c-red">
              <ShieldX size={10} />
              {stats.rejected}
            </span>
          </div>
        )}

        {extractError && (
          <div className="text-xs text-c-red mt-2">{extractError}</div>
        )}
      </div>

      {/* Status filter */}
      <div className="p-2 border-b border-line flex gap-1">
        {(
          ['all', 'draft', 'verified', 'needs_revision', 'rejected'] as const
        ).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-2 py-1 text-xs ${
              filter === f ? 'bg-ink text-paper' : 'text-muted hover:bg-bg'
            }`}
          >
            {f === 'all'
              ? 'All'
              : f === 'needs_revision'
                ? 'Revision'
                : f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
      </div>

      {/* Claims grouped by type */}
      <div className="flex-1 overflow-y-auto">
        {filteredClaims.length === 0 ? (
          <div className="p-6 text-center">
            <FileText size={24} className="mx-auto text-muted mb-2" />
            <p className="text-sm text-muted mb-1">
              {stats.total === 0
                ? 'No claims found in this document.'
                : 'No claims match the current filter.'}
            </p>
            {stats.total === 0 && (
              <p className="text-xs text-muted">
                Use &ldquo;Extract Claims&rdquo; to automatically identify
                verifiable assertions.
              </p>
            )}
          </div>
        ) : (
          <div>
            {activeTypes.map((type) => {
              const config = TYPE_CONFIG[type];
              const typeClaims = groupedClaims[type];
              const collapsed = collapsedGroups.has(type);
              const Icon = config.icon;

              return (
                <div key={type}>
                  {/* Group header */}
                  <button
                    className="w-full flex items-center gap-2 px-3 py-2 bg-bg border-b border-line hover:bg-line/30 text-left"
                    onClick={() => toggleGroup(type)}
                  >
                    {collapsed ? (
                      <ChevronRight size={12} className="text-muted" />
                    ) : (
                      <ChevronDown size={12} className="text-muted" />
                    )}
                    <Icon size={12} className={config.colorClass} />
                    <span className="text-xs font-medium text-ink">
                      {config.label}
                    </span>
                    <span className="text-xs text-muted">
                      ({typeClaims.length})
                    </span>
                  </button>

                  {/* Claims in group */}
                  {!collapsed &&
                    typeClaims.map((claim) => {
                      const statusConf = STATUS_CONFIG[claim.status];
                      const StatusIcon = statusConf.icon;
                      const strength = evidenceStrength(claim);
                      const isActive = claim.claim_id === activeClaimId;

                      return (
                        <div
                          key={claim.claim_id}
                          className={`border-b border-line cursor-pointer hover:bg-bg/50 ${
                            isActive ? 'border-l-2 border-l-c-blue bg-bg/50' : ''
                          }`}
                          onClick={() =>
                            onClaimClick?.(
                              claim.claim_id,
                              claim.claim_text,
                              claim.start_offset ?? null,
                              claim.end_offset ?? null,
                            )
                          }
                        >
                          <div className="p-3">
                            {/* Status + ID row */}
                            <div className="flex items-center justify-between mb-1 gap-2">
                              <div className="flex items-center gap-2 min-w-0">
                                <StatusIcon
                                  size={14}
                                  className={`${statusConf.colorClass} flex-shrink-0`}
                                />
                                <span
                                  className={`text-xs font-medium whitespace-nowrap ${statusConf.colorClass}`}
                                >
                                  {statusConf.label}
                                </span>
                              </div>
                              <span className="text-xs text-muted font-mono flex-shrink-0">
                                {claim.claim_id.slice(0, 10)}
                              </span>
                            </div>

                            {/* Claim text */}
                            <p className="text-sm text-ink line-clamp-3 leading-relaxed font-medium mt-1">
                              {claim.claim_text}
                            </p>

                            {/* Meta row: section + evidence strength */}
                            <div className="flex items-center justify-between mt-2">
                              <div className="flex items-center gap-2">
                                {claim.section && (
                                  <span className="text-xs text-muted truncate max-w-[120px]">
                                    {claim.section}
                                  </span>
                                )}
                                {claim.start_offset != null && (
                                  <span
                                    className="text-xs text-c-blue underline cursor-pointer"
                                    title="Jump to position in document"
                                  >
                                    pos:{claim.start_offset}
                                  </span>
                                )}
                              </div>

                              {/* Evidence strength bar */}
                              <div
                                className="flex items-center gap-1"
                                title={strength.label}
                              >
                                <div className="flex gap-0.5">
                                  {[0, 1, 2].map((i) => (
                                    <div
                                      key={i}
                                      className={`w-1.5 h-3 ${
                                        (strength.level === 'strong' &&
                                          i <= 2) ||
                                        (strength.level === 'moderate' &&
                                          i <= 1) ||
                                        (strength.level === 'weak' && i === 0)
                                          ? STRENGTH_COLORS[strength.level]
                                          : 'bg-line'
                                      }`}
                                    />
                                  ))}
                                </div>
                                <span className="text-xs text-muted">
                                  {(claim.evidence?.length || 0) +
                                    (claim.source_sentences?.length || 0)}
                                </span>
                              </div>
                            </div>

                            {/* Actions */}
                            <div className="flex flex-row items-center gap-3 mt-2">
                              {claim.status === 'draft' && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleVerify(claim.claim_id);
                                  }}
                                  className="flex items-center gap-1 text-xs text-c-green hover:underline"
                                >
                                  <Check size={10} />
                                  Verify
                                </button>
                              )}
                              {claim.status === 'rejected' && (
                                <button
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    handleVerify(claim.claim_id);
                                  }}
                                  className="flex items-center gap-1 text-xs text-c-amber hover:underline"
                                >
                                  <RotateCcw size={10} />
                                  Reopen
                                </button>
                              )}
                              <button
                                onClick={(e) => {
                                  e.stopPropagation();
                                  handleDelete(claim.claim_id);
                                }}
                                className="flex items-center gap-1 text-xs text-c-red hover:underline"
                              >
                                <X size={10} />
                                Delete
                              </button>
                            </div>
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

      {/* Bottom actions */}
      <div className="p-3 border-t border-line">
        <div className="flex flex-col gap-2">
          <button
            className="w-full py-2 text-sm text-center border border-line hover:bg-bg flex items-center justify-center gap-2"
            onClick={handleExtractClaims}
            disabled={extracting}
          >
            {extracting ? (
              <>
                <AlertCircle size={14} className="animate-pulse" />
                Extracting...
              </>
            ) : (
              <>
                <Beaker size={14} />
                Extract Claims
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

export default ClaimsPanel;
