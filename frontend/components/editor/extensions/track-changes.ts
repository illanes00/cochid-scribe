import { Extension, Mark, mergeAttributes } from '@tiptap/core'
import { Plugin } from '@tiptap/pm/state'

export interface ChangeOptions {
  HTMLAttributes: Record<string, unknown>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    trackChanges: {
      setTrackChanges: (enabled: boolean) => ReturnType
    }
  }
}

export const ChangeMark = Mark.create<ChangeOptions>({
  name: 'change',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      kind: {
        default: 'insert',
        parseHTML: (element) => element.getAttribute('data-change-kind') || 'insert',
        renderHTML: (attributes) => {
          return { 'data-change-kind': attributes.kind }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-change-kind]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    const kind = HTMLAttributes['data-change-kind'] || 'insert'
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: `change-mark change-${kind}`,
      }),
      0,
    ]
  },
})

export const TrackChanges = Extension.create({
  name: 'trackChanges',

  addStorage() {
    return {
      enabled: false,
    }
  },

  addCommands() {
    return {
      setTrackChanges:
        (enabled: boolean) =>
        ({ editor }) => {
          editor.storage.trackChanges.enabled = enabled
          return true
        },
    }
  },

  addProseMirrorPlugins() {
    const extension = this
    return [
      new Plugin({
        appendTransaction(transactions, _oldState, newState) {
          if (!extension.storage.enabled) return

          let tr = newState.tr
          let modified = false

          transactions.forEach((transaction) => {
            if (!transaction.docChanged) return
            transaction.steps.forEach((step: any) => {
              if (!step || typeof step.from !== 'number' || !step.slice) return
              const sliceSize = step.slice.size || 0
              if (sliceSize <= 0) return
              const mappedFrom = transaction.mapping.map(step.from)
              const insertFrom = mappedFrom
              const insertTo = mappedFrom + sliceSize
              const markType = newState.schema.marks.change
              if (!markType) return
              tr.addMark(insertFrom, insertTo, markType.create({ kind: 'insert' }))
              modified = true
            })
          })

          if (modified) {
            tr.setMeta('addToHistory', false)
            return tr
          }
        },
      }),
    ]
  },
})

export default TrackChanges
