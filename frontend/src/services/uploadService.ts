import { apiUrl } from '@/lib/api'
import type { AnalysisResponse } from '@/types/analysis'

export async function uploadAndAnalyzeDocument(
  file: File,
): Promise<AnalysisResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(apiUrl('/api/v1/upload'), {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    let message = `Analysis request failed (${response.status})`
    try {
      const errorBody = (await response.json()) as { detail?: string | { msg: string }[] }
      if (typeof errorBody.detail === 'string') {
        message = errorBody.detail
      } else if (Array.isArray(errorBody.detail)) {
        message = errorBody.detail.map((item) => item.msg).join(', ')
      }
    } catch {
      // Keep default message when response is not JSON.
    }
    throw new Error(message)
  }

  return response.json() as Promise<AnalysisResponse>
}
