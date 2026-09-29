import { FileText } from 'lucide-react'

import { cn } from '@/lib/utils'

type DocumentPreviewProps = {
  src: string
  alt: string
  fileName?: string
  mimeType?: string
  className?: string
  frameClassName?: string
}

function isPdfDocument(
  src: string,
  mimeType?: string,
  fileName?: string,
): boolean {
  if (mimeType === 'application/pdf') {
    return true
  }
  if (fileName?.toLowerCase().endsWith('.pdf')) {
    return true
  }
  return src.toLowerCase().includes('.pdf')
}

export function DocumentPreview({
  src,
  alt,
  fileName,
  mimeType,
  className,
  frameClassName,
}: DocumentPreviewProps) {
  const isPdf = isPdfDocument(src, mimeType, fileName)

  if (isPdf) {
    return (
      <div
        className={cn(
          'overflow-hidden rounded-lg border bg-background',
          className,
        )}
      >
        <iframe
          src={`${src}#view=FitH&toolbar=0&navpanes=0`}
          title={alt}
          className={cn('h-72 w-full bg-white', frameClassName)}
        />
        <div className="flex items-center gap-2 border-t bg-muted/20 px-3 py-2 text-left text-xs text-muted-foreground">
          <FileText className="size-3.5 shrink-0" />
          PDF preview · first page glimpse
        </div>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className={cn(
        'mx-auto max-h-72 w-full rounded-lg border object-contain bg-background',
        className,
        frameClassName,
      )}
    />
  )
}

export function createDocumentPreviewUrl(file: File): string | null {
  if (file.type.startsWith('image/') || file.type === 'application/pdf') {
    return URL.createObjectURL(file)
  }

  const extension = file.name.slice(file.name.lastIndexOf('.')).toLowerCase()
  if (['.jpg', '.jpeg', '.png', '.pdf'].includes(extension)) {
    return URL.createObjectURL(file)
  }

  return null
}

export function getDocumentPreviewType(file: File): 'image' | 'pdf' | null {
  if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')) {
    return 'pdf'
  }
  if (file.type.startsWith('image/')) {
    return 'image'
  }
  return null
}
