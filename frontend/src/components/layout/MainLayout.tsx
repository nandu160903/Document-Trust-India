import type { ReactNode } from 'react'

import { Navbar } from '@/components/layout/Navbar'

type MainLayoutProps = {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div className="min-h-svh bg-linear-to-b from-muted/40 via-background to-background">
      <Navbar />
      <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6 sm:py-10 lg:px-8">
        {children}
      </main>
      <footer className="border-t py-6 text-center text-xs text-muted-foreground">
        DocumentTrust India · Secure document screening for identity verification
      </footer>
    </div>
  )
}
