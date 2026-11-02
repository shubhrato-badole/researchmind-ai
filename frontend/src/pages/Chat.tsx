import { useState, useRef, useEffect, useCallback } from 'react'

import { useSearchParams } from 'react-router-dom'

import { useQuery, useQueryClient } from '@tanstack/react-query'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

import { Send, Mic, MicOff, Brain, StopCircle, X, FileText, Image as ImageIcon } from 'lucide-react'



import Layout from '../Components/Layout'

import client from '../Api/client'

import { useSessions } from '../hooks/useSessions'

import { useDocuments } from '../hooks/useDocuments'

import { useVoiceInput } from '../hooks/useVoiceInput'

import { useAuth } from '../context/AuthContext'

import SearchModeDropdown, {

  type SearchMode,

} from '../Components/SearchModeDropdown'

import AddContentMenu, { type PendingFile } from '../Components/AddContentMenu'




function MarkdownContent({ content }: { content: string }) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ children }) => (
          <h1 className="mt-4 mb-2 text-lg font-semibold text-white first:mt-0">{children}</h1>
        ),
        h2: ({ children }) => (
          <h2 className="mt-4 mb-2 text-base font-semibold text-white first:mt-0">{children}</h2>
        ),
        h3: ({ children }) => (
          <h3 className="mt-3 mb-1.5 text-sm font-semibold text-white">{children}</h3>
        ),
        p: ({ children }) => (
          <p className="my-2 whitespace-pre-wrap leading-7 first:mt-0 last:mb-0">{children}</p>
        ),
        ul: ({ children }) => (
          <ul className="my-2 list-disc space-y-1 pl-5">{children}</ul>
        ),
        ol: ({ children }) => (
          <ol className="my-2 list-decimal space-y-1 pl-5">{children}</ol>
        ),
        li: ({ children }) => <li className="pl-1">{children}</li>,
        strong: ({ children }) => <strong className="font-semibold text-white">{children}</strong>,
        em: ({ children }) => <em className="italic">{children}</em>,
        blockquote: ({ children }) => (
          <blockquote className="my-3 border-l-2 border-[#7C75D4] pl-4 text-[#c9c5f4]">
            {children}
          </blockquote>
        ),
        a: ({ href, children }) => (
          <a
            href={href}
            target="_blank"
            rel="noopener noreferrer"
            className="break-words text-[#AFA9EC] underline underline-offset-2 hover:text-white"
          >
            {children}
          </a>
        ),
        hr: () => <hr className="my-4 border-[#3a3a3c]" />,
        pre: ({ children }) => (
          <pre className="my-3 max-w-full overflow-x-auto rounded-lg border border-[#3a3a3c] bg-[#111113] p-3 text-xs leading-6">
            {children}
          </pre>
        ),
        code: ({ className, children }) => (
          <code
            className={
              className
                ? `${className} font-mono text-xs text-[#e5e7eb]`
                : 'rounded bg-black/30 px-1.5 py-0.5 font-mono text-[0.9em] text-[#e5e7eb]'
            }
          >
            {children}
          </code>
        ),
        table: ({ children }) => (
          <div className="my-3 w-full overflow-x-auto rounded-lg border border-[#3a3a3c]">
            <table className="w-full border-collapse text-left text-sm">{children}</table>
          </div>
        ),
        thead: ({ children }) => <thead className="bg-[#252528]">{children}</thead>,
        th: ({ children }) => (
          <th className="border-b border-[#3a3a3c] px-3 py-2 font-semibold text-white">{children}</th>
        ),
        td: ({ children }) => (
          <td className="border-b border-[#3a3a3c] px-3 py-2 align-top text-[#ddd]">{children}</td>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
  )
}

interface Message {

  role: 'user' | 'assistant'

  content: string

  awaiting_approval?: boolean

  thread_id?: string

}




