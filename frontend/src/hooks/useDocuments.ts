import { useQuery } from '@tanstack/react-query'
import client from '../Api/client'

export interface DocumentItem {
  id: number
  title: string
}

export function useDocuments() {
  const { data: documents = [], isLoading } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await client.get('/ingest/')
      return res.data.documents as DocumentItem[]
    }
  })
  return { documents, isLoading }
}