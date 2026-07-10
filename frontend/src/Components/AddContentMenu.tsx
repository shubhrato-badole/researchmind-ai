import { useRef, useState } from 'react'
import { Plus } from 'lucide-react'
import client from '../Api/client'

export default function AddContentMenu({ onAdded }: { onAdded?: () => void }) {
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [uploading, setUploading] = useState(false)

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      await client.post('/ingest/file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      onAdded?.()
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  return (
    <div className="relative">
      <input
        ref={fileInputRef}
        type="file"
       accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.pptx,.md"
        className="hidden"
        onChange={handleFileChange}
      />
      <button
        onClick={() => fileInputRef.current?.click()}
        disabled={uploading}
        className="w-8 h-8 rounded-full border border-[#3a3a3c] flex items-center justify-center text-[#888] hover:text-white transition-colors flex-shrink-0 disabled:opacity-40"
        aria-label="Add content"
        title="Upload a PDF or image"
      >
        <Plus size={16} />
      </button>
    </div>
  )
}