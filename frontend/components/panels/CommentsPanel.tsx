'use client';

import { useEffect, useMemo, useState } from 'react';
import {
  MessageSquare,
  Send,
  ChevronDown,
  ChevronRight,
  CheckCircle,
  Circle,
  Mail,
  Globe,
  MapPin,
} from 'lucide-react';
import { Comment, CommentCreate, commentsApi } from '@/lib/api';
import { renderMarkdown } from '@/lib/markdown';

interface CommentsPanelProps {
  documentSlug: string;
  sourceProvider?: string | null;
  onSelectComment?: (anchorId: string) => void;
  onCommentsChange?: (comments: Comment[]) => void;
}

interface CommentThread {
  anchorId: string;
  root?: Comment;
  replies: Comment[];
}

type SourceFilter = 'all' | 'google' | 'email' | 'local';
type StatusFilter = 'all' | 'pending' | 'resolved';

const SOURCE_LABELS: Record<string, { label: string; icon: typeof Globe; badgeClass: string }> = {
  google: { label: 'Google', icon: Globe, badgeClass: 'provider-badge google' },
  email: { label: 'Email', icon: Mail, badgeClass: 'provider-badge email' },
  local: { label: 'Scribe', icon: MapPin, badgeClass: 'provider-badge scribe' },
};

function extractMentions(text: string): string[] {
  const matches = text.match(/@\w+/g);
  return matches ? matches.map((m) => m.slice(1)) : [];
}

