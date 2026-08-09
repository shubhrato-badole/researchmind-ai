import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Trash2, Plus, FileText, Globe, Image, FileSpreadsheet, Presentation, File, Download } from 'lucide-react'
import Layout from '../Components/Layout'
import client from '../Api/client'
import Modal from '../Components/ui/Modal'
import Button from '../Components/ui/button'
import Input from '../Components/ui/input'
import LimitReachedModal from '../Components/LimitReachedModal'

interface Document {
  id: number
  title: string
  source_type: string
  source_url: string
  created_at: string
}

const SOURCE_ICONS: Record<string, any> = {
  pdf: FileText,
  website: Globe,
  youtube: Globe,
  ocr: Image,
  csv: FileSpreadsheet,
  pptx: Presentation,
  word: FileText,
  text: FileText,
  markdown: FileText
}

const SOURCE_COLORS: Record<string, string> = {
  pdf: 'text-red-400',
  website: 'text-blue-400',
  youtube: 'text-red-500',
  ocr: 'text-amber-400',
  csv: 'text-green-400',
  pptx: 'text-orange-400',
  word: 'text-blue-300',
  text: 'text-gray-400',
  markdown: 'text-purple-400'
}


const DOWNLOADABLE_TYPES = new Set(['pdf', 'docx', 'txt', 'csv', 'png', 'jpg', 'jpeg', 'pptx', 'md', 'ocr', 'word'])

