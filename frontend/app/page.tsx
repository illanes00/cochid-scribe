'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import Script from 'next/script'
import { LogIn, PenLine } from 'lucide-react'
import { useAuth } from '@/lib/auth'

const JSON_LD = {
  '@context': 'https://schema.org',
  '@type': 'SoftwareApplication',
  name: 'Cochid · Scribe',
  url: 'https://scribe.cochid.cl/',
  applicationCategory: 'Writing Platform',
  operatingSystem: 'Web',
  offers: {
    '@type': 'Offer',
    price: '0',
    priceCurrency: 'CLP',
    availability: 'https://schema.org/InStock',
    description: 'Gratis con SSO Cochid (Authentik)',
  },
  publisher: {
    '@type': 'Organization',
    name: 'COCHID',
    url: 'https://cochid.cl/',
  },
}

export default function Home() {
  const router = useRouter()
  const { authenticated, loading, loginWithSSO } = useAuth()

  useEffect(() => {
    if (!loading && authenticated) {
      router.replace('/dashboard')
    }
  }, [authenticated, loading, router])

  // Don't flash the landing while we're checking the session, or right after
  // detecting an authenticated user (the redirect is about to fire). Still
  // render hidden h-product + JSON-LD so indieweb crawlers + schema.org
  // bots see the product metadata even on the initial SSR snapshot.
  if (loading || authenticated) {
    return (
      <div className="min-h-screen bg-bg flex items-center justify-center">
        <Script id="scribe-jsonld-loading" type="application/ld+json" strategy="beforeInteractive">
          {JSON.stringify(JSON_LD)}
        </Script>
        <article className="h-product sr-only">
          <span className="p-name">Cochid · Scribe</span>
          <span className="p-summary">Escritura colaborativa con IA · claims verificables · bibliografía APA.</span>
          <data className="p-price" value="0">Gratis con SSO Cochid</data>
          <a className="u-url" href="https://scribe.cochid.cl/">scribe.cochid.cl</a>
          <span className="p-brand">Cochid</span>
        </article>
        <div className="text-sm text-muted">Cargando...</div>
      </div>
    )
  }

  // JSON-LD content is a serialized object built from compile-time constants
  // (no user input) — safe to inject as the Script element's text child.
  const jsonLdText = JSON.stringify(JSON_LD)

  return (
    <div className="h-screen bg-bg flex items-center justify-center p-6 overflow-hidden">
      <Script id="scribe-jsonld" type="application/ld+json" strategy="beforeInteractive">
        {jsonLdText}
      </Script>
      <article className="h-product max-w-md w-full text-center">
        <div className="flex items-center justify-center gap-2 mb-4">
          <PenLine size={22} className="text-c-blue" />
          <span className="p-name text-2xl font-bold text-ink">Cochid · Scribe</span>
        </div>
        <p className="p-summary text-sm text-muted leading-relaxed mb-8">
          Escritura colaborativa con IA · claims verificables · bibliografía APA.
        </p>
        <button
          type="button"
          onClick={loginWithSSO}
          className="btn btn-primary w-full"
        >
          <LogIn size={14} className="mr-2" />
          Iniciar sesión
        </button>
        <p className="text-[11px] text-muted mt-6">
          Acceso vía Cochid SSO · Authentik
        </p>
        {/* Indieweb microformat metadata (hidden) */}
        <data className="p-price" value="0" hidden>Gratis con SSO Cochid</data>
        <a className="u-url" href="https://scribe.cochid.cl/" hidden>scribe.cochid.cl</a>
        <span className="p-brand" hidden>Cochid</span>
        <span className="p-category" hidden>Writing Platform</span>
      </article>
    </div>
  )
}