function renderMentions(text: string) {
  const parts = text.split(/(@\w+)/g);
  return parts.map((part, idx) => {
    if (part.startsWith('@')) {
      return (
        <span key={`${part}-${idx}`} className="comment-mention">
          {part}
        </span>
      );
    }
    return <span key={`${part}-${idx}`}>{part}</span>;
  });
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

function getSourceKey(provider: string): string {
  if (provider === 'google') return 'google';
  if (provider === 'email' || provider === 'cif') return 'email';
  return 'local';
}

function isThreadResolved(thread: CommentThread): boolean {
  const items = [thread.root, ...thread.replies].filter(Boolean) as Comment[];
  return items.length > 0 && items.every((c) => c.resolved);
}

function threadHasReplies(thread: CommentThread): boolean {
  return thread.replies.length > 0;
}

export function CommentsPanel({
  documentSlug,
  sourceProvider,
  onSelectComment,
  onCommentsChange,
}: CommentsPanelProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [creating, setCreating] = useState(false);
  const [content, setContent] = useState('');
  const [replyFor, setReplyFor] = useState<string | null>(null);
  const [replyContent, setReplyContent] = useState('');
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('all');
  const [sourceFilter, setSourceFilter] = useState<SourceFilter>('all');
  const [authorFilter, setAuthorFilter] = useState<string>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [collapsedThreads, setCollapsedThreads] = useState<Set<string>>(
    new Set(),
  );

  async function loadComments() {
    try {
      setLoading(true);
      setError(null);
      const data = await commentsApi.list(documentSlug);
      setComments(data);
      onCommentsChange?.(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comments');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!documentSlug || documentSlug === 'new') {
      setLoading(false);
      return;
    }
    loadComments();
  }, [documentSlug]);

  async function handleSync() {
    if (!documentSlug || documentSlug === 'new') return;
    try {
      setSyncing(true);
      await commentsApi.syncGoogle(documentSlug);
      await loadComments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync comments');
    } finally {
      setSyncing(false);
    }
  }

  async function handleCreate(localOnly: boolean) {
    if (!content.trim()) return;
    const payload: CommentCreate = { content: content.trim() };
    try {
      setCreating(true);
      if (localOnly || sourceProvider !== 'google') {
        await commentsApi.create(documentSlug, payload);
      } else {
        await commentsApi.createGoogle(documentSlug, payload);
      }
      setContent('');
      await loadComments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create comment');
    } finally {
      setCreating(false);
    }
  }

  async function handleReply(anchorId: string, parentId?: string | null) {
    if (!replyContent.trim()) return;
    const payload: CommentCreate = {
      content: replyContent.trim(),
      parent_id: parentId || null,
      anchor_id: anchorId,
    };
    try {
      setCreating(true);
      await commentsApi.create(documentSlug, payload);
      setReplyContent('');
      setReplyFor(null);
      await loadComments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create reply');
    } finally {
      setCreating(false);
    }
  }

  async function toggleThreadResolved(
    thread: CommentThread,
    resolved: boolean,
  ) {
    try {
      setCreating(true);
      const updates = [thread.root, ...thread.replies].filter(
        Boolean,
      ) as Comment[];
      await Promise.all(
        updates.map((comment) => commentsApi.update(comment.id, { resolved })),
      );
      await loadComments();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update comments');
    } finally {
      setCreating(false);
    }
  }

  function toggleCollapse(anchorId: string) {
    setCollapsedThreads((prev) => {
      const next = new Set(prev);
      if (next.has(anchorId)) {
        next.delete(anchorId);
      } else {
        next.add(anchorId);
      }
      return next;
    });
  }

  // Build threads
  const threads = comments.reduce<Record<string, CommentThread>>(
    (acc, comment) => {
      const anchorId = comment.anchor_id || comment.id;
      if (!acc[anchorId]) {
        acc[anchorId] = { anchorId, replies: [] };
      }
      if (!comment.parent_id) {
        acc[anchorId].root = comment;
      } else {
        acc[anchorId].replies.push(comment);
      }
      return acc;
    },
    {},
  );

  // Unique authors for filter
  const uniqueAuthors = useMemo(() => {
    const authors = new Set<string>();
    comments.forEach((c) => {
      const name = c.author || c.provider;
      if (name) authors.add(name);
    });
    return Array.from(authors).sort();
  }, [comments]);

  // Stats
  const stats = useMemo(() => {
    const allThreads = Object.values(threads);
    const pending = allThreads.filter((t) => !isThreadResolved(t)).length;
    const resolved = allThreads.filter((t) => isThreadResolved(t)).length;
    const withoutReply = allThreads.filter(
      (t) => !isThreadResolved(t) && !threadHasReplies(t),
    ).length;
    return { total: allThreads.length, pending, resolved, withoutReply };
  }, [threads]);

  // Filtered threads
  const threadList = Object.values(threads)
    .filter((thread) => {
      if (statusFilter === 'pending') return !isThreadResolved(thread);
      if (statusFilter === 'resolved') return isThreadResolved(thread);
      return true;
    })
    .filter((thread) => {
      if (sourceFilter === 'all') return true;
      const root = thread.root || thread.replies[0];
      if (!root) return true;
      return getSourceKey(root.provider) === sourceFilter;
    })
    .filter((thread) => {
      if (authorFilter === 'all') return true;
      const items = [thread.root, ...thread.replies].filter(
        Boolean,
      ) as Comment[];
      return items.some((c) => (c.author || c.provider) === authorFilter);
    })
    .sort((a, b) => {
      const aDate = a.root?.created_at || a.replies[0]?.created_at || '';
      const bDate = b.root?.created_at || b.replies[0]?.created_at || '';
      return new Date(bDate).getTime() - new Date(aDate).getTime();
    });

  const SourceBadge = ({ provider }: { provider: string }) => {
    const key = getSourceKey(provider);
    const config = SOURCE_LABELS[key] || SOURCE_LABELS.local;
    const Icon = config.icon;
    return (
      <span className={config.badgeClass} title={config.label}>
        <Icon size={9} />
        {config.label}
      </span>
    );
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header with stats */}
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <MessageSquare size={14} className="text-muted" />
            <h2 className="font-medium text-ink text-sm">Comments</h2>
            <span className="text-xs text-muted">({stats.total})</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              className="p-1 hover:bg-bg text-muted"
              onClick={() => setShowFilters((v) => !v)}
              title="Toggle filters"
            >
              <ChevronDown
                size={14}
                className={
                  showFilters
                    ? 'rotate-180 transition-transform'
                    : 'transition-transform'
                }
              />
            </button>
            <button
              className="text-xs underline text-muted"
              onClick={handleSync}
              disabled={syncing || sourceProvider !== 'google'}
              title={
                sourceProvider === 'google'
                  ? 'Sync from Google'
                  : 'Connect Google first'
              }
            >
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
          </div>
        </div>

        {/* Pending counter */}
        {stats.pending > 0 && (
          <div className="flex items-center gap-3 mt-2 text-xs">
            <span className="flex items-center gap-1 text-c-amber font-medium">
              <Circle size={8} className="fill-current" />
              {stats.pending} pending
            </span>
            {stats.withoutReply > 0 && (
              <span className="text-c-red">
                {stats.withoutReply} without reply
              </span>
            )}
            <span className="flex items-center gap-1 text-c-green">
              <CheckCircle size={8} />
              {stats.resolved} resolved
            </span>
          </div>
        )}

        {error && <div className="text-xs text-c-red mt-2">{error}</div>}
      </div>

      {/* Filters */}
      {showFilters && (
        <div className="p-2 border-b border-line space-y-2">
          {/* Status filter */}
          <div className="flex gap-1">
            {(['all', 'pending', 'resolved'] as StatusFilter[]).map((f) => (
              <button
                key={f}
                onClick={() => setStatusFilter(f)}
                className={`px-2 py-1 text-xs ${
                  statusFilter === f
                    ? 'bg-ink text-paper'
                    : 'text-muted hover:bg-bg'
                }`}
              >
                {f === 'all'
                  ? 'All'
                  : f === 'pending'
                    ? `Pending (${stats.pending})`
                    : `Resolved (${stats.resolved})`}
              </button>
            ))}
          </div>

          {/* Source filter */}
          <div className="flex gap-1">
            {(['all', 'google', 'email', 'local'] as SourceFilter[]).map(
              (f) => (
                <button
                  key={f}
                  onClick={() => setSourceFilter(f)}
                  className={`px-2 py-1 text-xs ${
                    sourceFilter === f
                      ? 'bg-ink text-paper'
                      : 'text-muted hover:bg-bg'
                  }`}
                >
                  {f === 'all'
                    ? 'All sources'
                    : SOURCE_LABELS[f]?.label || f}
                </button>
              ),
            )}
          </div>

          {/* Author filter */}
          {uniqueAuthors.length > 1 && (
            <select
              value={authorFilter}
              onChange={(e) => setAuthorFilter(e.target.value)}
              className="w-full text-xs py-1 px-2 border border-line bg-paper text-ink"
            >
              <option value="all">All authors</option>
              {uniqueAuthors.map((author) => (
                <option key={author} value={author}>
                  {author}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* New comment form */}
      <div className="p-3 border-b border-line">
        <textarea
          className="w-full p-2 text-sm border border-line bg-paper resize-none h-14 focus:outline-none focus:border-ink"
          placeholder="Add a comment..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
              handleCreate(sourceProvider !== 'google');
            }
          }}
        />
        <div className="flex gap-2 mt-2">
          <button
            className="btn btn-sm"
            onClick={() => handleCreate(true)}
            disabled={creating || !content.trim()}
          >
            Add Scribe
          </button>
          {sourceProvider === 'google' && (
            <button
              className="btn btn-sm btn-primary"
              onClick={() => handleCreate(false)}
              disabled={creating || !content.trim()}
            >
              Add to Google
            </button>
          )}
        </div>
      </div>

      {/* Thread list */}
      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-muted text-sm">Loading comments...</div>
        ) : threadList.length === 0 ? (
          <div className="p-6 text-center">
            <MessageSquare size={24} className="mx-auto text-muted mb-2" />
            <p className="text-sm text-muted">
              {stats.total === 0
                ? 'No comments yet. Start a discussion.'
                : 'No comments match the current filters.'}
            </p>
          </div>
        ) : (
          <ul>
            {threadList.map((thread) => {
              const root = thread.root || thread.replies[0];
              if (!root) return null;
              const resolved = isThreadResolved(thread);
              const hasReplies = threadHasReplies(thread);
              const collapsed = collapsedThreads.has(thread.anchorId);
              return (
                <li
                  key={thread.anchorId}
                  className={`comment-bubble ${resolved ? 'resolved' : ''}`}
                >
                  {/* Root comment */}
                  <div
                    className="cursor-pointer hover:bg-bg/30 group"
                    onClick={() => onSelectComment?.(thread.anchorId)}
                  >
                    {/* Author row */}
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="comment-author truncate">
                          {root.author || (root.provider === 'local' ? 'Scribe' : root.provider)}
                        </span>
                        <SourceBadge provider={root.provider} />
                      </div>
                      <div className="flex items-center gap-2">
                        {resolved && (
                          <CheckCircle
                            size={12}
                            className="text-c-green flex-shrink-0"
                          />
                        )}
                        {hasReplies && (
                          <span className="text-xs text-muted">
                            {thread.replies.length}
                          </span>
                        )}
                        {!hasReplies && !resolved && (
                          <span
                            className="text-xs text-c-red font-medium"
                            title="No reply yet"
                          >
                            !
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Meta: time + document link */}
                    <div className="comment-meta flex items-center gap-2">
                      <span>{timeAgo(root.created_at)}</span>
                      {!root.anchor_id && documentSlug && (
                        <a
                          href={`/documents/${documentSlug}`}
                          className="text-c-blue hover:underline"
                          onClick={(e) => e.stopPropagation()}
                        >
                          View document
                        </a>
                      )}
                    </div>

                    {/* Quoted text */}
                    {root.quote && (
                      <div className="text-xs text-muted mt-1.5 pl-3.5 border-l-2 border-line italic line-clamp-2">
                        {root.quote}
                      </div>
                    )}

                    {/* Comment content — rendered as markdown */}
                    <div
                      className={`comment-content ${resolved ? 'line-through opacity-60' : ''}`}
                    >
                      {renderMarkdown(root.content)}
                    </div>
                  </div>

                  {/* Replies section */}
                  {hasReplies && (
                    <div className="px-3">
                      <button
                        className="flex items-center gap-1 text-xs text-muted hover:text-ink py-1"
                        onClick={() => toggleCollapse(thread.anchorId)}
                      >
                        {collapsed ? (
                          <ChevronRight size={12} />
                        ) : (
                          <ChevronDown size={12} />
                        )}
                        {thread.replies.length}{' '}
                        {thread.replies.length === 1 ? 'reply' : 'replies'}
                      </button>

                      {!collapsed && (
                        <div className="ml-3 border-l-2 border-line pl-3 pb-2 space-y-2">
                          {thread.replies.map((reply) => (
                            <div key={reply.id}>
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-medium text-ink">
                                  {reply.author || (reply.provider === 'local' ? 'Scribe' : reply.provider)}
                                </span>
                                <SourceBadge provider={reply.provider} />
                                <span className="text-xs text-muted">
                                  {timeAgo(reply.created_at)}
                                </span>
                              </div>
                              <div className="comment-content mt-0.5 ml-3">
                                {renderMarkdown(reply.content)}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}

                  {/* Inline reply form */}
                  {replyFor === thread.anchorId ? (
                    <div className="px-3 pb-3">
                      <div className="ml-3 border-l-2 border-c-blue pl-3">
                        <textarea
                          className="w-full p-2 text-xs border border-line bg-paper resize-none h-14 focus:outline-none focus:border-c-blue"
                          placeholder="Write a reply..."
                          value={replyContent}
                          onChange={(e) => setReplyContent(e.target.value)}
                          onKeyDown={(e) => {
                            if (
                              e.key === 'Enter' &&
                              (e.metaKey || e.ctrlKey)
                            ) {
                              handleReply(thread.anchorId, root.id);
                            }
                            if (e.key === 'Escape') {
                              setReplyFor(null);
                              setReplyContent('');
                            }
                          }}
                          autoFocus
                        />
                        <div className="flex items-center gap-2 mt-1">
                          <button
                            className="btn btn-sm btn-primary flex items-center gap-1"
                            onClick={() =>
                              handleReply(thread.anchorId, root.id)
                            }
                            disabled={creating || !replyContent.trim()}
                          >
                            <Send size={10} />
                            Reply
                          </button>
                          <button
                            className="text-xs text-muted hover:text-ink"
                            onClick={() => {
                              setReplyFor(null);
                              setReplyContent('');
                            }}
                          >
                            Cancel
                          </button>
                          <span className="text-xs text-muted ml-auto">
                            Ctrl+Enter to send
                          </span>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="px-3 pb-2 flex flex-row items-center gap-3 text-xs">
                      <button
                        className="text-muted hover:text-ink whitespace-nowrap"
                        onClick={() => setReplyFor(thread.anchorId)}
                      >
                        Reply
                      </button>
                      <button
                        className="text-muted hover:text-ink whitespace-nowrap"
                        onClick={() =>
                          toggleThreadResolved(thread, !resolved)
                        }
                        disabled={creating}
                      >
                        {resolved ? 'Reopen' : 'Resolve'}
                      </button>
                    </div>
                  )}
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );
}

export default CommentsPanel;
