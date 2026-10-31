import { useRef } from 'react'
import { Plus, Paperclip } from 'lucide-react'

export interface PendingFile {
  file: File
  preview: string
  type: string
}

export default function AddContentMenu({
  onFilesSelected,
  disabled = false,
  selectedCount = 0,
}: {
  onFilesSelected: (files: PendingFile[]) => void
  disabled?: boolean
  selectedCount?: number
}) {
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const fileList = Array.from(event.currentTarget.files ?? []) as File[]
    if (!fileList.length) return

    const selected = fileList.map((file) => ({
      file,
      preview: file.name,
      type: file.type.startsWith('image/') ? 'image' : 'document',
    }))
    onFilesSelected(selected)
    event.target.value = ''
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.pptx,.md"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        disabled={disabled}
        title={selectedCount ? `Add files (${selectedCount} selected)` : 'Attach files'}
        aria-label="Attach files"
        className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-full border border-[#3a3a3c] text-[#999] transition-colors hover:border-[#534AB7] hover:text-white disabled:cursor-not-allowed disabled:opacity-40"
      >
        {selectedCount > 0 ? <Paperclip size={17} /> : <Plus size={17} />}
        {selectedCount > 0 && (
          <span className="absolute -right-1 -top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-[#7C75D4] px-1 text-[9px] font-semibold text-white">
            {selectedCount}
          </span>
        )}
      </button>
    </>
  )
}