export default function Documents() {
  const queryClient = useQueryClient()
  const [urlModal, setUrlModal] = useState(false)
  const [urlType, setUrlType] = useState<'website' | 'youtube'>('website')
  const [url, setUrl] = useState('')
  const [uploading, setUploading] = useState(false)
  const [urlError, setUrlError] = useState('')
  const [downloadingId, setDownloadingId] = useState<number | null>(null)
  const [limitModalOpen, setLimitModalOpen] = useState(false)
  const [limitMessage, setLimitMessage] = useState('')

  const { data, isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await client.get('/ingest/')
      return res.data.documents as Document[]
    },
    retry: 2,
    retryDelay: 1000,
    staleTime: 30_000,
    refetchOnWindowFocus: false
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/ingest/${id}`),
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: ['documents'] })
      const previous = queryClient.getQueryData<Document[]>(['documents'])
      queryClient.setQueryData<Document[]>(['documents'], (old: Document[] | undefined) =>
        (old ?? []).filter(d => d.id !== id)
      )
      return { previous }
    },
    onError: (_err: any, _id: any, context: any) => {
      if (context?.previous) {
        queryClient.setQueryData(['documents'], context.previous)
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    }
  })

  const handleDownload = async (doc: Document) => {
    setDownloadingId(doc.id)
    try {
      const res = await client.get(`/ingest/${doc.id}/download`)
      const { download_url } = res.data
      // Open the presigned S3 URL directly — the browser fetches the file
      // straight from S3, not through our backend.
      window.open(download_url, '_blank')
    } catch (err: any) {
      alert(err.response?.data?.detail || 'File not available for download')
    } finally {
      setDownloadingId(null)
    }
  }

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      await client.post('/ingest/file', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      })
      queryClient.invalidateQueries({ queryKey: ['documents'] })
    } catch (err: any) {
      if (err.response?.status === 429 || err.response?.status === 403) {
        setLimitMessage(err.response?.data?.detail || 'Limit reached')
        setLimitModalOpen(true)
      } else {
        alert(err.response?.data?.detail || 'Upload failed')
      }
    } finally {
      setUploading(false)
      e.target.value = ''
    }
  }

  const handleUrlIngest = async () => {
    if (!url.trim()) return
    setUrlError('')
    setUploading(true)
    try {
      if (urlType === 'website') {
        await client.post('/ingest/website', { url })
      } else {
        await client.post('/ingest/youtube', { url })
      }
      queryClient.invalidateQueries({ queryKey: ['documents'] })
      setUrlModal(false)
      setUrl('')
    } catch (err: any) {
      setUrlError(err.response?.data?.detail || 'Failed to ingest URL')
    } finally {
      setUploading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    })
  }

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">

        <div className="px-5 py-3 border-b border-[#3a3a3c] flex items-center justify-between bg-[#2d2d2f] flex-shrink-0">
          <div>
            <h1 className="text-sm font-semibold text-white">My documents</h1>
            <p className="text-xs text-[#666]">{data?.length ?? 0} documents in your knowledge base</p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => { setUrlType('youtube'); setUrlModal(true) }}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 border border-[#3a3a3c] text-[#999] rounded-lg hover:text-white hover:border-[#555] transition-colors"
            >
              <Globe size={13} /> YouTube
            </button>
            <button
              onClick={() => { setUrlType('website'); setUrlModal(true) }}
              className="flex items-center gap-1.5 text-xs px-3 py-1.5 border border-[#3a3a3c] text-[#999] rounded-lg hover:text-white hover:border-[#555] transition-colors"
            >
              <Globe size={13} /> Website
            </button>
            <label className="cursor-pointer">
              <div className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors">
                {uploading ? <Spinner size="sm" /> : <><Plus size={13} /> Upload file</>}
              </div>
              <input
                type="file"
                className="hidden"
                accept=".pdf,.docx,.txt,.csv,.png,.jpg,.jpeg,.pptx,.md"
                onChange={handleFileUpload}
              />
            </label>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 bg-[#2d2d2f]">
          {isLoading ? (
            <div className="flex justify-center py-20">
              <Spinner />
            </div>
          ) : isError ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
              <div className="w-14 h-14 bg-[#3a1c1c] rounded-2xl flex items-center justify-center text-3xl">⚠️</div>
              <h2 className="text-sm font-semibold text-white">0 documents uploaded</h2>
              <p className="text-xs text-[#666] max-w-xs">
                {(error as any)?.response?.data?.detail || 'Something went wrong. Check your connection and try again.'}
              </p>
              <button
                onClick={() => refetch()}
                className="text-xs px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors"
              >
                {isFetching ? 'Retrying...' : 'Try again'}
              </button>
            </div>
          ) : data?.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
              <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center text-3xl">📭</div>
              <h2 className="text-sm font-semibold text-white">No documents yet</h2>
              <p className="text-xs text-[#666] max-w-xs">Upload a PDF, add a website URL, or paste a YouTube link to get started</p>
            </div>
          ) : (
            <div className="flex flex-col gap-2">
              {data?.map(doc => {
                const IconComponent = SOURCE_ICONS[doc.source_type] ?? File
                const iconColor = SOURCE_COLORS[doc.source_type] ?? 'text-gray-400'
                const canDownload = DOWNLOADABLE_TYPES.has(doc.source_type)
                return (
                  <div
                    key={doc.id}
                    className="group flex items-center gap-3 bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl px-4 py-3 hover:border-[#3a3a3c] transition-colors"
                  >
                    <div className="w-9 h-9 bg-[#2d2d2f] rounded-lg flex items-center justify-center flex-shrink-0">
                      <IconComponent size={18} className={iconColor} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-white truncate">{doc.title}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-xs text-[#555] capitalize">{doc.source_type}</span>
                        <span className="text-xs text-[#444]">·</span>
                        <span className="text-xs text-[#555]">{formatDate(doc.created_at)}</span>
                        {doc.source_url && (
                          <>
                            <span className="text-xs text-[#444]">·</span>
                            <a
                              href={doc.source_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-xs text-[#7C75D4] hover:underline truncate max-w-xs"
                            >
                              {doc.source_url}
                            </a>
                          </>
                        )}
                      </div>
                    </div>
                    {canDownload && (
                      <button
                        onClick={() => handleDownload(doc)}
                        disabled={downloadingId === doc.id}
                        className="opacity-0 group-hover:opacity-100 text-[#555] hover:text-[#7C75D4] transition-all disabled:opacity-50"
                        title="Download original file"
                      >
                        {downloadingId === doc.id ? <Spinner size="sm" /> : <Download size={15} />}
                      </button>
                    )}
                    <button
                      onClick={() => deleteMutation.mutate(doc.id)}
                      className="opacity-0 group-hover:opacity-100 text-[#555] hover:text-red-400 transition-all"
                      title="Delete document"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>

      <Modal
        open={urlModal}
        onClose={() => { setUrlModal(false); setUrl(''); setUrlError('') }}
        title={urlType === 'website' ? 'Add website' : 'Add YouTube video'}
      >
        <div className="flex flex-col items-center gap-3">
          <Input
            value={url}
            onChange={e => setUrl(e.target.value)}
            placeholder={urlType === 'website' ? 'https://example.com' : 'https://youtube.com/watch?v=...'}
            error={urlError}
            className="text-center w-full"
          />
          <Button
            onClick={handleUrlIngest}
            disabled={uploading || !url.trim()}
            className="w-full"
          >
            {uploading ? 'Adding...' : 'Add to knowledge base'}
          </Button>
        </div>
      </Modal>
      <LimitReachedModal
        open={limitModalOpen}
        onClose={() => setLimitModalOpen(false)}
        message={limitMessage}
      />
    </Layout>
  )
}