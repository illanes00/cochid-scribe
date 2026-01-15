'use client'

import { useEditor, EditorContent, BubbleMenu, Editor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Placeholder from '@tiptap/extension-placeholder'
import Highlight from '@tiptap/extension-highlight'
import TiptapLink from '@tiptap/extension-link'
import Underline from '@tiptap/extension-underline'
import CharacterCount from '@tiptap/extension-character-count'
import { useCallback, useEffect } from 'react'
import {
  Bold,
  Italic,
  Underline as UnderlineIcon,
  Strikethrough,
  Code,
  List,
  ListOrdered,
  Quote,
  Heading1,
  Heading2,
  Heading3,
  Undo,
  Redo,
  Link as LinkIcon,
  Highlighter,
  Tag,
  BookOpen,
} from 'lucide-react'
import { Claim } from './extensions/claim'
import { Citation } from './extensions/citation'

interface TiptapEditorProps {
  content?: string
  onChange?: (content: string) => void
  onReady?: (editor: Editor) => void
  placeholder?: string
}

export function TiptapEditor({
  content = '',
  onChange,
  onReady,
  placeholder = 'Start writing...',
}: TiptapEditorProps) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({
        heading: {
          levels: [1, 2, 3],
        },
      }),
      Placeholder.configure({
        placeholder,
      }),
      Highlight.configure({
        multicolor: true,
      }),
      TiptapLink.configure({
        openOnClick: false,
      }),
      Underline,
      CharacterCount,
      Claim,
      Citation,
    ],
    content,
    onUpdate: ({ editor }) => {
      onChange?.(editor.getHTML())
    },
    editorProps: {
      attributes: {
        class: 'tiptap-editor',
      },
    },
  })

  // Notify parent when editor is ready
  useEffect(() => {
    if (editor && onReady) {
      onReady(editor)
    }
  }, [editor, onReady])

  // Update content when it changes from outside (only if different)
  useEffect(() => {
    if (editor && content && editor.getHTML() !== content) {
      editor.commands.setContent(content)
    }
  }, [content, editor])

  const setLink = useCallback(() => {
    if (!editor) return
    const previousUrl = editor.getAttributes('link').href
    const url = window.prompt('URL', previousUrl)

    if (url === null) return
    if (url === '') {
      editor.chain().focus().extendMarkRange('link').unsetLink().run()
      return
    }

    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }, [editor])

  const markAsClaim = useCallback(() => {
    if (!editor) return
    const { from, to } = editor.state.selection
    if (from === to) return

    const claimId = `C-${Date.now().toString(36)}`
    editor.chain().focus().setClaim({ claimId }).run()
  }, [editor])

  const insertCitation = useCallback(() => {
    if (!editor) return
    const bibKey = window.prompt('Enter citation key (e.g., Bathelt_2004)')
    if (!bibKey) return

    editor.chain().focus().insertCitation({ bibKey }).run()
  }, [editor])

  if (!editor) {
    return null
  }

  return (
    <div className="flex flex-col h-full">
      {/* Toolbar */}
      <div className="flex items-center gap-1 p-3 border-b border-line bg-paper flex-wrap">
        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().undo().run()}
            disabled={!editor.can().undo()}
            title="Undo"
          >
            <Undo size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().redo().run()}
            disabled={!editor.can().redo()}
            title="Redo"
          >
            <Redo size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            active={editor.isActive('bold')}
            title="Bold"
          >
            <Bold size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            active={editor.isActive('italic')}
            title="Italic"
          >
            <Italic size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleUnderline().run()}
            active={editor.isActive('underline')}
            title="Underline"
          >
            <UnderlineIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleStrike().run()}
            active={editor.isActive('strike')}
            title="Strikethrough"
          >
            <Strikethrough size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleCode().run()}
            active={editor.isActive('code')}
            title="Code"
          >
            <Code size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            active={editor.isActive('highlight')}
            title="Highlight"
          >
            <Highlighter size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 1 }).run()
            }
            active={editor.isActive('heading', { level: 1 })}
            title="Heading 1"
          >
            <Heading1 size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 2 }).run()
            }
            active={editor.isActive('heading', { level: 2 })}
            title="Heading 2"
          >
            <Heading2 size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() =>
              editor.chain().focus().toggleHeading({ level: 3 }).run()
            }
            active={editor.isActive('heading', { level: 3 })}
            title="Heading 3"
          >
            <Heading3 size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBulletList().run()}
            active={editor.isActive('bulletList')}
            title="Bullet List"
          >
            <List size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleOrderedList().run()}
            active={editor.isActive('orderedList')}
            title="Ordered List"
          >
            <ListOrdered size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBlockquote().run()}
            active={editor.isActive('blockquote')}
            title="Quote"
          >
            <Quote size={16} />
          </ToolbarButton>
        </ToolbarGroup>

        <Divider />

        <ToolbarGroup>
          <ToolbarButton
            onClick={setLink}
            active={editor.isActive('link')}
            title="Link"
          >
            <LinkIcon size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={markAsClaim}
            active={editor.isActive('claim')}
            title="Mark as Claim"
          >
            <Tag size={16} />
          </ToolbarButton>
          <ToolbarButton
            onClick={insertCitation}
            title="Insert Citation"
          >
            <BookOpen size={16} />
          </ToolbarButton>
        </ToolbarGroup>
      </div>

      {/* Editor */}
      <div className="flex-1 overflow-auto">
        <EditorContent editor={editor} className="h-full" />
      </div>

      {/* Bubble Menu */}
      {editor && (
        <BubbleMenu
          editor={editor}
          tippyOptions={{ duration: 100 }}
          className="flex items-center gap-1 p-1 bg-paper border border-line"
        >
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleBold().run()}
            active={editor.isActive('bold')}
            size="sm"
          >
            <Bold size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleItalic().run()}
            active={editor.isActive('italic')}
            size="sm"
          >
            <Italic size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={setLink}
            active={editor.isActive('link')}
            size="sm"
          >
            <LinkIcon size={14} />
          </ToolbarButton>
          <ToolbarButton
            onClick={() => editor.chain().focus().toggleHighlight().run()}
            active={editor.isActive('highlight')}
            size="sm"
          >
            <Highlighter size={14} />
          </ToolbarButton>
          <Divider />
          <ToolbarButton
            onClick={markAsClaim}
            active={editor.isActive('claim')}
            size="sm"
            title="Mark as Claim"
          >
            <Tag size={14} />
          </ToolbarButton>
        </BubbleMenu>
      )}
    </div>
  )
}

function ToolbarGroup({ children }: { children: React.ReactNode }) {
  return <div className="flex items-center gap-0.5">{children}</div>
}

function ToolbarButton({
  children,
  onClick,
  active,
  disabled,
  title,
  size = 'md',
}: {
  children: React.ReactNode
  onClick?: () => void
  active?: boolean
  disabled?: boolean
  title?: string
  size?: 'sm' | 'md'
}) {
  const sizeClasses = size === 'sm' ? 'p-1' : 'p-2'

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      title={title}
      className={`
        ${sizeClasses}
        border border-transparent
        ${active ? 'bg-bg border-line text-c-blue' : 'text-ink hover:bg-bg'}
        ${disabled ? 'opacity-40 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      {children}
    </button>
  )
}

function Divider() {
  return <div className="w-px h-6 bg-line mx-1" />
}
