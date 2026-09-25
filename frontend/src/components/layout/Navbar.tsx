import { ShieldCheck } from 'lucide-react'

import { Badge } from '@/components/ui/badge'

export function Navbar() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-3">
          <div className="flex size-10 items-center justify-center rounded-xl bg-primary text-primary-foreground shadow-sm">
            <ShieldCheck className="size-5" aria-hidden="true" />
          </div>
          <div className="text-left">
            <p className="font-heading text-base font-semibold tracking-tight sm:text-lg">
              DocumentTrust India
            </p>
            <p className="hidden text-xs text-muted-foreground sm:block">
              AI Document & Identity Screening
            </p>
          </div>
        </div>

        <Badge variant="secondary" className="hidden sm:inline-flex">
          Phase 3 · Screening UI
        </Badge>
      </div>
    </header>
  )
}
