import { useState, useEffect } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Zap, Layers, FileText, Briefcase, ChevronRight, RotateCcw, Check, X, Upload } from 'lucide-react'
import Layout from '../Components/Layout'
import client from '../Api/client'
import Spinner from '../Components/ui/Spinner'
import Button from '../Components/ui/button'
import DocumentPicker from '../Components/DocumentPicker'
import { useDocuments } from '../hooks/useDocuments'
import { useTopics } from '../hooks/useTopics'
import LimitReachedModal from '../Components/LimitReachedModal'

type Tab = 'quiz' | 'flashcards' | 'summary' | 'interview'
type Difficulty = 'easy' | 'medium' | 'hard'

interface Question {
  question: string
  options: string[]
  correct: number
  explanation: string
  topic: string
}

interface Flashcard {
  front: string
  back: string
  topic: string
}

export default function StudyMode() {
  const [searchParams] = useSearchParams()
  const { documents, isLoading: docsLoading } = useDocuments()
  const [selectedDocIds, setSelectedDocIds] = useState<number[]>([])
  const [selectedTopic, setSelectedTopic] = useState<string | null>(null)
  const { topics } = useTopics(selectedDocIds)

    useEffect(() => {
    setSelectedTopic(null)
  }, [selectedDocIds])

  // Clear generated Study Mode content when selection changes.
  useEffect(() => {
    setActionError('')
    setQuestions([])
    setFlashcards([])
    setSummary('')
    setInterviewQuestion(null)
    setInterviewAnswer('')
    setInterviewFeedback(null)
    setCurrentQ(0)
    setSelected(null)
    setChecked(false)
    setScore(0)
    setQuizDone(false)
    setFlipped(false)
    setCurrentCard(0)
  }, [selectedDocIds, selectedTopic])


  useEffect(() => {
    setQuestions([])
    setFlashcards([])
    setSummary('')
    setInterviewQuestion(null)
    setInterviewAnswer('')
    setInterviewFeedback(null)

    setCurrentQ(0)
    setSelected(null)
    setChecked(false)
    setScore(0)
    setQuizDone(false)

    setFlipped(false)
    setCurrentCard(0)
  }, [selectedDocIds, selectedTopic])

  const [activeTab, setActiveTab] = useState<Tab>('quiz')
  const [difficulty, setDifficulty] = useState<Difficulty>('medium')
  const [questions, setQuestions] = useState<Question[]>([])
  const [flashcards, setFlashcards] = useState<Flashcard[]>([])
  const [summary, setSummary] = useState<string>('')
  const [interviewQuestion, setInterviewQuestion] = useState<any>(null)
  const [interviewAnswer, setInterviewAnswer] = useState('')
  const [interviewFeedback, setInterviewFeedback] = useState<any>(null)
  const [currentQ, setCurrentQ] = useState(0)
  const [selected, setSelected] = useState<number | null>(null)
  const [checked, setChecked] = useState(false)
  const [score, setScore] = useState(0)
  const [quizDone, setQuizDone] = useState(false)
  const [flipped, setFlipped] = useState(false)
  const [currentCard, setCurrentCard] = useState(0)
  const [loading, setLoading] = useState(false)
  const [submittingScore, setSubmittingScore] = useState(false)
  const [limitModalOpen, setLimitModalOpen] = useState(false)
  const [limitMessage, setLimitMessage] = useState('')
  const [actionError, setActionError] = useState('')
  const roadmapQuizId = searchParams.get('roadmapId')
  const roadmapStepNumber = searchParams.get('stepNumber')
  const isRoadmapQuiz = Boolean(roadmapQuizId && roadmapStepNumber)
  const hasSelection = selectedDocIds.length > 0

  const readStudyResponse = (response: any, fallback: string) => {
    const data = response?.data
    if (!data || typeof data !== 'object') {
      throw new Error(fallback)
    }
    if (typeof data.error === 'string' && data.error.trim()) {
      throw new Error(data.error)
    }
    return data
  }

  
  const reportStudyError = (err: any, fallback: string) => {
    const status = err?.response?.status
    const detail =
      err?.response?.data?.detail ??
      err?.response?.data?.error

    const rawMessage =
      typeof detail === 'string'
        ? detail
        : typeof err?.message === 'string'
          ? err.message
          : ''

    const quotaExceeded =
      /RESOURCE_EXHAUSTED|GenerateRequestsPerDay|quota exceeded|exceeded your current quota/i.test(
        rawMessage
      )

    if (quotaExceeded) {
      setActionError(
        'AI generation is temporarily unavailable because the Gemini API quota has been reached. Please retry after the quota resets or check your Google AI Studio usage and billing settings.'
      )
      return
    }

    if (status === 429) {
      setLimitMessage(rawMessage || fallback)
      setLimitModalOpen(true)
    } else {
      setActionError(rawMessage || fallback)
    }
  }


  const generateQuiz = async () => {
    setLoading(true)
    setActionError('')
    setQuestions([])
    setCurrentQ(0)
    setScore(0)
    setQuizDone(false)
    setSelected(null)
    setChecked(false)

    try {
      const res = isRoadmapQuiz
        ? await client.post(`/roadmap/${roadmapQuizId}/steps/${roadmapStepNumber}/quiz`)
        : await client.post('/features/quiz', {
            num_questions: 5,
            difficulty,
            document_ids: selectedDocIds,
            topic: selectedTopic
          })
      const data = readStudyResponse(res, 'The server returned an invalid quiz response.')
      if (!Array.isArray(data.questions)) {
        throw new Error('The quiz response did not contain a questions list. Please try again.')
      }
      const validQuestions: Question[] = data.questions
        .filter((item: any) => item && typeof item.question === 'string' && Array.isArray(item.options))
        .map((item: any): Question => ({
          question: item.question,
          options: item.options.map((option: unknown) => String(option)),
          correct: Number(item.correct),
          explanation: typeof item.explanation === 'string' ? item.explanation : '',
          topic: typeof item.topic === 'string' ? item.topic : (selectedTopic || 'General')
        }))
        .filter((item: Question) => item.options.length >= 2 && Number.isInteger(item.correct) && item.correct >= 0 && item.correct < item.options.length)
      if (validQuestions.length === 0) {
        throw new Error('No valid quiz questions were generated. Please try again.')
      }
      setQuestions(validQuestions)
    } catch (err: any) {
      reportStudyError(err, 'Failed to generate the quiz. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleAnswer = (index: number) => {
    const question = questions[currentQ]
    if (checked || !question) return
    setSelected(index)
    setChecked(true)
    if (index === question.correct) {
      setScore(s => s + 1)
    }
  }

  const nextQuestion = async () => {
    if (currentQ + 1 >= questions.length) {
      setSubmittingScore(true)
      setActionError('')
      try {
        const res = await client.post('/features/quiz/score', {
          score,
          total: questions.length,
          document_ids: selectedDocIds,
          topic: selectedTopic,
          difficulty,
          roadmap_id: searchParams.get('roadmapId') ? Number(searchParams.get('roadmapId')) : undefined,
          step_number: searchParams.get('stepNumber') ? Number(searchParams.get('stepNumber')) : undefined
        })
        readStudyResponse(res, 'The server returned an invalid score response.')
        setQuizDone(true)
      } catch (err: any) {
        reportStudyError(err, 'Could not save your quiz score. Please try again.')
      } finally {
        setSubmittingScore(false)
      }
    } else {
      setCurrentQ(q => q + 1)
      setSelected(null)
      setChecked(false)
    }
  }

  const generateFlashcards = async () => {
    setLoading(true)
    setActionError('')
    setFlashcards([])
    setCurrentCard(0)
    setFlipped(false)
    try {
      const res = await client.post('/features/flashcards', {
        document_ids: selectedDocIds,
        topic: selectedTopic,
        count: 10
      })
      const data = readStudyResponse(res, 'The server returned an invalid flashcard response.')
      if (!Array.isArray(data.flashcards)) {
        throw new Error('The flashcard response did not contain a flashcards list. Please try again.')
      }
      const validCards: Flashcard[] = data.flashcards
        .filter((item: any) => item && typeof item.front === 'string' && typeof item.back === 'string')
        .map((item: any): Flashcard => ({
          front: item.front,
          back: item.back,
          topic: typeof item.topic === 'string' ? item.topic : (selectedTopic || 'General')
        }))
      if (validCards.length === 0) {
        throw new Error('No flashcards were generated. Check the selected document and try again.')
      }
      setFlashcards(validCards)
    } catch (err: any) {
      reportStudyError(err, 'Failed to generate flashcards. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateSummary = async () => {
    setLoading(true)
    setActionError('')
    setSummary('')
    try {
      const res = await client.post('/features/summary', {
        document_ids: selectedDocIds,
        topic: selectedTopic
      })
      const data = readStudyResponse(res, 'The server returned an invalid summary response.')
      if (typeof data.summary !== 'string' || !data.summary.trim()) {
        throw new Error('The server returned an empty summary. Please try again.')
      }
      setSummary(data.summary)
    } catch (err: any) {
      reportStudyError(err, 'Failed to generate the summary. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const generateInterviewQuestion = async () => {
    setLoading(true)
    setActionError('')
    setInterviewQuestion(null)
    setInterviewAnswer('')
    setInterviewFeedback(null)
    try {
      const res = await client.post('/features/interview/question', {
        document_ids: selectedDocIds,
        topic: selectedTopic
      })
      const data = readStudyResponse(res, 'The server returned an invalid interview question.')
      if (typeof data.question !== 'string' || !data.question.trim()) {
        throw new Error('No interview question was generated. Please try again.')
      }
      setInterviewQuestion({
        ...data,
        key_points: Array.isArray(data.key_points) ? data.key_points.filter((point: unknown) => typeof point === 'string') : [],
        topic: typeof data.topic === 'string' ? data.topic : (selectedTopic || 'General')
      })
    } catch (err: any) {
      reportStudyError(err, 'Failed to generate an interview question. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const evaluateAnswer = async () => {
    if (!interviewAnswer.trim() || !interviewQuestion) return
    setLoading(true)
    setActionError('')
    setInterviewFeedback(null)
    try {
      const res = await client.post('/features/interview/evaluate', {
        question: interviewQuestion.question,
        answer: interviewAnswer,
        key_points: Array.isArray(interviewQuestion.key_points) ? interviewQuestion.key_points : []
      })
      const data = readStudyResponse(res, 'The server returned invalid interview feedback.')
      if (typeof data.score !== 'number' || typeof data.feedback !== 'string') {
        throw new Error('The interview feedback was incomplete. Please submit your answer again.')
      }
      setInterviewFeedback({
        ...data,
        max_score: typeof data.max_score === 'number' ? data.max_score : 10,
        covered_points: Array.isArray(data.covered_points) ? data.covered_points : [],
        missed_points: Array.isArray(data.missed_points) ? data.missed_points : []
      })
    } catch (err: any) {
      reportStudyError(err, 'Failed to evaluate your answer. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const tabs = [
    { id: 'quiz' as Tab, label: 'Quiz', icon: Zap },
    { id: 'flashcards' as Tab, label: 'Flashcards', icon: Layers },
    { id: 'summary' as Tab, label: 'Summary', icon: FileText },
    { id: 'interview' as Tab, label: 'Interview', icon: Briefcase }
  ]

  const EmptyIcon = {
    quiz: Zap,
    flashcards: Layers,
    summary: FileText,
    interview: Briefcase
  }[activeTab]

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">

        <div className="px-3 sm:px-5 py-3 pl-14 md:pl-5 border-b border-[#3a3a3c] bg-[#2d2d2f] flex-shrink-0">
          <h1 className="text-sm font-semibold text-white mb-3">Study mode</h1>
          <div className="flex flex-wrap gap-1">
            {tabs.map(tab => {
              const Icon = tab.icon
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                    activeTab === tab.id ? 'bg-[#534AB7] text-white' : 'text-[#888] hover:text-white hover:bg-[#1c1c1e]'
                  }`}
                >
                  <Icon size={13} />
                  {tab.label}
                </button>
              )
            })}
          </div>
        </div>

        <div className="flex-1 min-h-0 overflow-y-auto p-3 sm:p-5 bg-[#2d2d2f]">
          {actionError && (
            <div role="alert" className="max-w-2xl mx-auto mb-4 flex items-start justify-between gap-3 rounded-xl border border-red-800 bg-red-900/20 px-4 py-3 text-sm text-red-300">
              <p className="whitespace-pre-wrap">{actionError}</p>
              <button type="button" onClick={() => setActionError('')} className="shrink-0 text-red-200 hover:text-white" aria-label="Dismiss error">Dismiss</button>
            </div>
          )}

          {!docsLoading && documents.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4 text-center max-w-2xl mx-auto">
              <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                <Upload size={26} className="text-[#7C75D4]" />
              </div>
              <h2 className="text-base font-semibold text-white">Upload a document first</h2>
              <p className="text-sm text-[#666] max-w-xs">Study mode generates quizzes, flashcards, and summaries from your documents</p>
              <Link to="/documents">
                <Button>Go to My documents</Button>
              </Link>
            </div>
          ) : (
            <>
              <div className="flex items-center gap-3 mb-5 flex-wrap max-w-2xl mx-auto">
                <DocumentPicker
                  documents={documents}
                  selectedIds={selectedDocIds}
                  onChange={setSelectedDocIds}
                />

                {selectedDocIds.length > 0 && (
                  <>
                    <div className="w-px h-5 bg-[#3a3a3c]" />
                    <select
                      value={selectedTopic ?? ''}
                      onChange={e => setSelectedTopic(e.target.value || null)}
                      className="bg-[#1c1c1e] border border-[#3a3a3c] text-xs text-white rounded-lg px-3 py-1.5 outline-none"
                    >
                      <option value="">All topics</option>
                      {topics.map(t => (
                        <option key={t} value={t}>{t}</option>
                      ))}
                    </select>
                  </>
                )}

                {activeTab === 'quiz' && (
                  <div className="flex border border-[#3a3a3c] rounded-lg overflow-hidden ml-auto">
                    {(['easy', 'medium', 'hard'] as Difficulty[]).map(d => (
                      <button
                        key={d}
                        onClick={() => setDifficulty(d)}
                        className={`px-3 py-1.5 text-xs capitalize transition-colors ${
                          difficulty === d ? 'bg-[#534AB7] text-white' : 'text-[#888] hover:text-white'
                        }`}
                      >
                        {d}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {!hasSelection && (
                <div className="mb-5 text-xs text-[#7C75D4] bg-[#1e1b4b] border border-[#534AB7]/30 rounded-lg px-3 py-2 inline-block max-w-2xl mx-auto flex justify-center w-full">
                  Select at least one document to get started
                </div>
              )}

              {activeTab === 'quiz' && (
                <div className="max-w-2xl mx-auto">
                  {questions.length === 0 && !loading && (
                    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                      <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                        <EmptyIcon size={26} className="text-[#7C75D4]" />
                      </div>
                      <h2 className="text-base font-semibold text-white">Ready to test yourself?</h2>
                      <p className="text-sm text-[#666] max-w-xs">AI generates questions from your selected documents</p>
                      <Button onClick={generateQuiz} disabled={!hasSelection && !isRoadmapQuiz} className="px-8">
                        Start quiz
                      </Button>
                    </div>
                  )}

                  {loading && <div className="flex justify-center py-20"><Spinner /></div>}

                  {questions.length > 0 && !quizDone && !loading && (
                    <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-2">
                        <span className="text-xs text-[#666]">Question {currentQ + 1} of {questions.length}</span>
                        <span className="text-xs text-[#666]">{score} correct</span>
                      </div>
                      <div className="h-1 bg-[#2d2d2f] rounded-full mb-5">
                        <div
                          className="h-1 bg-[#534AB7] rounded-full transition-all"
                          style={{ width: `${(currentQ / questions.length) * 100}%` }}
                        />
                      </div>
                      <p className="text-base font-semibold text-white mb-5 leading-relaxed">
                        {questions[currentQ].question}
                      </p>
                      <div className="flex flex-col gap-2 mb-5">
                        {questions[currentQ].options.map((opt, i) => {
                          let style = 'bg-[#2d2d2f] border-[#3a3a3c] text-[#ccc]'
                          if (checked) {
                            if (i === questions[currentQ].correct) style = 'bg-green-900/30 border-green-600 text-green-400'
                            else if (i === selected) style = 'bg-red-900/30 border-red-600 text-red-400'
                            else style = 'bg-[#2d2d2f] border-[#3a3a3c] text-[#555]'
                          } else if (selected === i) {
                            style = 'bg-[#1e1b4b] border-[#534AB7] text-white'
                          }
                          return (
                            <button
                              key={i}
                              onClick={() => handleAnswer(i)}
                              className={`flex items-center gap-3 px-4 py-3 rounded-xl border text-sm text-left transition-colors ${style}`}
                            >
                              {checked && i === questions[currentQ].correct && <Check size={14} className="flex-shrink-0" />}
                              {checked && i === selected && i !== questions[currentQ].correct && <X size={14} className="flex-shrink-0" />}
                              {opt}
                            </button>
                          )
                        })}
                      </div>
                      {checked && (
                        <div className="bg-[#2d2d2f] rounded-xl p-3 mb-4">
                          <p className="text-xs text-[#999] leading-relaxed">{questions[currentQ].explanation}</p>
                        </div>
                      )}
                      {checked && (
                        <div className="flex justify-end">
                          <Button onClick={nextQuestion} size="sm" disabled={submittingScore}>
                            {submittingScore ? 'Saving...' : (currentQ + 1 >= questions.length ? 'Finish' : 'Next')} <ChevronRight size={14} />
                          </Button>
                        </div>
                      )}
                    </div>
                  )}

                  {quizDone && (
                    <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-8 text-center">
                      <div className="text-4xl mb-3">{score >= 4 ? '🎉' : score >= 3 ? '👍' : '📚'}</div>
                      <h2 className="text-xl font-bold text-white mb-1">{score}/{questions.length} correct</h2>
                      <p className="text-sm text-[#666] mb-6">
                        {score >= 4 ? 'Excellent work!' : score >= 3 ? 'Good job, keep going!' : "Keep studying, you'll get there!"}
                      </p>
                      <Button onClick={generateQuiz}>
                        <RotateCcw size={14} /> Try again
                      </Button>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'flashcards' && (
                <div className="max-w-2xl mx-auto">
                  {flashcards.length === 0 && !loading && (
                    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                      <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                        <EmptyIcon size={26} className="text-[#7C75D4]" />
                      </div>
                      <h2 className="text-base font-semibold text-white">Generate flashcards</h2>
                      <p className="text-sm text-[#666] max-w-xs">AI creates question/answer cards from your selected documents</p>
                      <Button onClick={generateFlashcards} disabled={!hasSelection}>Generate flashcards</Button>
                    </div>
                  )}

                  {loading && <div className="flex justify-center py-20"><Spinner /></div>}

                  {flashcards.length > 0 && !loading && (
                    <div>
                      <div className="flex items-center justify-between mb-4">
                        <span className="text-xs text-[#666]">Card {currentCard + 1} of {flashcards.length}</span>
                        <button onClick={generateFlashcards} className="text-xs text-[#666] hover:text-white flex items-center gap-1 transition-colors">
                          <RotateCcw size={12} /> Regenerate
                        </button>
                      </div>
                      <div
                        onClick={() => setFlipped(f => !f)}
                        className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-8 min-h-48 flex flex-col items-center justify-center text-center cursor-pointer hover:border-[#534AB7] transition-colors mb-4"
                      >
                        <p className="text-xs text-[#666] mb-3">{flipped ? 'Answer' : 'Question'}</p>
                        <p className="text-base text-white leading-relaxed">
                          {flipped ? flashcards[currentCard].back : flashcards[currentCard].front}
                        </p>
                        <p className="text-xs text-[#444] mt-4">Click to {flipped ? 'see question' : 'reveal answer'}</p>
                      </div>
                      <div className="flex items-center justify-between">
                        <button
                          onClick={() => { setCurrentCard(c => Math.max(0, c - 1)); setFlipped(false) }}
                          disabled={currentCard === 0}
                          className="text-xs px-4 py-2 border border-[#3a3a3c] text-[#888] rounded-lg hover:text-white disabled:opacity-30 transition-colors"
                        >
                          ← Previous
                        </button>
                        <div className="flex gap-1">
                          {flashcards.map((_, i) => (
                            <div key={i} className={`w-1.5 h-1.5 rounded-full transition-colors ${i === currentCard ? 'bg-[#534AB7]' : 'bg-[#3a3a3c]'}`} />
                          ))}
                        </div>
                        <button
                          onClick={() => { setCurrentCard(c => Math.min(flashcards.length - 1, c + 1)); setFlipped(false) }}
                          disabled={currentCard === flashcards.length - 1}
                          className="text-xs px-4 py-2 border border-[#3a3a3c] text-[#888] rounded-lg hover:text-white disabled:opacity-30 transition-colors"
                        >
                          Next →
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'summary' && (
                <div className="max-w-2xl mx-auto">
                  {!summary && !loading && (
                    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                      <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                        <EmptyIcon size={26} className="text-[#7C75D4]" />
                      </div>
                      <h2 className="text-base font-semibold text-white">Smart summary</h2>
                      <p className="text-sm text-[#666] max-w-xs">Get key points and important terms from your selected documents</p>
                      <Button onClick={generateSummary} disabled={!hasSelection}>Generate summary</Button>
                    </div>
                  )}

                  {loading && <div className="flex justify-center py-20"><Spinner /></div>}

                  {summary && !loading && (
                    <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
                      <div className="flex items-center justify-between mb-4">
                        <h2 className="text-sm font-semibold text-white">Summary</h2>
                        <button onClick={generateSummary} className="text-xs text-[#666] hover:text-white flex items-center gap-1 transition-colors">
                          <RotateCcw size={12} /> Refresh
                        </button>
                      </div>
                      <pre className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap font-sans">{summary}</pre>
                    </div>
                  )}
                </div>
              )}

              {activeTab === 'interview' && (
                <div className="max-w-2xl mx-auto">
                  {!interviewQuestion && !loading && (
                    <div className="flex flex-col items-center justify-center py-16 gap-4 text-center">
                      <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                        <EmptyIcon size={26} className="text-[#7C75D4]" />
                      </div>
                      <h2 className="text-base font-semibold text-white">Interview mode</h2>
                      <p className="text-sm text-[#666] max-w-xs">Practice open-ended questions and get AI feedback on your answers</p>
                      <Button onClick={generateInterviewQuestion} disabled={!hasSelection}>Start interview</Button>
                    </div>
                  )}

                  {loading && <div className="flex justify-center py-20"><Spinner /></div>}

                  {interviewQuestion && !loading && (
                    <div className="flex flex-col gap-4">
                      <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
                        <p className="text-xs text-[#666] mb-2">Question — {interviewQuestion.topic}</p>
                        <p className="text-base font-semibold text-white leading-relaxed mb-4">{interviewQuestion.question}</p>
                        <div className="flex flex-wrap gap-1">
                          {interviewQuestion.key_points?.map((kp: string) => (
                            <span key={kp} className="text-xs px-2 py-0.5 bg-[#1e1b4b] text-[#7C75D4] rounded-full">{kp}</span>
                          ))}
                        </div>
                      </div>

                      {!interviewFeedback && (
                        <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-4">
                          <textarea
                            value={interviewAnswer}
                            onChange={e => setInterviewAnswer(e.target.value)}
                            placeholder="Type your answer here..."
                            rows={5}
                            className="w-full bg-transparent text-sm text-white outline-none resize-none placeholder:text-[#555]"
                          />
                          <div className="flex justify-end mt-3">
                            <Button onClick={evaluateAnswer} disabled={!interviewAnswer.trim() || loading} size="sm">
                              {loading ? 'Evaluating...' : 'Submit answer'}
                            </Button>
                          </div>
                        </div>
                      )}

                      {interviewFeedback && (
                        <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
                          <div className="flex items-center justify-between mb-4">
                            <h3 className="text-sm font-semibold text-white">Feedback</h3>
                            <span className="text-lg font-bold text-[#7C75D4]">
                              {interviewFeedback.score}/{interviewFeedback.max_score}
                            </span>
                          </div>
                          <p className="text-sm text-[#ccc] leading-relaxed mb-4">{interviewFeedback.feedback}</p>
                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                            <div className="bg-green-900/20 border border-green-800 rounded-xl p-3">
                              <p className="text-xs text-green-400 mb-1">Covered</p>
                              {interviewFeedback.covered_points?.map((p: string) => (
                                <p key={p} className="text-xs text-[#ccc] flex items-start gap-1"><Check size={10} className="mt-0.5 text-green-400 flex-shrink-0" />{p}</p>
                              ))}
                            </div>
                            <div className="bg-red-900/20 border border-red-800 rounded-xl p-3">
                              <p className="text-xs text-red-400 mb-1">Missed</p>
                              {interviewFeedback.missed_points?.map((p: string) => (
                                <p key={p} className="text-xs text-[#ccc] flex items-start gap-1"><X size={10} className="mt-0.5 text-red-400 flex-shrink-0" />{p}</p>
                              ))}
                            </div>
                          </div>
                          <Button onClick={generateInterviewQuestion} variant="ghost" size="sm" className="w-full">
                            <RotateCcw size={13} /> Next question
                          </Button>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>
      </div>
      <LimitReachedModal
        open={limitModalOpen}
        onClose={() => setLimitModalOpen(false)}
        message={limitMessage}
      />
    </Layout>
  )
}