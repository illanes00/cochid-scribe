import { Node, mergeAttributes } from '@tiptap/core'
import { ReactNodeViewRenderer } from '@tiptap/react'

export interface CitationOptions {
  HTMLAttributes: Record<string, unknown>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    citation: {
      insertCitation: (attributes: {
        bibKey: string
        locator?: string
        style?: 'parenthetical' | 'narrative'
      }) => ReturnType
    }
  }
}

export const Citation = Node.create<CitationOptions>({
  name: 'citation',
  group: 'inline',
  inline: true,
  atom: true,

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      bibKey: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-bib-key'),
        renderHTML: (attributes) => {
          if (!attributes.bibKey) return {}
          return { 'data-bib-key': attributes.bibKey }
        },
      },
      locator: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-locator'),
        renderHTML: (attributes) => {
          if (!attributes.locator) return {}
          return { 'data-locator': attributes.locator }
        },
      },
      style: {
        default: 'parenthetical',
        parseHTML: (element) => element.getAttribute('data-cite-style'),
        renderHTML: (attributes) => {
          return { 'data-cite-style': attributes.style }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-bib-key]',
      },
    ]
  },

  renderHTML({ node, HTMLAttributes }) {
    const bibKey = node.attrs.bibKey || ''
    const locator = node.attrs.locator ? `, ${node.attrs.locator}` : ''
    const displayText =
      node.attrs.style === 'narrative'
        ? `${bibKey}${locator}`
        : `(${bibKey}${locator})`

    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'citation',
        contenteditable: 'false',
      }),
      displayText,
    ]
  },

  addCommands() {
    return {
      insertCitation:
        (attributes) =>
        ({ commands }) => {
          return commands.insertContent({
            type: this.name,
            attrs: attributes,
          })
        },
    }
  },

  addKeyboardShortcuts() {
    return {
      // Ctrl/Cmd + Shift + C to insert citation
      'Mod-Shift-c': () => {
        // This will trigger the citation dialog in the editor
        return true
      },
    }
  },
})

export default Citation
