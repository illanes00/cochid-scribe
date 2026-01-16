import { Extension } from '@tiptap/core'
import Suggestion, { SuggestionOptions } from '@tiptap/suggestion'

export interface SlashCommandItem {
  title: string
  description: string
  icon: string
  command: (props: { editor: any; range: any }) => void
}

const slashCommands: SlashCommandItem[] = [
  {
    title: 'Heading 1',
    description: 'Large section heading',
    icon: 'H1',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 1 }).run()
    },
  },
  {
    title: 'Heading 2',
    description: 'Medium section heading',
    icon: 'H2',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 2 }).run()
    },
  },
  {
    title: 'Heading 3',
    description: 'Small section heading',
    icon: 'H3',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setNode('heading', { level: 3 }).run()
    },
  },
  {
    title: 'Bullet List',
    description: 'Create a bullet list',
    icon: '•',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBulletList().run()
    },
  },
  {
    title: 'Numbered List',
    description: 'Create a numbered list',
    icon: '1.',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleOrderedList().run()
    },
  },
  {
    title: 'Quote',
    description: 'Insert a blockquote',
    icon: '"',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleBlockquote().run()
    },
  },
  {
    title: 'Code Block',
    description: 'Insert a code block',
    icon: '</>',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleCodeBlock().run()
    },
  },
  {
    title: 'Horizontal Rule',
    description: 'Insert a divider',
    icon: '—',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).setHorizontalRule().run()
    },
  },
  {
    title: 'Task List',
    description: 'Create a checklist',
    icon: '☑',
    command: ({ editor, range }) => {
      editor.chain().focus().deleteRange(range).toggleTaskList().run()
    },
  },
  {
    title: 'Image',
    description: 'Insert an image by URL',
    icon: '🖼',
    command: ({ editor, range }) => {
      const url = window.prompt('Image URL')
      if (!url) return
      editor.chain().focus().deleteRange(range).setImage({ src: url }).run()
    },
  },
  {
    title: 'Table',
    description: 'Insert a 3x3 table',
    icon: '▦',
    command: ({ editor, range }) => {
      editor
        .chain()
        .focus()
        .deleteRange(range)
        .insertTable({ rows: 3, cols: 3, withHeaderRow: true })
        .run()
    },
  },
]

function createSlashMenu() {
  let component: HTMLDivElement | null = null
  let list: HTMLUListElement | null = null
  let items: SlashCommandItem[] = []
  let selectedIndex = 0

  const renderItems = (props: { command: (item: SlashCommandItem) => void }) => {
    if (!list) return
    const listEl = list
    // Clear existing items by removing all children
    while (listEl.firstChild) {
      listEl.removeChild(listEl.firstChild)
    }

    if (items.length === 0) {
      const empty = document.createElement('li')
      empty.className = 'slash-command-empty'
      empty.textContent = 'No results'
      listEl.appendChild(empty)
      return
    }

    items.forEach((item, index) => {
      const button = document.createElement('button')
      button.type = 'button'
      button.className = `slash-command-item ${index === selectedIndex ? 'is-active' : ''}`
      button.addEventListener('click', () => props.command(item))

      const icon = document.createElement('span')
      icon.className = 'slash-command-icon'
      icon.textContent = item.icon

      const content = document.createElement('span')
      content.className = 'slash-command-content'

      const title = document.createElement('span')
      title.className = 'slash-command-title'
      title.textContent = item.title

      const description = document.createElement('span')
      description.className = 'slash-command-description'
      description.textContent = item.description

      content.appendChild(title)
      content.appendChild(description)
      button.appendChild(icon)
      button.appendChild(content)
      listEl.appendChild(button)
    })
  }

  return {
    onStart: (props: any) => {
      items = props.items
      selectedIndex = 0
      component = document.createElement('div')
      component.className = 'slash-command-menu'

      list = document.createElement('ul')
      list.className = 'slash-command-list'
      component.appendChild(list)

      document.body.appendChild(component)
      renderItems(props)

      if (props.clientRect) {
        const rect = props.clientRect()
        component.style.left = `${Math.min(rect.left, window.innerWidth - 320)}px`
        component.style.top = `${rect.bottom + 6}px`
      }
    },
    onUpdate(props: any) {
      items = props.items
      selectedIndex = 0
      renderItems(props)

      if (props.clientRect && component) {
        const rect = props.clientRect()
        component.style.left = `${Math.min(rect.left, window.innerWidth - 320)}px`
        component.style.top = `${rect.bottom + 6}px`
      }
    },
    onKeyDown(props: any) {
      if (!items.length) return false

      if (props.event.key === 'ArrowDown') {
        selectedIndex = (selectedIndex + 1) % items.length
        renderItems(props)
        return true
      }

      if (props.event.key === 'ArrowUp') {
        selectedIndex = (selectedIndex - 1 + items.length) % items.length
        renderItems(props)
        return true
      }

      if (props.event.key === 'Enter') {
        props.command(items[selectedIndex])
        return true
      }

      if (props.event.key === 'Escape') {
        return true
      }

      return false
    },
    onExit() {
      if (component) {
        component.remove()
      }
      component = null
      list = null
      items = []
      selectedIndex = 0
    },
  }
}

export const SlashCommands = Extension.create({
  name: 'slashCommands',

  addOptions() {
    return {
      suggestion: {
        char: '/',
        command: ({ editor, range, props }: { editor: any; range: any; props: SlashCommandItem }) => {
          props.command({ editor, range })
        },
        render: createSlashMenu,
      } as Partial<SuggestionOptions>,
    }
  },

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        ...this.options.suggestion,
        items: ({ query }: { query: string }) => {
          return slashCommands.filter((item) =>
            item.title.toLowerCase().includes(query.toLowerCase())
          )
        },
      }),
    ]
  },
})

export { slashCommands }
export default SlashCommands
