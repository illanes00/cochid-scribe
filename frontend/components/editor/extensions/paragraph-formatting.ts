import { Extension } from '@tiptap/core'

export interface ParagraphFormattingOptions {
  types: string[]
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    paragraphFormatting: {
      /**
       * Set paragraph margins
       */
      setParagraphMargins: (margins: {
        left?: string
        right?: string
        top?: string
        bottom?: string
      }) => ReturnType
      /**
       * Set first-line indent
       */
      setFirstLineIndent: (indent: string) => ReturnType
      /**
       * Reset paragraph formatting to defaults
       */
      resetParagraphFormatting: () => ReturnType
    }
  }
}

/**
 * ParagraphFormatting extension for TipTap.
 *
 * Adds margin and text-indent attributes to paragraphs and headings,
 * allowing integration with a visual ruler component.
 *
 * Usage:
 * ```ts
 * editor.chain().focus().setParagraphMargins({ left: '72px', right: '72px' }).run()
 * editor.chain().focus().setFirstLineIndent('36px').run()
 * ```
 */
export const ParagraphFormatting = Extension.create<ParagraphFormattingOptions>({
  name: 'paragraphFormatting',

  addOptions() {
    return {
      types: ['paragraph', 'heading'],
    }
  },

  addGlobalAttributes() {
    return [
      {
        types: this.options.types,
        attributes: {
          marginLeft: {
            default: null,
            parseHTML: element => element.style.marginLeft || null,
            renderHTML: attributes => {
              if (!attributes.marginLeft) return {}
              return { style: `margin-left: ${attributes.marginLeft}` }
            },
          },
          marginRight: {
            default: null,
            parseHTML: element => element.style.marginRight || null,
            renderHTML: attributes => {
              if (!attributes.marginRight) return {}
              return { style: `margin-right: ${attributes.marginRight}` }
            },
          },
          marginTop: {
            default: null,
            parseHTML: element => element.style.marginTop || null,
            renderHTML: attributes => {
              if (!attributes.marginTop) return {}
              return { style: `margin-top: ${attributes.marginTop}` }
            },
          },
          marginBottom: {
            default: null,
            parseHTML: element => element.style.marginBottom || null,
            renderHTML: attributes => {
              if (!attributes.marginBottom) return {}
              return { style: `margin-bottom: ${attributes.marginBottom}` }
            },
          },
          textIndent: {
            default: null,
            parseHTML: element => element.style.textIndent || null,
            renderHTML: attributes => {
              if (!attributes.textIndent) return {}
              return { style: `text-indent: ${attributes.textIndent}` }
            },
          },
        },
      },
    ]
  },

  addCommands() {
    return {
      setParagraphMargins:
        (margins) =>
        ({ commands }) => {
          const attrs: Record<string, string | null> = {}
          if (margins.left !== undefined) attrs.marginLeft = margins.left
          if (margins.right !== undefined) attrs.marginRight = margins.right
          if (margins.top !== undefined) attrs.marginTop = margins.top
          if (margins.bottom !== undefined) attrs.marginBottom = margins.bottom

          return this.options.types.every(type =>
            commands.updateAttributes(type, attrs)
          )
        },

      setFirstLineIndent:
        (indent) =>
        ({ commands }) => {
          return this.options.types.every(type =>
            commands.updateAttributes(type, { textIndent: indent })
          )
        },

      resetParagraphFormatting:
        () =>
        ({ commands }) => {
          return this.options.types.every(type =>
            commands.updateAttributes(type, {
              marginLeft: null,
              marginRight: null,
              marginTop: null,
              marginBottom: null,
              textIndent: null,
            })
          )
        },
    }
  },
})

export default ParagraphFormatting
