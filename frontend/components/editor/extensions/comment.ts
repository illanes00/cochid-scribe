import { Mark, mergeAttributes } from '@tiptap/core'

export interface CommentOptions {
  HTMLAttributes: Record<string, unknown>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    comment: {
      setComment: (attributes: { commentId: string }) => ReturnType
      unsetComment: () => ReturnType
      toggleComment: (attributes: { commentId: string }) => ReturnType
    }
  }
}

export const Comment = Mark.create<CommentOptions>({
  name: 'comment',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      commentId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-comment-id'),
        renderHTML: (attributes) => {
          if (!attributes.commentId) return {}
          return { 'data-comment-id': attributes.commentId }
        },
      },
      resolved: {
        default: false,
        parseHTML: (element) => element.getAttribute('data-comment-resolved') === 'true',
        renderHTML: (attributes) => {
          return { 'data-comment-resolved': String(Boolean(attributes.resolved)) }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-comment-id]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'comment-mark',
      }),
      0,
    ]
  },

  addCommands() {
    return {
      setComment:
        (attributes) =>
        ({ commands }) => {
          return commands.setMark(this.name, attributes)
        },
      unsetComment:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name)
        },
      toggleComment:
        (attributes) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, attributes)
        },
    }
  },
})

export default Comment
