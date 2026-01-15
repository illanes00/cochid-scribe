'use client'

import Link from 'next/link'
import { FileText, Database, Network, Sparkles } from 'lucide-react'

export default function Home() {
  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <div className="flex items-center gap-2">
            <span className="text-2xl font-bold text-ink">Scribe</span>
            <span className="text-muted">|</span>
            <span className="text-sm text-muted">Academic Writing Platform</span>
          </div>
          <Link href="/dashboard" className="btn btn-primary">
            Open Dashboard
          </Link>
        </div>
      </header>

      {/* Hero */}
      <section className="py-16 border-b border-line">
        <div className="container-narrow text-center">
          <h1 className="text-4xl font-black mb-6">
            Write with Evidence
          </h1>
          <p className="text-lg text-muted mb-8">
            Academic writing platform that helps you organize claims,
            verify evidence, and produce publication-ready documents.
          </p>
          <div className="flex gap-4 justify-center">
            <Link href="/dashboard" className="btn btn-primary">
              Get Started
            </Link>
            <Link href="/dashboard" className="btn">
              View Demo
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16">
        <div className="container">
          <h2 className="text-2xl font-bold text-center mb-12">Features</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              icon={<FileText size={24} />}
              title="Rich Editor"
              description="Google Docs-like editing with real-time collaboration and auto-save"
            />
            <FeatureCard
              icon={<Sparkles size={24} />}
              title="AI Assistant"
              description="Claude-powered rewriting, hedging improvement, and citation suggestions"
            />
            <FeatureCard
              icon={<Database size={24} />}
              title="Claim System"
              description="Track and verify every claim with linked evidence"
            />
            <FeatureCard
              icon={<Network size={24} />}
              title="Knowledge Graph"
              description="Obsidian-like linking between notes, ideas, and bibliography"
            />
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-line">
        <div className="container text-center text-sm text-muted">
          <p>Scribe - Built with illanes v3 Design System</p>
        </div>
      </footer>
    </div>
  )
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode
  title: string
  description: string
}) {
  return (
    <div className="card">
      <div className="text-c-blue mb-4">{icon}</div>
      <h3 className="font-bold mb-2">{title}</h3>
      <p className="text-sm text-muted">{description}</p>
    </div>
  )
}
