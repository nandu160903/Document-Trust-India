import { DocumentUpload } from '@/components/DocumentUpload'
import { MainLayout } from '@/components/layout/MainLayout'

export function HomePage() {
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
        <DocumentUpload />
      </section>
    </MainLayout>
  )
}
