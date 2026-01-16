'use client'

import { useEffect, useState } from 'react'
import { Comment, CommentCreate, commentsApi } from '@/lib/api'

interface CommentsPanelProps {
  documentSlug: string
  sourceProvider?: string | null
  onSelectComment?: (anchorId: string) => void
  onCommentsChange?: (comments: Comment[]) => void
}

interface CommentThread {
  anchorId: string
  root?: Comment
  replies: Comment[]
}

function extractMentions(text: string): string[] {
  const matches = text.match(/@\w+/g)
  return matches ? matches.map((m) => m.slice(1)) : []
}

function renderMentions(text: string) {
  const parts = text.split(/(@\w+)/g)
  return parts.map((part, idx) => {
    if (part.startsWith('@')) {
      return (
        <span key={`${part}-${idx}`} className="comment-mention">
          {part}
        </span>
      )
    }
    return <span key={`${part}-${idx}`}>{part}</span>
  })
}

export function CommentsPanel({
  documentSlug,
  sourceProvider,
  onSelectComment,
  onCommentsChange,
}: CommentsPanelProps) {
  const [comments, setComments] = useState<Comment[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [syncing, setSyncing] = useState(false)
  const [creating, setCreating] = useState(false)
  const [content, setContent] = useState('')
  const [replyFor, setReplyFor] = useState<string | null>(null)
  const [replyContent, setReplyContent] = useState('')
  const [showResolved, setShowResolved] = useState(true)
  const [showMentionsOnly, setShowMentionsOnly] = useState(false)

  async function loadComments() {
    try {
      setLoading(true)
      setError(null)
      const data = await commentsApi.list(documentSlug)
      setComments(data)
      onCommentsChange?.(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load comments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!documentSlug || documentSlug === 'new') {
      setLoading(false)
      return
    }
    loadComments()
  }, [documentSlug])

  async function handleSync() {
    if (!documentSlug || documentSlug === 'new') return
    try {
      setSyncing(true)
      await commentsApi.syncGoogle(documentSlug)
      await loadComments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to sync comments')
    } finally {
      setSyncing(false)
    }
  }

  async function handleCreate(localOnly: boolean) {
    if (!content.trim()) return
    const payload: CommentCreate = { content: content.trim() }
    try {
      setCreating(true)
      if (localOnly || sourceProvider !== 'google') {
        await commentsApi.create(documentSlug, payload)
      } else {
        await commentsApi.createGoogle(documentSlug, payload)
      }
      setContent('')
      await loadComments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create comment')
    } finally {
      setCreating(false)
    }
  }

  async function handleReply(anchorId: string, parentId?: string | null) {
    if (!replyContent.trim()) return
    const payload: CommentCreate = {
      content: replyContent.trim(),
      parent_id: parentId || null,
      anchor_id: anchorId,
    }
    try {
      setCreating(true)
      await commentsApi.create(documentSlug, payload)
      setReplyContent('')
      setReplyFor(null)
      await loadComments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create reply')
    } finally {
      setCreating(false)
    }
  }

  async function toggleThreadResolved(thread: CommentThread, resolved: boolean) {
    try {
      setCreating(true)
      const updates = [thread.root, ...thread.replies].filter(Boolean) as Comment[]
      await Promise.all(
        updates.map((comment) => commentsApi.update(comment.id, { resolved }))
      )
      await loadComments()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to update comments')
    } finally {
      setCreating(false)
    }
  }

  const threads = comments.reduce<Record<string, CommentThread>>((acc, comment) => {
    const anchorId = comment.anchor_id || comment.id
    if (!acc[anchorId]) {
      acc[anchorId] = { anchorId, replies: [] }
    }
    if (!comment.parent_id) {
      acc[anchorId].root = comment
    } else {
      acc[anchorId].replies.push(comment)
    }
    return acc
  }, {})

  const threadList = Object.values(threads)
    .filter((thread) => {
      if (showResolved) return true
      const root = thread.root || thread.replies[0]
      if (!root) return true
      const resolved = ![root, ...thread.replies].some(
        (comment) => comment && !comment.resolved
      )
      return !resolved
    })
    .filter((thread) => {
      if (!showMentionsOnly) return true
      const items = [thread.root, ...thread.replies].filter(Boolean) as Comment[]
      return items.some((item) => extractMentions(item.content).length > 0)
    })
    .sort((a, b) => {
      const aDate = a.root?.created_at || a.replies[0]?.created_at || ''
      const bDate = b.root?.created_at || b.replies[0]?.created_at || ''
      return new Date(bDate).getTime() - new Date(aDate).getTime()
    })

  return (
    <div className="flex flex-col h-full">
      <div className="p-3 border-b border-line">
        <div className="flex items-center justify-between">
          <h2 className="font-medium text-ink">Comments</h2>
          <div className="flex items-center gap-3 text-xs">
            <button
              className="underline"
              onClick={() => setShowMentionsOnly((v) => !v)}
            >
              {showMentionsOnly ? 'All comments' : 'Mentions'}
            </button>
            <button
              className="underline"
              onClick={() => setShowResolved((v) => !v)}
            >
              {showResolved ? 'Hide resolved' : 'Show resolved'}
            </button>
            <button
              className="underline"
              onClick={handleSync}
              disabled={syncing || sourceProvider !== 'google'}
              title={sourceProvider === 'google' ? 'Sync from Google' : 'Connect Google first'}
            >
              {syncing ? 'Syncing...' : 'Sync'}
            </button>
          </div>
        </div>
        {error && <div className="text-xs text-c-red mt-2">{error}</div>}
      </div>

      <div className="p-3 border-b border-line">
        <textarea
          className="w-full p-2 text-sm border border-line bg-paper resize-none h-16 focus:outline-none focus:border-ink"
          placeholder="Add a comment..."
          value={content}
          onChange={(e) => setContent(e.target.value)}
        />
        <div className="flex gap-2 mt-2">
          <button
            className="btn btn-sm"
            onClick={() => handleCreate(true)}
            disabled={creating}
          >
            Add (local)
          </button>
          <button
            className="btn btn-sm btn-primary"
            onClick={() => handleCreate(false)}
            disabled={creating || sourceProvider !== 'google'}
            title={sourceProvider === 'google' ? 'Create on Google' : 'Connect Google first'}
          >
            Add to Google
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="p-4 text-muted">Loading comments...</div>
        ) : threadList.length === 0 ? (
          <div className="p-4 text-center text-muted">No comments yet</div>
        ) : (
          <ul className="divide-y divide-line">
            {threadList.map((thread) => {
              const root = thread.root || thread.replies[0]
              if (!root) return null
              const threadResolved = ![root, ...thread.replies].some(
                (comment) => comment && !comment.resolved
              )
              return (
                <li key={thread.anchorId} className="p-3">
                  <div
                    className="cursor-pointer hover:bg-bg p-2 -mx-2"
                    onClick={() => onSelectComment?.(thread.anchorId)}
                  >
                    <div className="text-xs text-muted">
                      {root.author || root.provider} • {new Date(root.created_at).toLocaleString()}
                      {threadResolved && (
                        <span className="ml-2 text-c-green">Resolved</span>
                      )}
                    </div>
                    {root.quote && (
                      <div className="text-xs text-muted mt-1 italic">"{root.quote}"</div>
                    )}
                    <div className={`text-sm text-ink mt-1 ${threadResolved ? 'line-through text-muted' : ''}`}>
                      {renderMentions(root.content)}
                    </div>
                  </div>

                  {thread.replies.length > 0 && (
                    <div className="mt-2 space-y-2 pl-3 border-l border-line">
                      {thread.replies.map((reply) => (
                        <div key={reply.id}>
                          <div className="text-xs text-muted">
                            {reply.author || reply.provider} • {new Date(reply.created_at).toLocaleString()}
                          </div>
                          <div className="text-sm text-ink mt-1">
                            {renderMentions(reply.content)}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="mt-2">
                    {replyFor === thread.anchorId ? (
                      <div className="flex flex-col gap-2">
                        <textarea
                          className="w-full p-2 text-xs border border-line bg-paper resize-none h-16 focus:outline-none focus:border-ink"
                          placeholder="Write a reply..."
                          value={replyContent}
                          onChange={(e) => setReplyContent(e.target.value)}
                        />
                        <div className="flex gap-2">
                          <button
                            className="btn btn-sm btn-primary"
                            onClick={() => handleReply(thread.anchorId, root.id)}
                            disabled={creating}
                          >
                            Reply
                          </button>
                          <button
                            className="btn btn-sm"
                            onClick={() => {
                              setReplyFor(null)
                              setReplyContent('')
                            }}
                          >
                            Cancel
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-3 text-xs">
                        <button
                          className="underline text-muted"
                          onClick={() => setReplyFor(thread.anchorId)}
                        >
                          Reply
                        </button>
                        <button
                          className="underline text-muted"
                          onClick={() => toggleThreadResolved(thread, !threadResolved)}
                          disabled={creating}
                        >
                          {threadResolved ? 'Reopen' : 'Resolve'}
                        </button>
                      </div>
                    )}
                  </div>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    </div>
  )
}

export default CommentsPanel
