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

function ScoreMeter({
  label,
  value,
  helper,
  barClassName,
}: {
  label: string
  value: number
  helper: string
  barClassName: string
}) {
  return (
    <div className="rounded-xl border bg-muted/10 p-4 text-left">
      <div className="mb-2 flex items-center justify-between gap-3">
        <div>
          <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
            {label}
          </p>
          <p className="text-3xl font-bold tabular-nums">{value}%</p>
        </div>
      </div>
      <div
        className="mb-2 h-2.5 w-full overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={value}
        aria-label={label}
      >
        <div
          className={cn('h-full rounded-full transition-all', barClassName)}
          style={{ width: `${value}%` }}
        />
      </div>
      <p className="text-xs text-muted-foreground">{helper}</p>
    </div>
  )
}

export function ResultsDashboard({
  result,
  localPreviewUrl,
  fileName,
  mimeType,
}: ResultsDashboardProps) {
  const riskLevel = result.risk_level.toUpperCase()
  const authenticityPercentage =
    result.authenticity_percentage ??
    Math.round(result.authenticity_score * 100)
  const riskPercentage =
    result.risk_percentage ?? result.risk_score ?? 0

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
              Authenticity and risk are reported separately for clarity
            </CardDescription>
          </div>
          <Badge
            className={cn(
              'self-start px-3 py-1 text-sm font-semibold sm:self-auto',
              RISK_STYLES[riskLevel] ?? RISK_STYLES.MEDIUM,
            )}
          >
            {riskLevel} RISK VERDICT
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        <div className="grid gap-4 md:grid-cols-2">
          <ScoreMeter
            label="Authenticity"
            value={authenticityPercentage}
            helper="Higher means the document appears more genuine and consistent."
            barClassName="bg-emerald-500"
          />
          <ScoreMeter
            label="Risk"
            value={riskPercentage}
            helper="Higher means stronger tampering or fraud indicators were detected."
            barClassName="bg-red-500"
          />
        </div>

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
            Authenticity {authenticityPercentage}% · Risk {riskPercentage}% ·
            Inference engine: {result.inference_method}
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
