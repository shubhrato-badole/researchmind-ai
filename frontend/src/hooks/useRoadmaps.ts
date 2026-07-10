import { useQuery, useQueryClient } from '@tanstack/react-query'
import client from '../Api/client'

export interface Roadmap {
  id: number
  goal: string
  current_step: number
  streak: number
}

export function useRoadmaps() {
  const queryClient = useQueryClient()

  const { data: roadmaps = [], isLoading } = useQuery({
    queryKey: ['roadmaps'],
    queryFn: async () => {
      const res = await client.get('/roadmap/')
      return res.data.roadmaps as Roadmap[]
    }
  })

  const refetchRoadmaps = () => queryClient.invalidateQueries({ queryKey: ['roadmaps'] })

  return { roadmaps, isLoading, refetchRoadmaps }
}