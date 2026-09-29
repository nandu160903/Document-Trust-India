import { AlertTriangle, CheckCircle2, ShieldAlert } from 'lucide-react'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { apiUrl } from '@/lib/api'
import { cn } from '@/lib/utils'
import { DocumentPreview } from '@/components/DocumentPreview'
import type { AnalysisResponse } from '@/types/analysis'

type ResultsDashboardProps = {
  result: AnalysisResponse
  localPreviewUrl?: string | null
  fileName?: string
  mimeType?: string
}

const RISK_STYLES: Record<string, string> = {
  LOW: 'bg-emerald-100 text-emerald-800 border-emerald-300 dark:bg-emerald-950 dark:text-emerald-200',
  MEDIUM: 'bg-amber-100 text-amber-900 border-amber-300 dark:bg-amber-950 dark:text-amber-200',
  HIGH: 'bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-200',
}

export function ResultsDashboard({
  result,
  localPreviewUrl,
  fileName,
  mimeType,
}: ResultsDashboardProps) {
  const riskLevel = result.risk_level.toUpperCase()
  const originalSrc =
    localPreviewUrl ?? apiUrl(result.original_image_url)
  const heatmapSrc = apiUrl(result.heatmap_image_url)
  const resolvedFileName =
    fileName ?? result.original_image_url.split('/').pop() ?? 'document'
  const resolvedMimeType =
    mimeType ??
    (resolvedFileName.toLowerCase().endsWith('.pdf')
      ? 'application/pdf'
      : 'image/jpeg')

  return (
    <Card className="mx-auto mt-8 w-full max-w-5xl shadow-sm">
      <CardHeader>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="text-left">
            <CardTitle className="text-xl sm:text-2xl">
              Screening Results
            </CardTitle>
            <CardDescription>
              Forensic analysis completed by DocumentTrust India engine
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              className={cn(
                'px-3 py-1 text-sm font-semibold',
                RISK_STYLES[riskLevel] ?? RISK_STYLES.MEDIUM,
              )}
            >
              {riskLevel} RISK
            </Badge>
            <div className="rounded-lg border px-4 py-2 text-left">
              <p className="text-xs text-muted-foreground">Risk Score</p>
              <p className="text-2xl font-bold tabular-nums">
                {result.risk_score}
                <span className="text-sm font-normal text-muted-foreground">
                  /100
                </span>
              </p>
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <Alert>
          {riskLevel === 'HIGH' ? (
            <ShieldAlert />
          ) : riskLevel === 'MEDIUM' ? (
            <AlertTriangle />
          ) : (
            <CheckCircle2 />
          )}
          <AlertTitle>Analysis summary</AlertTitle>
          <AlertDescription>
            Anomaly confidence: {(result.anomaly_score * 100).toFixed(1)}% ·
            Inference: {result.inference_method}
          </AlertDescription>
        </Alert>

        <div>
          <h3 className="mb-3 text-left text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Diagnostic reasons
          </h3>
          <ul className="space-y-2 text-left">
            {result.reasons.map((reason) => (
              <li
                key={reason}
                className="rounded-lg border bg-muted/20 px-4 py-3 text-sm"
              >
                {reason}
              </li>
            ))}
          </ul>
        </div>

        <div>
          <h3 className="mb-3 text-left text-sm font-semibold uppercase tracking-wide text-muted-foreground">
            Visual evidence
          </h3>
          <div className="grid gap-4 md:grid-cols-2">
            <div className="overflow-hidden rounded-xl border">
              <p className="border-b bg-muted/30 px-4 py-2 text-left text-sm font-medium">
                Original document
              </p>
              <DocumentPreview
                src={originalSrc}
                alt="Original uploaded document"
                fileName={resolvedFileName}
                mimeType={resolvedMimeType}
                frameClassName="max-h-96"
              />
            </div>
            <div className="overflow-hidden rounded-xl border">
              <p className="border-b bg-muted/30 px-4 py-2 text-left text-sm font-medium">
                ELA heatmap (tamper regions)
              </p>
              <img
                src={heatmapSrc}
                alt="ELA heatmap highlighting anomalies"
                className="max-h-96 w-full bg-background object-contain p-2"
              />
            </div>
          </div>
        </div>

        {Object.keys(result.extracted_fields).length > 0 ? (
          <div>
            <h3 className="mb-3 text-left text-sm font-semibold uppercase tracking-wide text-muted-foreground">
              Extracted fields
            </h3>
            <div className="grid gap-2 sm:grid-cols-2">
              {Object.entries(result.extracted_fields).map(([key, value]) => (
                <div
                  key={key}
                  className="rounded-lg border px-4 py-3 text-left text-sm"
                >
                  <p className="text-xs text-muted-foreground">{key}</p>
                  <p className="font-medium">{String(value)}</p>
                </div>
              ))}
            </div>
          </div>
        ) : null}
      </CardContent>
    </Card>
  )
}