export default function Chat() {

  const { user } = useAuth()

  const [searchParams, setSearchParams] = useSearchParams()



  const currentSessionId = searchParams.get('session')

    ? Number(searchParams.get('session'))

    : null



  const { addSessionOptimistic } = useSessions()
  const { documents } = useDocuments()
  const queryClient = useQueryClient()



  const [messages, setMessages] = useState<Message[]>([])

  const [input, setInput] = useState('')

  const [loading, setLoading] = useState(false)

  const [searchMode, setSearchMode] =

    useState<SearchMode>('docs_web')

  const [pendingFiles, setPendingFiles] = useState<PendingFile[]>([])



  const bottomRef = useRef<HTMLDivElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const generationAbortRef = useRef<AbortController | null>(null)
  const voiceBaseTextRef = useRef('')

  const handleVoiceResult = useCallback((transcript: string) => {
    const prefix = voiceBaseTextRef.current
    const separator = prefix && !/\s$/.test(prefix) ? ' ' : ''
    setInput(`${prefix}${separator}${transcript}`)
  }, [])

  const {
    listening,
    supported: micSupported,
    start: startListening,
    stop: stopListening,
  } = useVoiceInput(handleVoiceResult)

  const startVoiceInput = () => {
    voiceBaseTextRef.current = input.trimEnd()
    if (voiceBaseTextRef.current) voiceBaseTextRef.current += ' '
    startListening()
  }

  const stopGeneration = () => {
    generationAbortRef.current?.abort()
  }

  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    const maxHeight = 144
    textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 44), maxHeight)}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [input])



  // Load chat history.

  const { data: historyData } = useQuery({

    queryKey: ['chat-history', currentSessionId],

    queryFn: async () => {

      const res = await client.get(

        `/chat/history?session_id=${currentSessionId}`,

      )



      return res.data.history.map((msg: any) => ({

        role: msg.role,

        content: msg.message,

      })) as Message[]

    },

    enabled: !!currentSessionId,

    placeholderData: (previousData) => previousData,

  })



  useEffect(() => {

    if (currentSessionId && historyData) {

      setMessages(historyData)

    } else if (!currentSessionId) {

      setMessages([])

    }

  }, [currentSessionId, historyData])



  useEffect(() => {

    bottomRef.current?.scrollIntoView({

      behavior: 'smooth',

    })

  }, [messages])



  // Upload selected files and submit the prompt as one chat action.
  const sendMessage = async () => {
    if (loading) return

    const filesToUpload = [...pendingFiles]
    const query = input.trim()
    if (!query && filesToUpload.length === 0) return

    if (
      searchMode === 'docs' &&
      documents.length === 0 &&
      filesToUpload.length === 0 &&
      query
    ) {
      setMessages((prev) => [
        ...prev,
        { role: 'user', content: query },
        {
          role: 'assistant',
          content: "You haven't uploaded any documents yet. Add a document to use My docs only, or switch to Docs + web or Web only mode.",
        },
      ])
      setInput('')
      return
    }

    const controller = new AbortController()
    generationAbortRef.current = controller
    setInput('')
    setPendingFiles([])
    setLoading(true)

    const attachmentSummary = filesToUpload.length
      ? `📎 ${filesToUpload.length} file${filesToUpload.length === 1 ? '' : 's'} selected:\n${filesToUpload.map((item) => `• ${item.preview}`).join('\n')}`
      : ''
    setMessages((prev) => [
      ...prev,
      {
        role: 'user',
        content: [attachmentSummary, query].filter(Boolean).join('\n\n'),
      },
    ])

    let failedFile: PendingFile | null = null

    try {
      for (const item of filesToUpload) {
        failedFile = item
        const formData = new FormData()
        formData.append('file', item.file)
        await client.post('/ingest/file', formData, { signal: controller.signal })
      }
      failedFile = null
      if (filesToUpload.length > 0) {
        await queryClient.invalidateQueries({ queryKey: ['documents'] })
      }

      if (query) {
        if (searchMode === 'web') {
          const response = await fetch(`${import.meta.env.VITE_API_URL}/chat/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            signal: controller.signal,
            body: JSON.stringify({
              query,
              search_mode: searchMode,
              session_id: currentSessionId,
              stream: true,
            }),
          })

          if (!response.ok) {
            throw new Error(`Chat request failed with HTTP ${response.status}`)
          }
          if (!response.body) throw new Error('No response stream received')

          setMessages((prev) => [...prev, { role: 'assistant', content: '' }])
          const reader = response.body.getReader()
          const decoder = new TextDecoder()
          let fullText = ''

          while (true) {
            const { done, value } = await reader.read()
            if (done) break
            fullText += decoder.decode(value, { stream: true })
            setMessages((prev) => {
              const updated = [...prev]
              const lastIndex = updated.length - 1
              if (lastIndex >= 0 && updated[lastIndex].role === 'assistant') {
                updated[lastIndex] = { ...updated[lastIndex], content: fullText }
              }
              return updated
            })
          }

          fullText += decoder.decode()
          if (!fullText.trim()) {
            throw new Error('The assistant returned an empty response. Please try again.')
          }
          setMessages((prev) => {
            const updated = [...prev]
            const lastIndex = updated.length - 1
            if (lastIndex >= 0 && updated[lastIndex].role === 'assistant') {
              updated[lastIndex] = { ...updated[lastIndex], content: fullText }
            }
            return updated
          })

          if (!currentSessionId) {
            addSessionOptimistic({
              id: Date.now(),
              title: query.slice(0, 40),
              created_at: new Date().toISOString(),
            })
          }
        } else {
          const res = await client.post('/chat/', {
            query,
            search_mode: searchMode,
            session_id: currentSessionId,
          }, { signal: controller.signal })
          const data = res.data

          if (!currentSessionId && data.session_id) {
            setSearchParams({ session: String(data.session_id) })
            addSessionOptimistic({
              id: data.session_id,
              title: query.slice(0, 40),
              created_at: new Date().toISOString(),
            })
          }

          if (data.status === 'awaiting_approval') {
            setMessages((prev) => [...prev, {
              role: 'assistant',
              content: data.message,
              awaiting_approval: true,
              thread_id: data.thread_id,
            }])
          } else if (typeof data.answer === 'string' && data.answer.trim()) {
            setMessages((prev) => [...prev, { role: 'assistant', content: data.answer }])
          } else if (data.error) {
            throw new Error(String(data.error))
          } else {
            throw new Error('The assistant returned an empty response. Please try again.')
          }
        }
      } else if (filesToUpload.length > 0) {
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: `✅ Successfully uploaded ${filesToUpload.length} file${filesToUpload.length === 1 ? '' : 's'}. Ask me a question about your content.`,
        }])
      }
    } catch (error: unknown) {
      const err = error as {
        name?: string
        code?: string
        message?: string
        response?: { status?: number; data?: { detail?: string; error?: string } }
      }
      const wasCancelled = controller.signal.aborted || err.name === 'AbortError' || err.code === 'ERR_CANCELED'

      if (wasCancelled) {
        setMessages((prev) => {
          const updated = [...prev]
          const lastIndex = updated.length - 1
          const last = updated[lastIndex]
          if (last?.role === 'assistant' && !last.content.trim()) updated.pop()
          const newLast = updated[updated.length - 1]
          if (newLast?.role === 'assistant' && newLast.content.trim() && searchMode === 'web') {
            updated[updated.length - 1] = {
              ...newLast,
              content: `${newLast.content}\n\n_Generation stopped._`,
            }
            return updated
          }
          return [...updated, {
            role: 'assistant',
            content: failedFile
              ? `Upload stopped while processing "${failedFile.preview}". Files uploaded before stopping may already be available in My documents.`
              : 'Generation stopped.',
          }]
        })
        return
      }

      console.error('Message or document upload failed:', error)
      const status = err.response?.status
      const detail = err.response?.data?.detail || err.response?.data?.error
      const errorMessage = failedFile
        ? `❌ Failed to upload "${failedFile.preview}". ${detail || (status ? `The server returned HTTP ${status}.` : 'Check your connection and backend logs.')} You can select the file again to retry.`
        : detail || err.message || 'Something went wrong while processing your message. Please try again.'

      setMessages((prev) => {
        const updated = [...prev]
        const lastIndex = updated.length - 1
        const last = updated[lastIndex]
        if (last?.role === 'assistant' && !last.content.trim()) {
          updated[lastIndex] = { role: 'assistant', content: errorMessage }
          return updated
        }
        return [...updated, { role: 'assistant', content: errorMessage }]
      })
    } finally {
      if (generationAbortRef.current === controller) generationAbortRef.current = null
      setLoading(false)
    }
  }

  const handleApproval = async (

    threadId: string,

    approved: boolean,

  ) => {
    if (loading) return
    const controller = new AbortController()
    generationAbortRef.current = controller
    setLoading(true)

    try {
      const res = await client.post('/chat/resume', {
        thread_id: threadId,
        approved,
        session_id: currentSessionId,
      }, { signal: controller.signal })



      if (

        res.data.answer &&

        res.data.answer.trim()

      ) {

        setMessages((prev) => [

          ...prev.filter((message) => !message.awaiting_approval),

          {

            role: 'assistant',

            content: res.data.answer,

          },

        ])

      } else {

        setMessages((prev) =>

          prev.filter((message) => !message.awaiting_approval),

        )

      }

    } catch (error) {
      const err = error as { name?: string; code?: string }
      const wasCancelled = controller.signal.aborted || err.name === 'AbortError' || err.code === 'ERR_CANCELED'
      if (!wasCancelled) {
        console.error('Approval request failed:', error)
        setMessages((prev) => [...prev, {
          role: 'assistant',
          content: 'Failed to process your choice. Please try again.',
        }])
      }
    } finally {
      if (generationAbortRef.current) generationAbortRef.current = null
      setLoading(false)
    }
  }

  const userInitial =

    user?.name?.[0]?.toUpperCase() || 'U'



  return (

    <Layout>

      <div className="flex-1 min-w-0 min-h-0 flex flex-col overflow-hidden">

        {/* Chat header */}

        <div className="px-3 sm:px-5 py-3 pl-14 md:pl-5 border-b border-[#3a3a3c] flex items-center justify-between gap-2 bg-[#2d2d2f] flex-shrink-0">

          <h1 className="text-sm font-semibold text-white">

            {currentSessionId ? 'Chat' : 'New chat'}

          </h1>



          <SearchModeDropdown

            value={searchMode}

            onChange={setSearchMode}

          />

        </div>



        {/* Chat messages */}

        <div className="flex-1 min-h-0 min-w-0 overflow-y-auto px-3 py-3 sm:px-5 sm:py-4 flex flex-col gap-4 bg-[#2d2d2f]">

          {messages.length === 0 && (

            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center py-16">

              <div className="w-14 h-14 bg-[#534AB7] rounded-2xl flex items-center justify-center">

                <Brain size={26} color="white" />

              </div>



              <h2 className="text-base font-semibold text-white mt-1">

                Welcome to ResearchMind

              </h2>



              <p className="text-sm font-medium text-[#AFA9EC] m-0">

                Ask anything

              </p>



              <p className="text-sm text-[#999] max-w-xs m-0">

                Get answers from your documents, or anywhere

                on the web.

              </p>



              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 mt-3 w-full max-w-md">

                {[

                  {

                    n: 1,

                    title: 'Add content',

                    desc: 'PDF, website, YouTube, or image',

                  },

                  {

                    n: 2,

                    title: 'Ask anything',

                    desc: 'Docs, the web, or general questions',

                  },

                  {

                    n: 3,

                    title: 'Get answers',

                    desc: 'With sources shown',

                  },

                ].map((step) => (

                  <div

                    key={step.n}

                    className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-xl p-3"

                  >

                    <div className="w-5 h-5 bg-[#1e1b4b] text-[#7C75D4] rounded-full flex items-center justify-center text-[11px] font-medium mx-auto mb-2">

                      {step.n}

                    </div>



                    <p className="text-xs font-medium text-white mb-1">

                      {step.title}

                    </p>



                    <p className="text-[11px] text-[#777] leading-tight">

                      {step.desc}

                    </p>

                  </div>

                ))}

              </div>



              <div className="flex gap-2 mt-3 flex-wrap justify-center">

                {[

                  'Summarise my documents',

                  "What's trending in RAG research?",

                  'Explain reranking',

                ].map((suggestion) => (

                  <button

                    key={suggestion}

                    onClick={() => setInput(suggestion)}

                    className="text-xs px-3 py-1.5 bg-[#1c1c1e] border border-[#3a3a3c] rounded-full text-[#999] hover:text-white hover:border-[#534AB7] transition-colors"

                  >

                    {suggestion}

                  </button>

                ))}

              </div>

            </div>

          )}



          {messages.map((msg, index) => {
            // Streaming creates an empty assistant placeholder. Keep it out of the UI;
            // the separate Thinking indicator is shown until content arrives.
            if (msg.role === 'assistant' && !msg.content.trim()) return null

            return (
            <div

              key={index}

              className={`flex flex-col min-w-0 ${

                msg.role === 'user'

                  ? 'items-end'

                  : 'items-start'

              }`}

            >

              <div

                className={`flex items-start gap-2 max-w-[92%] sm:max-w-[75%] min-w-0 ${

                  msg.role === 'user' ? 'flex-row-reverse' : ''

                }`}

              >

                {msg.role === 'assistant' ? (

                  <div className="w-7 h-7 rounded-lg bg-[#534AB7] flex items-center justify-center flex-shrink-0 mt-0.5">

                    <Brain size={14} color="white" />

                  </div>

                ) : (

                  <div className="w-7 h-7 rounded-full bg-[#1e1b4b] text-[#7C75D4] flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">

                    {userInitial}

                  </div>

                )}



                <div

                  className={`px-4 py-3 rounded-2xl text-sm leading-relaxed break-words whitespace-pre-wrap min-w-0 ${

                    msg.role === 'user'

                      ? 'bg-[#534AB7] text-white rounded-br-sm'

                      : 'bg-[#1c1c1e] text-white border border-[#3a3a3c] rounded-bl-sm'

                  }`}

                >

                  {msg.role === 'assistant' ? (
                    <MarkdownContent content={msg.content} />
                  ) : (
                    msg.content
                  )}

                </div>

              </div>



              {msg.awaiting_approval && msg.thread_id && (

                <div className="flex gap-2 mt-2 ml-9">

                  <button

                    onClick={() =>

                      handleApproval(msg.thread_id!, true)

                    }

                    disabled={loading}

                    className="text-xs px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors disabled:opacity-40"

                  >

                    Yes, search web

                  </button>



                  <button

                    onClick={() =>

                      handleApproval(msg.thread_id!, false)

                    }

                    disabled={loading}

                    className="text-xs px-4 py-2 bg-[#1c1c1e] text-[#999] border border-[#3a3a3c] rounded-lg hover:text-white transition-colors disabled:opacity-40"

                  >

                    Docs only

                  </button>

                </div>

              )}

            </div>
            )
          })}



          {loading && (

            <div className="flex items-start gap-2">

              <div className="w-7 h-7 rounded-lg bg-[#534AB7] flex items-center justify-center flex-shrink-0">

                <Brain size={14} color="white" />

              </div>



              <div className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">

                <span className="text-xs text-[#888] mr-1">

                  ResearchMind is thinking

                </span>



                <span

                  className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce"

                  style={{ animationDelay: '0ms' }}

                />



                <span

                  className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce"

                  style={{ animationDelay: '150ms' }}

                />



                <span

                  className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce"

                  style={{ animationDelay: '300ms' }}

                />

              </div>

            </div>

          )}



          <div ref={bottomRef} />

        </div>



        {/* Responsive composer: attachments above, expanding textarea below. */}
        <div className="shrink-0 border-t border-[#3a3a3c] bg-[#2d2d2f]">
          <div className="mx-auto w-full max-w-5xl px-3 py-3 sm:px-5 sm:py-4">
            {pendingFiles.length > 0 && (
              <div className="mb-2 flex max-h-24 flex-wrap gap-2 overflow-y-auto" aria-label="Attached files">
                {pendingFiles.map((item, index) => (
                  <div
                    key={`${item.file.name}-${item.file.size}-${item.file.lastModified}`}
                    className="flex max-w-full items-center gap-2 rounded-xl border border-[#534AB7]/60 bg-[#1e1b4b] px-2.5 py-1.5 text-xs text-[#dedbff]"
                  >
                    {item.type === 'image' ? <ImageIcon size={14} className="shrink-0" /> : <FileText size={14} className="shrink-0" />}
                    <span className="max-w-[min(48vw,240px)] truncate" title={item.preview}>{item.preview}</span>
                    <button
                      type="button"
                      onClick={() => setPendingFiles((previous) => previous.filter((_, fileIndex) => fileIndex !== index))}
                      disabled={loading}
                      aria-label={`Remove ${item.preview}`}
                      className="shrink-0 rounded p-0.5 text-[#aaa5ee] hover:bg-white/10 hover:text-white disabled:opacity-40"
                    >
                      <X size={13} />
                    </button>
                  </div>
                ))}
              </div>
            )}

            {listening && (
              <div className="mb-2 flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-950/30 px-3 py-2 text-xs text-red-300" role="status" aria-live="polite">
                <span className="relative flex h-2.5 w-2.5 shrink-0">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-red-400 opacity-75" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full bg-red-500" />
                </span>
                <span className="flex-1">Recording · Speak naturally; stop when you're done.</span>
                <button type="button" onClick={stopListening} className="font-semibold text-red-200 underline underline-offset-2">Stop recording</button>
              </div>
            )}

            <div className="flex w-full items-end gap-2">
              <AddContentMenu
                selectedCount={pendingFiles.length}
                disabled={loading}
                onFilesSelected={(newFiles) => setPendingFiles((previous) => {
                  const existing = new Set(previous.map((item) => `${item.file.name}:${item.file.size}:${item.file.lastModified}`))
                  const additions = newFiles.filter((item) => !existing.has(`${item.file.name}:${item.file.size}:${item.file.lastModified}`))
                  return [...previous, ...additions]
                })}
              />

              <button
                type="button"
                onClick={listening ? stopListening : startVoiceInput}
                disabled={!micSupported || loading}
                title={!micSupported ? 'Voice input is not supported in this browser' : listening ? 'Stop recording' : 'Start voice input'}
                aria-label={listening ? 'Stop recording' : 'Start voice input'}
                aria-pressed={listening}
                className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full border transition-all disabled:cursor-not-allowed disabled:opacity-30 ${listening ? 'border-red-400 bg-red-500/15 text-red-300 shadow-[0_0_0_3px_rgba(248,113,113,0.12)]' : 'border-[#3a3a3c] text-[#999] hover:border-[#534AB7] hover:text-white'}`}
              >
                {listening ? <MicOff size={16} /> : <Mic size={16} />}
              </button>

              <textarea
                ref={textareaRef}
                rows={1}
                value={input}
                disabled={loading}
                onChange={(event) => setInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                    event.preventDefault()
                    if (!loading) void sendMessage()
                  }
                }}
placeholder={
  loading
    ? 'ResearchMind is working…'
    : pendingFiles.length
      ? 'Ask about attached files…'
      : 'Ask anything…'
}
title="Press Enter to send · Shift + Enter for a new line"
                aria-label="Message to ResearchMind"
                className="min-h-10 max-h-36 min-w-0 flex-1 resize-none overflow-y-hidden rounded-2xl border border-[#3a3a3c] bg-[#1c1c1e] px-4 py-2.5 text-sm leading-5 text-white outline-none transition-colors placeholder:text-[#666] focus:border-[#534AB7] disabled:cursor-wait disabled:opacity-70"
              />

              {loading ? (
                <button
                  type="button"
                  onClick={stopGeneration}
                  title="Stop generation"
                  aria-label="Stop generation"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#7b3030] text-white transition-colors hover:bg-[#a33c3c]"
                >
                  <StopCircle size={18} />
                </button>
              ) : (
                <button
                  type="button"
                  onClick={() => void sendMessage()}
                  disabled={!input.trim() && pendingFiles.length === 0}
                  title="Send message"
                  aria-label="Send message"
                  className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-[#534AB7] text-white transition-colors hover:bg-[#3C3489] disabled:cursor-not-allowed disabled:opacity-40"
                >
                  <Send size={15} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

    </Layout>

  )

}


