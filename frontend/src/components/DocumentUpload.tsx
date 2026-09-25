import { useCallback, useEffect, useRef, useState, type DragEvent } from 'react'
import {
  AlertCircle,
  FileText,
  ImageIcon,
  Loader2,
  ScanSearch,
  UploadCloud,
  X,
} from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import {
  ACCEPT_ATTRIBUTE,
  isAllowedFile,
} from '@/lib/constants'
import { cn } from '@/lib/utils'

type DocumentUploadProps = {
  onAnalyze?: (file: File) => Promise<void>
}

export function DocumentUpload({ onAnalyze }: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [isDragActive, setIsDragActive] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisProgress, setAnalysisProgress] = useState(0)

  const resetSelection = useCallback(() => {
    setSelectedFile(null)
    setPreviewUrl(null)
    setError(null)
    setAnalysisProgress(0)
    if (inputRef.current) {
      inputRef.current.value = ''
    }
  }, [])

  const handleFileSelection = useCallback((file: File | undefined) => {
    if (!file) {
      return
    }

    if (!isAllowedFile(file)) {
      setError('Only JPEG, PNG, and PDF files are supported.')
      setSelectedFile(null)
      setPreviewUrl(null)
      return
    }

    setError(null)
    setSelectedFile(file)

    if (file.type.startsWith('image/')) {
      const objectUrl = URL.createObjectURL(file)
      setPreviewUrl(objectUrl)
      return
    }

    setPreviewUrl(null)
  }, [])

  useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl)
      }
    }
  }, [previewUrl])

  const handleAnalyze = async () => {
    if (!selectedFile || isAnalyzing) {
      return
    }

    setIsAnalyzing(true)
    setAnalysisProgress(8)
    setError(null)

    const progressTimer = window.setInterval(() => {
      setAnalysisProgress((current) => {
        if (current >= 92) {
          return current
        }
        return current + Math.random() * 12
      })
    }, 350)

    try {
      if (onAnalyze) {
        await onAnalyze(selectedFile)
      } else {
        await new Promise((resolve) => window.setTimeout(resolve, 2200))
      }
      setAnalysisProgress(100)
    } catch {
      setError('Analysis failed. Please try again.')
      setAnalysisProgress(0)
    } finally {
      window.clearInterval(progressTimer)
      setIsAnalyzing(false)
    }
  }

  const onDrop = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setIsDragActive(false)
    handleFileSelection(event.dataTransfer.files?.[0])
  }

  return (
    <Card className="mx-auto w-full max-w-3xl shadow-sm">
      <CardHeader>
        <CardTitle className="text-xl sm:text-2xl">
          Upload Document for Screening
        </CardTitle>
        <CardDescription>
          Drag and drop an identity document or certificate. Supported formats:
          JPEG, PNG, and PDF.
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-4">
        {error ? (
          <Alert variant="destructive">
            <AlertCircle />
            <AlertTitle>Upload error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}

        <div
          role="button"
          tabIndex={0}
          aria-label="Document upload drop zone"
          onClick={() => inputRef.current?.click()}
          onKeyDown={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              event.preventDefault()
              inputRef.current?.click()
            }
          }}
          onDragOver={(event) => {
            event.preventDefault()
            setIsDragActive(true)
          }}
          onDragLeave={(event) => {
            event.preventDefault()
            setIsDragActive(false)
          }}
          onDrop={onDrop}
          className={cn(
            'relative flex min-h-56 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors',
            isDragActive
              ? 'border-primary bg-primary/5'
              : 'border-muted-foreground/30 hover:border-primary/50 hover:bg-muted/30',
            isAnalyzing && 'pointer-events-none opacity-70',
          )}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPT_ATTRIBUTE}
            className="hidden"
            onChange={(event) =>
              handleFileSelection(event.target.files?.[0])
            }
          />

          <div className="mb-4 flex size-14 items-center justify-center rounded-full bg-primary/10 text-primary">
            <UploadCloud className="size-7" aria-hidden="true" />
          </div>
          <p className="font-medium">
            {isDragActive
              ? 'Drop your document here'
              : 'Drag & drop your document here'}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">
            or click to browse files
          </p>
          <p className="mt-3 text-xs text-muted-foreground">
            Max recommended size: 10 MB · JPG, PNG, PDF
          </p>
        </div>

        {selectedFile ? (
          <div className="rounded-xl border bg-muted/20 p-4">
            <div className="mb-3 flex items-start justify-between gap-3">
              <div className="min-w-0 text-left">
                <p className="truncate font-medium">{selectedFile.name}</p>
                <p className="text-sm text-muted-foreground">
                  {(selectedFile.size / 1024 / 1024).toFixed(2)} MB ·{' '}
                  {selectedFile.type || 'Unknown type'}
                </p>
              </div>
              <Button
                type="button"
                variant="ghost"
                size="icon-sm"
                aria-label="Remove selected file"
                disabled={isAnalyzing}
                onClick={(event) => {
                  event.stopPropagation()
                  resetSelection()
                }}
              >
                <X className="size-4" />
              </Button>
            </div>

            {previewUrl ? (
              <img
                src={previewUrl}
                alt={`Preview of ${selectedFile.name}`}
                className="mx-auto max-h-72 w-full rounded-lg border object-contain bg-background"
              />
            ) : (
              <div className="flex min-h-40 flex-col items-center justify-center rounded-lg border border-dashed bg-background px-4 py-8 text-muted-foreground">
                <FileText className="mb-2 size-10" aria-hidden="true" />
                <p className="font-medium text-foreground">PDF preview</p>
                <p className="text-sm">
                  PDF documents will be analyzed directly by the backend.
                </p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex items-center gap-2 rounded-lg border border-dashed px-4 py-3 text-sm text-muted-foreground">
            <ImageIcon className="size-4 shrink-0" aria-hidden="true" />
            Selected document preview will appear here after upload.
          </div>
        )}

        {isAnalyzing ? (
          <div className="space-y-3 rounded-xl border bg-muted/20 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <Loader2 className="size-4 animate-spin text-primary" />
              Analyzing document with AI screening models…
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="text-muted-foreground">Processing</span>
                <span className="font-medium tabular-nums">
                  {Math.round(analysisProgress)}%
                </span>
              </div>
              <div
                className="h-2 w-full overflow-hidden rounded-full bg-muted"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={Math.round(analysisProgress)}
                aria-label="Document analysis progress"
              >
                <div
                  className="h-full rounded-full bg-primary transition-all duration-300 ease-out"
                  style={{ width: `${Math.min(analysisProgress, 100)}%` }}
                />
              </div>
            </div>
          </div>
        ) : null}
      </CardContent>

      <CardFooter className="flex flex-col gap-3 sm:flex-row sm:justify-end">
        <Button
          type="button"
          variant="outline"
          disabled={!selectedFile || isAnalyzing}
          onClick={resetSelection}
        >
          Clear
        </Button>
        <Button
          type="button"
          size="lg"
          disabled={!selectedFile || isAnalyzing}
          onClick={handleAnalyze}
          className="min-w-48 bg-linear-to-r from-emerald-600 to-teal-600 text-white shadow-md hover:from-emerald-700 hover:to-teal-700"
        >
          {isAnalyzing ? (
            <>
              <Loader2 className="animate-spin" />
              Analyzing…
            </>
          ) : (
            <>
              <ScanSearch />
              Analyze Document
            </>
          )}
        </Button>
      </CardFooter>
    </Card>
  )
}
