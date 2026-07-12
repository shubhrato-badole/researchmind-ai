import { useRef } from 'react'
import { Plus, X, FileText, Image } from 'lucide-react'

interface PendingFile {
  file: File
  preview: string
  type: string
}

export default function AddContentMenu({
  pendingFile,
  onFileSelected,
  onRemove
}: {
  pendingFile: PendingFile | null
  onFileSelected: (file: PendingFile) => void
  onRemove: () => void
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const type = file.type.startsWith('image') ? 'image' : 'document'
    const preview = file.name

    onFileSelected({ file, preview, type })
    e.target.value = ''
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.pptx,.md"
        className="hidden"
        onChange={handleFileChange}
      />

      {pendingFile ? (
     
        <div className="flex items-center gap-1.5 bg-[#1e1b4b] border border-[#534AB7] text-[#7C75D4] rounded-lg px-2.5 py-1.5 text-xs flex-shrink-0">
          {pendingFile.type === 'image'
            ? <Image size={12} />
            : <FileText size={12} />
          }
          <span className="max-w-[100px] truncate">{pendingFile.preview}</span>
          <button onClick={onRemove} className="hover:text-white transition-colors">
            <X size={12} />
          </button>
        </div>
      ) : (
        <button
          onClick={() => fileInputRef.current?.click()}
          className="w-8 h-8 rounded-full border border-[#3a3a3c] flex items-center justify-center text-[#666] hover:text-white transition-colors flex-shrink-0"
          aria-label="Add file"
        >
          <Plus size={16} />
        </button>
      )}
    </>
  )
}