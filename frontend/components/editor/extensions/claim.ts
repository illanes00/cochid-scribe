import { Mark, mergeAttributes } from '@tiptap/core'

export interface ClaimOptions {
  HTMLAttributes: Record<string, unknown>
}

declare module '@tiptap/core' {
  interface Commands<ReturnType> {
    claim: {
      setClaim: (attributes: { claimId: string; claimType?: string }) => ReturnType
      unsetClaim: () => ReturnType
      toggleClaim: (attributes: { claimId: string; claimType?: string }) => ReturnType
    }
  }
}

export const Claim = Mark.create<ClaimOptions>({
  name: 'claim',

  addOptions() {
    return {
      HTMLAttributes: {},
    }
  },

  addAttributes() {
    return {
      claimId: {
        default: null,
        parseHTML: (element) => element.getAttribute('data-claim-id'),
        renderHTML: (attributes) => {
          if (!attributes.claimId) return {}
          return { 'data-claim-id': attributes.claimId }
        },
      },
      claimType: {
        default: 'MIXED',
        parseHTML: (element) => element.getAttribute('data-claim-type'),
        renderHTML: (attributes) => {
          return { 'data-claim-type': attributes.claimType }
        },
      },
      status: {
        default: 'draft',
        parseHTML: (element) => element.getAttribute('data-claim-status'),
        renderHTML: (attributes) => {
          return { 'data-claim-status': attributes.status }
        },
      },
    }
  },

  parseHTML() {
    return [
      {
        tag: 'span[data-claim-id]',
      },
    ]
  },

  renderHTML({ HTMLAttributes }) {
    return [
      'span',
      mergeAttributes(this.options.HTMLAttributes, HTMLAttributes, {
        class: 'claim-highlight',
      }),
      0,
    ]
  },

  addCommands() {
    return {
      setClaim:
        (attributes) =>
        ({ commands }) => {
          return commands.setMark(this.name, attributes)
        },
      unsetClaim:
        () =>
        ({ commands }) => {
          return commands.unsetMark(this.name)
        },
      toggleClaim:
        (attributes) =>
        ({ commands }) => {
          return commands.toggleMark(this.name, attributes)
        },
    }
  },
})

export default Claim
