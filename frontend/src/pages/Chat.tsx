import { useState, useRef, useEffect, useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Send, Mic, Brain } from 'lucide-react'
import Layout from '../Components/Layout'
import client from '../Api/client'
import Spinner from '../Components/ui/Spinner'
import { useSessions } from '../hooks/useSessions'
import { useVoiceInput } from '../hooks/useVoiceInput'
import { useAuth } from '../context/AuthContext'
import SearchModeDropdown, { type SearchMode } from '../Components/SearchModeDropdown'
import AddContentMenu from '../Components/AddContentMenu'

interface Message {
  role: 'user' | 'assistant'
  content: string
  awaiting_approval?: boolean
  thread_id?: string
}

interface PendingFile {
  file: File
  preview: string
  type: string
}

export default function Chat() {
  const { user } = useAuth()
  const [searchParams, setSearchParams] = useSearchParams()
  const currentSessionId = searchParams.get('session') ? Number(searchParams.get('session')) : null
  const { addSessionOptimistic } = useSessions()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [searchMode, setSearchMode] = useState<SearchMode>('docs_web')
  const [pendingFile, setPendingFile] = useState<PendingFile | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  const handleVoiceResult = useCallback((text: string) => setInput(text), [])
  const { listening, supported: micSupported, toggle: toggleMic } = useVoiceInput(handleVoiceResult)

  useEffect(() => {
    if (currentSessionId) {
      loadSession(currentSessionId)
    } else {
      setMessages([])
    }
  }, [currentSessionId])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const loadSession = async (sessionId: number) => {
    try {
      const res = await client.get(`/chat/history?session_id=${sessionId}`)
      const history = res.data.history.map((msg: any) => ({ role: msg.role, content: msg.message }))
      setMessages(history)
    } catch { }
  }

  const sendMessage = async () => {
    if ((!input.trim() && !pendingFile) || loading) return

    const query = input.trim()
    setInput('')
    setLoading(true)

    setMessages(prev => [...prev, {
      role: 'user',
      content: pendingFile ? `📎 ${pendingFile.preview}${query ? '\n' + query : ''}` : query
    }])

    try {
      if (pendingFile) {
        const formData = new FormData()
        formData.append('file', pendingFile.file)
        await client.post('/ingest/file', formData, {
          headers: { 'Content-Type': 'multipart/form-data' }
        })
        setPendingFile(null)
      }

      if (query) {
        const res = await client.post('/chat/', {
          query,
          search_mode: searchMode,
          session_id: currentSessionId
        })
        const data = res.data

        if (!currentSessionId && data.session_id) {
          setSearchParams({ session: String(data.session_id) })
          addSessionOptimistic({ id: data.session_id, title: query.slice(0, 40), created_at: new Date().toISOString() })
        }

        if (data.status === 'awaiting_approval') {
          setMessages(prev => [...prev, { role: 'assistant', content: data.message, awaiting_approval: true, thread_id: data.thread_id }])
        } else {
          setMessages(prev => [...prev, { role: 'assistant', content: data.answer }])
        }
      } else {
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: `✅ Added to your knowledge base. Ask me anything about it.`
        }])
      }
    } catch {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Something went wrong. Please try again.' }])
    } finally {
      setLoading(false)
    }
  }

  const handleApproval = async (threadId: string, approved: boolean) => {
    setLoading(true)
    try {
      const res = await client.post('/chat/resume', { thread_id: threadId, approved })
      setMessages(prev => [...prev.filter(m => !m.awaiting_approval), { role: 'assistant', content: res.data.answer }])
    } finally {
      setLoading(false)
    }
  }

  const userInitial = user?.name?.[0]?.toUpperCase() || 'U'

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">

        <div className="px-5 py-3 border-b border-[#3a3a3c] flex items-center justify-between bg-[#2d2d2f] flex-shrink-0">
          <h1 className="text-sm font-semibold text-white">
            {currentSessionId ? 'Chat' : 'New chat'}
          </h1>
          <SearchModeDropdown value={searchMode} onChange={setSearchMode} />
        </div>

        <div className="flex-1 overflow-y-auto px-5 py-4 flex flex-col gap-4 bg-[#2d2d2f]">
          {messages.length === 0 && (
            <div className="flex-1 flex flex-col items-center justify-center gap-2 text-center py-16">
              <div className="w-14 h-14 bg-[#534AB7] rounded-2xl flex items-center justify-center">
                <Brain size={26} color="white" />
              </div>
              <h2 className="text-base font-semibold text-white mt-1">Welcome to ResearchMind</h2>
              <p className="text-sm font-medium text-[#AFA9EC] m-0">Ask anything</p>
              <p className="text-sm text-[#999] max-w-xs m-0">Get answers from your documents, or anywhere on the web.</p>

              <div className="grid grid-cols-3 gap-2 mt-3 w-full max-w-md">
                {[
                  { n: 1, title: 'Add content', desc: 'PDF, website, YouTube, or image' },
                  { n: 2, title: 'Ask anything', desc: 'Docs, the web, or general questions' },
                  { n: 3, title: 'Get answers', desc: 'With sources shown' }
                ].map(step => (
                  <div key={step.n} className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-xl p-3">
                    <div className="w-5 h-5 bg-[#1e1b4b] text-[#7C75D4] rounded-full flex items-center justify-center text-[11px] font-medium mx-auto mb-2">{step.n}</div>
                    <p className="text-xs font-medium text-white mb-1">{step.title}</p>
                    <p className="text-[11px] text-[#777] leading-tight">{step.desc}</p>
                  </div>
                ))}
              </div>

              <div className="flex gap-2 mt-3 flex-wrap justify-center">
                {['Summarise my documents', "What's trending in RAG research?", 'Explain reranking'].map(s => (
                  <button
                    key={s}
                    onClick={() => setInput(s)}
                    className="text-xs px-3 py-1.5 bg-[#1c1c1e] border border-[#3a3a3c] rounded-full text-[#999] hover:text-white hover:border-[#534AB7] transition-colors"
                  >
                    {s}
                  </button>
                ))}
              </div>
            </div>
          )}

          {messages.map((msg, i) => (
            <div key={i} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
              <div className={`flex items-start gap-2 max-w-[75%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {msg.role === 'assistant' ? (
                  <div className="w-7 h-7 rounded-lg bg-[#534AB7] flex items-center justify-center flex-shrink-0 mt-0.5">
                    <Brain size={14} color="white" />
                  </div>
                ) : (
                  <div className="w-7 h-7 rounded-full bg-[#1e1b4b] text-[#7C75D4] flex items-center justify-center text-xs font-medium flex-shrink-0 mt-0.5">
                    {userInitial}
                  </div>
                )}
                <div className={`px-4 py-3 rounded-2xl text-sm leading-relaxed ${msg.role === 'user'
                    ? 'bg-[#534AB7] text-white rounded-br-sm'
                    : 'bg-[#1c1c1e] text-white border border-[#3a3a3c] rounded-bl-sm'
                  }`}>
                  {msg.content}
                </div>
              </div>
              {msg.awaiting_approval && msg.thread_id && (
                <div className="flex gap-2 mt-2 ml-9">
                  <button onClick={() => handleApproval(msg.thread_id!, true)} className="text-xs px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors">
                    Yes, search web
                  </button>
                  <button onClick={() => handleApproval(msg.thread_id!, false)} className="text-xs px-4 py-2 bg-[#1c1c1e] text-[#999] border border-[#3a3a3c] rounded-lg hover:text-white transition-colors">
                    Docs only
                  </button>
                </div>
              )}
            </div>
          ))}

          {loading && (
            <div className="flex items-start gap-2">
              <div className="w-7 h-7 rounded-lg bg-[#534AB7] flex items-center justify-center flex-shrink-0">
                <Brain size={14} color="white" />
              </div>
              <div className="bg-[#1c1c1e] border border-[#3a3a3c] rounded-2xl rounded-bl-sm px-4 py-3 flex items-center gap-1.5">
                <span className="text-xs text-[#888] mr-1">Thinking</span>
                <span className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-[#7C75D4] animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <div className="px-4 py-3 border-t border-[#3a3a3c] bg-[#2d2d2f] flex items-center gap-2 flex-shrink-0">
          <AddContentMenu
            pendingFile={pendingFile}
            onFileSelected={setPendingFile}
            onRemove={() => setPendingFile(null)}
          />

          <button
            onClick={toggleMic}
            disabled={!micSupported}
            title={micSupported ? 'Voice input' : 'Voice input not supported in this browser'}
            className={`w-8 h-8 rounded-full border flex items-center justify-center transition-colors flex-shrink-0 disabled:opacity-30 ${listening ? 'border-red-400 text-red-400' : 'border-[#3a3a3c] text-[#666] hover:text-white'
              }`}
          >
            <Mic size={15} />
          </button>

          <input
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            placeholder={pendingFile ? 'Add a message or just send the file...' : 'Ask anything...'}
            className="flex-1 bg-[#1c1c1e] border border-[#3a3a3c] rounded-full px-4 py-2 text-sm text-white outline-none focus:border-[#534AB7] transition-colors placeholder:text-[#555]"
          />
          <button
            onClick={sendMessage}
            disabled={loading || (!input.trim() && !pendingFile)}
            className="w-8 h-8 rounded-full bg-[#534AB7] flex items-center justify-center text-white flex-shrink-0 disabled:opacity-40 hover:bg-[#3C3489] transition-colors"
          >
            <Send size={14} />
          </button>
        </div>
      </div>
    </Layout>
  )
}