import { useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Plus, CheckCircle, Circle, Clock, Flame, BookOpen, Trophy, Map } from 'lucide-react'
import Layout from '../Components/Layout'
import client from '../Api/client'
import Spinner from '../Components/ui/Spinner'
import Button from '../Components/ui/button'
import Input from '../Components/ui/input'
import { useRoadmaps } from '../hooks/useRoadmaps'

interface RoadmapStep {
  step_number: number
  title: string
  description: string
  status: 'upcoming' | 'in_progress' | 'completed'
  estimated_days: number
  quiz_passed: boolean
  resources_ingested: boolean
}

interface RoadmapProgress {
  goal: string
  progress_percentage: number
  completed_steps: number
  total_steps: number
  estimated_remaining_days: number
  streak: number
  steps: RoadmapStep[]
}

export default function Roadmap() {
  const queryClient = useQueryClient()
  const [searchParams, setSearchParams] = useSearchParams()
  const selectedRoadmapId = searchParams.get('id') ? Number(searchParams.get('id')) : null
  const creating = searchParams.get('new') === 'true'

  const { refetchRoadmaps } = useRoadmaps()

  const [goal, setGoal] = useState('')
  const [currentKnowledge, setCurrentKnowledge] = useState('')
  const [createError, setCreateError] = useState('')

  const {
    data: progress,
    isLoading: loadingProgress,
    isError: progressError,
    error: progressErrorObj,
    refetch: refetchProgress
  } = useQuery({
    queryKey: ['roadmap-progress', selectedRoadmapId],
    queryFn: async () => {
      const res = await client.get(`/roadmap/${selectedRoadmapId}/progress`)
      return res.data as RoadmapProgress
    },
    enabled: !!selectedRoadmapId,
    retry: 2,
    retryDelay: 1000
  })

  const createMutation = useMutation({
    mutationFn: (data: any) => client.post('/roadmap/', data),
    onSuccess: (res) => {
      refetchRoadmaps()
      setSearchParams({ id: String(res.data.roadmap_id) })
      setGoal('')
      setCurrentKnowledge('')
      setCreateError('')
    },
    onError: (err: any) => {
      setCreateError(err.response?.data?.detail || 'Failed to generate roadmap. Please try again.')
    }
  })

  const startStepMutation = useMutation({
    mutationFn: (data: any) => client.post('/roadmap/start-step', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmap-progress', selectedRoadmapId] })
    }
  })

  const completeStepMutation = useMutation({
    mutationFn: (data: any) => client.post('/roadmap/complete-step', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roadmap-progress', selectedRoadmapId] })
    }
  })

  const handleCreate = () => {
    if (!goal.trim()) return
    setCreateError('')
    createMutation.mutate({
      goal,
      current_knowledge: currentKnowledge || 'beginner'
    })
  }

  const statusIcon = (step: RoadmapStep) => {
    if (step.status === 'completed') return <CheckCircle size={18} className="text-green-400 flex-shrink-0" />
    if (step.status === 'in_progress') return <Circle size={18} className="text-[#534AB7] flex-shrink-0" />
    return <Circle size={18} className="text-[#444] flex-shrink-0" />
  }

  return (
    <Layout>
      <div className="flex-1 flex flex-col overflow-hidden">

        <div className="px-5 py-3 border-b border-[#3a3a3c] bg-[#2d2d2f] flex-shrink-0">
          <h1 className="text-sm font-semibold text-white">Learning roadmap</h1>
        </div>

        <div className="flex-1 overflow-y-auto p-5 bg-[#2d2d2f]">

          {creating && (
            <div className="max-w-xl mx-auto">
              <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-2xl p-6">
                <h2 className="text-base font-semibold text-white mb-1">Create learning roadmap</h2>
                <p className="text-xs text-[#666] mb-5">Tell us your goal and what you already know — we'll build a personalised path.</p>

                <div className="flex flex-col gap-4">
                  <Input
                    label="What do you want to learn?"
                    placeholder="e.g. I want to become an AI engineer"
                    value={goal}
                    onChange={e => setGoal(e.target.value)}
                  />
                  <Input
                    label="What do you already know? (optional)"
                    placeholder="e.g. I know Python basics and have built some web apps"
                    value={currentKnowledge}
                    onChange={e => setCurrentKnowledge(e.target.value)}
                  />
                  <div className="flex gap-2">
                    <Button
                      onClick={handleCreate}
                      disabled={!goal.trim() || createMutation.isPending}
                      className="flex-1"
                    >
                      {createMutation.isPending ? 'Generating...' : 'Generate roadmap'}
                    </Button>
                    <Button variant="ghost" onClick={() => setSearchParams({})}>
                      Cancel
                    </Button>
                  </div>
                  {createError && <p className="text-xs text-red-400">{createError}</p>}
                </div>
              </div>
            </div>
          )}

          {!creating && !selectedRoadmapId && (
            <div className="flex flex-col items-center justify-center py-24 gap-4 text-center max-w-xl mx-auto">
              <div className="w-14 h-14 bg-[#1e1b4b] rounded-2xl flex items-center justify-center">
                <Map size={26} className="text-[#7C75D4]" />
              </div>
              <h2 className="text-base font-semibold text-white">No roadmap selected</h2>
              <p className="text-sm text-[#666] max-w-xs">Create a new roadmap or select an existing one from the sidebar</p>
              <Button onClick={() => setSearchParams({ new: 'true' })}>
                <Plus size={14} /> Create roadmap
              </Button>
            </div>
          )}

          {selectedRoadmapId && !creating && (
            <div className="max-w-2xl mx-auto">
              {loadingProgress ? (
                <div className="flex justify-center py-20"><Spinner /></div>
              ) : progressError ? (
                <div className="flex flex-col items-center justify-center py-24 gap-3 text-center">
                  <div className="w-14 h-14 bg-[#3a1c1c] rounded-2xl flex items-center justify-center text-3xl">⚠️</div>
                  <h2 className="text-sm font-semibold text-white">Couldn't load this roadmap</h2>
                  <p className="text-xs text-[#666] max-w-xs">
                    {(progressErrorObj as any)?.response?.data?.detail || 'Something went wrong. Please try again.'}
                  </p>
                  <button
                    onClick={() => refetchProgress()}
                    className="text-xs px-4 py-2 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors"
                  >
                    Try again
                  </button>
                </div>
              ) : progress && (
                <div className="flex flex-col gap-5">

                  <div className="grid grid-cols-4 gap-3">
                    {[
                      { icon: Trophy, label: 'Progress', value: `${progress.progress_percentage}%`, color: 'text-[#7C75D4]' },
                      { icon: CheckCircle, label: 'Completed', value: `${progress.completed_steps}/${progress.total_steps}`, color: 'text-green-400' },
                      { icon: Clock, label: 'Days left', value: `~${progress.estimated_remaining_days}`, color: 'text-amber-400' },
                      { icon: Flame, label: 'Streak', value: `${progress.streak} days`, color: 'text-orange-400' }
                    ].map(stat => {
                      const Icon = stat.icon
                      return (
                        <div key={stat.label} className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl p-3 text-center">
                          <Icon size={16} className={`${stat.color} mx-auto mb-1`} />
                          <p className={`text-base font-bold ${stat.color}`}>{stat.value}</p>
                          <p className="text-xs text-[#555]">{stat.label}</p>
                        </div>
                      )
                    })}
                  </div>

                  <div className="bg-[#1c1c1e] border border-[#2a2a2a] rounded-xl p-4">
                    <div className="flex items-center justify-between mb-2">
                      <p className="text-xs text-white font-medium truncate max-w-xs">{progress.goal}</p>
                      <span className="text-xs text-[#666]">{progress.progress_percentage}%</span>
                    </div>
                    <div className="h-2 bg-[#2d2d2f] rounded-full">
                      <div
                        className="h-2 bg-[#534AB7] rounded-full transition-all duration-500"
                        style={{ width: `${progress.progress_percentage}%` }}
                      />
                    </div>
                  </div>

                  <div className="flex flex-col gap-3">
                    {progress.steps.map(step => (
                      <div
                        key={step.step_number}
                        className={`bg-[#1c1c1e] border rounded-2xl p-5 transition-colors ${
                          step.status === 'in_progress' ? 'border-[#534AB7]' :
                          step.status === 'completed' ? 'border-green-800' : 'border-[#2a2a2a]'
                        }`}
                      >
                        <div className="flex items-start gap-3">
                          {statusIcon(step)}
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <h3 className={`text-sm font-semibold ${
                                step.status === 'completed' ? 'text-green-400' :
                                step.status === 'in_progress' ? 'text-white' : 'text-[#666]'
                              }`}>
                                {step.step_number}. {step.title}
                              </h3>
                              <div className="flex items-center gap-1 flex-shrink-0 ml-2">
                                <Clock size={11} className="text-[#555]" />
                                <span className="text-xs text-[#555]">{step.estimated_days}d</span>
                              </div>
                            </div>
                            <p className="text-xs text-[#666] leading-relaxed mb-3">{step.description}</p>

                            <div className="flex items-center gap-2 flex-wrap">
                              {step.status === 'upcoming' && (
                                <button
                                  onClick={() => startStepMutation.mutate({
                                    roadmap_id: selectedRoadmapId,
                                    step_number: step.step_number
                                  })}
                                  disabled={startStepMutation.isPending}
                                  className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-[#534AB7] text-white rounded-lg hover:bg-[#3C3489] transition-colors"
                                >
                                  <BookOpen size={12} /> Start step
                                </button>
                              )}

                              {step.status === 'in_progress' && (
                                <>
                                  {step.resources_ingested && (
                                    <span className="text-xs text-green-400 flex items-center gap-1">
                                      <CheckCircle size={11} /> Resources added to knowledge base
                                    </span>
                                  )}
                                  <button
                                    onClick={() => completeStepMutation.mutate({
                                      roadmap_id: selectedRoadmapId,
                                      step_number: step.step_number,
                                      quiz_passed: step.quiz_passed
                                    })}
                                    disabled={!step.quiz_passed || completeStepMutation.isPending}
                                    className="flex items-center gap-1.5 text-xs px-3 py-1.5 bg-green-700 text-white rounded-lg hover:bg-green-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
                                  >
                                    <CheckCircle size={12} />
                                    {step.quiz_passed ? 'Mark complete' : 'Pass quiz first'}
                                  </button>
                                </>
                              )}

                              {step.status === 'completed' && (
                                <span className="text-xs text-green-400 flex items-center gap-1">
                                  <CheckCircle size={11} /> Completed
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </Layout>
  )
}