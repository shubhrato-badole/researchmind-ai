import { useState, useRef, useEffect } from 'react'
import { FileText, Plus, X } from 'lucide-react'
import type { DocumentItem } from '../hooks/useDocuments'

const MAX_DOCS = 2

export default function DocumentPicker({
  documents,
  selectedIds,
  onChange
}: {
  documents: DocumentItem[]
  selectedIds: number[]
  onChange: (ids: number[]) => void
}) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const selectedDocs = documents.filter(d => selectedIds.includes(d.id))
  const atLimit = selectedIds.length >= MAX_DOCS

  const toggleDoc = (id: number) => {
    if (selectedIds.includes(id)) {
      onChange(selectedIds.filter(i => i !== id))
    } else if (!atLimit) {
      onChange([...selectedIds, id])
    }
  }

  const removeDoc = (id: number) => onChange(selectedIds.filter(i => i !== id))

  return (
    <div className="flex items-center gap-2 flex-wrap relative" ref={ref}>
      <div className="flex items-center gap-1.5 bg-[#1c1c1e] border border-[#3a3a3c] rounded-lg px-2.5 py-1.5">
        <FileText size={13} className="text-[#7C75D4]" />
        <span className="text-xs text-[#999]">Documents</span>
        <span className="text-[10px] bg-[#333] text-[#aaa] px-1.5 py-0.5 rounded-full">
          {selectedIds.length}/{MAX_DOCS}
        </span>
      </div>

      {selectedDocs.map(doc => (
        <div
          key={doc.id}
          className="flex items-center gap-1.5 bg-[#1e1b4b] border border-[#534AB7] text-[#7C75D4] rounded-full px-2.5 py-1 text-xs"
        >
          <span className="truncate max-w-[140px]">{doc.title}</span>
          <X size={12} className="cursor-pointer flex-shrink-0" onClick={() => removeDoc(doc.id)} />
        </div>
      ))}

      <button
        onClick={() => setOpen(prev => !prev)}
        disabled={atLimit}
        className="flex items-center gap-1 text-xs px-2.5 py-1 border border-[#3a3a3c] rounded-full text-[#888] hover:text-white hover:border-[#534AB7] transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
      >
        <Plus size={12} /> Add document
      </button>

      {open && (
        <div className="absolute top-9 left-0 bg-[#1c1c1e] border border-[#3a3a3c] rounded-lg p-1 w-56 z-10 max-h-56 overflow-y-auto">
          {documents.length === 0 ? (
            <p className="text-xs text-[#555] text-center py-3">No documents uploaded yet</p>
          ) : (
            documents.map(doc => {
              const isSelected = selectedIds.includes(doc.id)
              const disabled = !isSelected && atLimit
              return (
                <button
                  key={doc.id}
                  onClick={() => !disabled && toggleDoc(doc.id)}
                  disabled={disabled}
                  className={`w-full flex items-center gap-2 px-2 py-1.5 rounded-md text-xs text-left transition-colors ${
                    isSelected ? 'bg-[#1e1b4b] text-[#7C75D4]' : disabled ? 'text-[#444] cursor-not-allowed' : 'text-[#ccc] hover:bg-[#2d2d2f]'
                  }`}
                >
                  <span className={`w-3.5 h-3.5 rounded border flex-shrink-0 flex items-center justify-center ${
                    isSelected ? 'bg-[#534AB7] border-[#534AB7]' : 'border-[#555]'
                  }`}>
                    {isSelected && <span className="w-1.5 h-1.5 bg-white rounded-sm" />}
                  </span>
                  <span className="truncate">{doc.title}</span>
                </button>
              )
            })
          )}
        </div>
      )}
    </div>
  )
}