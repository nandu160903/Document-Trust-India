import { useEffect, useState } from 'react'

import { DocumentUpload } from '@/components/DocumentUpload'
import { createDocumentPreviewUrl } from '@/components/DocumentPreview'
import { MainLayout } from '@/components/layout/MainLayout'
import { ResultsDashboard } from '@/components/ResultsDashboard'
import { uploadAndAnalyzeDocument } from '@/services/uploadService'
import type { AnalysisResponse } from '@/types/analysis'

export function HomePage() {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(
    null,
  )
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploadedFileMeta, setUploadedFileMeta] = useState<{
    name: string
    type: string
  } | null>(null)

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleAnalyze = async (file: File) => {
    const objectPreview = createDocumentPreviewUrl(file)

    setPreviewUrl((current) => {
      if (current) {
        URL.revokeObjectURL(current)
      }
      return objectPreview
    })
    setUploadedFileMeta({ name: file.name, type: file.type })
    setAnalysisResult(null)

    const result = await uploadAndAnalyzeDocument(file)
    setAnalysisResult(result)
  }

  return (
    <MainLayout>
      <section className="mx-auto max-w-3xl space-y-3 text-center">
        <h1 className="font-heading text-3xl font-semibold tracking-tight sm:text-4xl">
          Verify documents with confidence
        </h1>
        <p className="text-muted-foreground sm:text-lg">
          Upload an identity document or certificate to detect tampering,
          inconsistencies, and potential fraud signals.
        </p>
      </section>

      <section className="mt-8">
        <DocumentUpload onAnalyze={handleAnalyze} />
      </section>

      {analysisResult ? (
        <ResultsDashboard
          result={analysisResult}
          localPreviewUrl={previewUrl}
          fileName={uploadedFileMeta?.name}
          mimeType={uploadedFileMeta?.type}
        />
      ) : null}
    </MainLayout>
  )
}
