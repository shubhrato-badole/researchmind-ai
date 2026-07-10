import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import client from '../Api/client'

export interface Session {
  id: number
  title: string
  created_at: string
}

const SESSIONS_KEY = ['sessions']

export function useSessions() {
  const queryClient = useQueryClient()

  const { data: sessions = [], isLoading } = useQuery({
    queryKey: SESSIONS_KEY,
    queryFn: async () => {
      const res = await client.get('/chat/sessions')
      return res.data.sessions as Session[]
    }
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => client.delete(`/chat/sessions/${id}`),
    onMutate: async (id: number) => {
      await queryClient.cancelQueries({ queryKey: SESSIONS_KEY })
      const previous = queryClient.getQueryData<Session[]>(SESSIONS_KEY)
      queryClient.setQueryData<Session[]>(SESSIONS_KEY, old => (old ?? []).filter(s => s.id !== id))
      return { previous }
    },
    onError: (_err:any, _id:number, context:any) => {
      if (context?.previous) queryClient.setQueryData(SESSIONS_KEY, context.previous)
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: SESSIONS_KEY })
    }
  })

  const addSessionOptimistic = (session: Session) => {
    queryClient.setQueryData<Session[]>(SESSIONS_KEY, old => [session, ...(old ?? [])])
  }

  return {
    sessions,
    isLoading,
    deleteSession: deleteMutation.mutateAsync,
    addSessionOptimistic
  }
}