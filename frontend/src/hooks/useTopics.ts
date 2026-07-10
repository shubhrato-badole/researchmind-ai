import { useQuery } from '@tanstack/react-query'
import client from '../Api/client'

export function useTopics(documentIds: number[]) {
  const { data: topics = [], isLoading } = useQuery({
    queryKey: ['topics', documentIds],
    queryFn: async () => {
      const res = await client.get('/features/topics', {
        params: { document_ids: documentIds.join(',') }
      })
      return res.data.topics as string[]
    },
    enabled: documentIds.length > 0
  })
  return { topics, isLoading }
}