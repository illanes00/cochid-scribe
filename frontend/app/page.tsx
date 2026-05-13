"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import {
  FileText,
  Database,
  Network,
  Sparkles,
  Shield,
  Clock,
  BookOpen,
  Presentation,
  ArrowRight,
  Plus,
  Cloud,
  MessageSquare,
  GraduationCap,
  Landmark,
  PenLine,
} from "lucide-react";
import { Document, documentsApi } from "@/lib/api";

export default function Home() {
  const [recentDocs, setRecentDocs] = useState<Document[]>([]);
  const [totalDocs, setTotalDocs] = useState(0);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    documentsApi
      .list(1, 6)
      .then((result) => {
        setRecentDocs(result.documents);
        setTotalDocs(result.total);
        setLoaded(true);
      })
      .catch(() => {
        setLoaded(true);
      });
  }, []);

  const totalClaims = recentDocs.reduce((s, d) => s + (d.claim_count || 0), 0);
  const totalVerified = recentDocs.reduce(
    (s, d) => s + (d.verified_count || 0),
    0,
  );

  const TYPE_ICONS: Record<string, typeof FileText> = {
    paper: FileText,
    thesis: GraduationCap,
    policy: Landmark,
    presentation: Presentation,
  };

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <div className="flex items-center gap-3">
            <span className="text-xl font-bold text-ink">Scribe</span>
            <span className="text-line">|</span>
            <span className="text-sm text-muted">
              Academic Writing Platform
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link
              href="/privacy"
              className="text-sm text-muted hover:text-ink hover:underline"
            >
              Privacidad
            </Link>
            <Link
              href="/terms"
              className="text-sm text-muted hover:text-ink hover:underline"
            >
              Términos
            </Link>
            <Link href="/dashboard" className="btn btn-primary">
              Open Dashboard
            </Link>
          </div>
        </div>
      </header>

      {/* Hero */}
      <section className="py-20 border-b border-line">
        <div className="container-narrow text-center">
          <h1 className="text-4xl font-black mb-4 leading-tight">
            Write with evidence.
            <br />
            Publish with confidence.
          </h1>
          <p className="text-lg text-muted mb-8 max-w-xl mx-auto">
            An academic writing platform that helps you track claims, verify
            evidence, manage bibliography, and produce publication-ready
            documents.
          </p>
          <div className="flex gap-3 justify-center">
            <Link href="/dashboard" className="btn btn-primary">
              <Plus size={16} className="mr-2" />
              New Document
            </Link>
            <Link href="/dashboard" className="btn">
              <FileText size={16} className="mr-2" />
              View Documents
            </Link>
          </div>
        </div>
      </section>

      {/* Quick stats + recent docs */}
      {loaded && totalDocs > 0 && (
        <section className="py-12 border-b border-line">
          <div className="container">
            {/* Stats strip */}
            <div className="grid grid-cols-3 gap-4 mb-10 max-w-xl mx-auto">
              <StatBox
                label="Documents"
                value={String(totalDocs)}
                icon={<FileText size={16} />}
              />
              <StatBox
                label="Claims"
                value={String(totalClaims)}
                icon={<Shield size={16} />}
              />
              <StatBox
                label="Verified"
                value={
                  totalClaims > 0
                    ? `${Math.round((totalVerified / totalClaims) * 100)}%`
                    : "--"
                }
                icon={<Shield size={16} />}
              />
            </div>

            {/* Recent documents */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-bold">Recent Documents</h2>
              <Link
                href="/dashboard"
                className="text-sm text-c-blue flex items-center gap-1 hover:underline"
              >
                View all
                <ArrowRight size={14} />
              </Link>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recentDocs.slice(0, 6).map((doc) => {
                const Icon = TYPE_ICONS[doc.doc_type] || FileText;
                const updatedDate = new Date(doc.updated_at).toLocaleDateString(
                  "en-US",
                  {
                    month: "short",
                    day: "numeric",
                  },
                );
                return (
                  <Link key={doc.slug} href={`/editor/${doc.slug}`}>
                    <div className="card group hover:border-line-strong transition-colors">
                      <div className="flex items-start gap-2.5">
                        <Icon
                          size={16}
                          className="text-muted mt-0.5 flex-shrink-0"
                        />
                        <div className="min-w-0 flex-1">
                          <h3 className="font-semibold text-sm truncate group-hover:text-c-blue transition-colors">
                            {doc.title}
                          </h3>
                          <div className="flex items-center gap-3 mt-1.5 text-xs text-muted">
                            <span className="capitalize">{doc.status}</span>
                            <span className="flex items-center gap-1">
                              <Clock size={10} />
                              {updatedDate}
                            </span>
                            {doc.claim_count > 0 && (
                              <span>
                                {doc.verified_count}/{doc.claim_count} claims
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  </Link>
                );
              })}
            </div>
          </div>
        </section>
      )}

      {/* Features */}
      <section className="py-16">
        <div className="container">
          <h2 className="text-2xl font-bold text-center mb-3">
            Built for rigorous writing
          </h2>
          <p className="text-muted text-center mb-12 max-w-lg mx-auto">
            Every feature is designed to help policy researchers and academics
            produce work that stands up to scrutiny.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <FeatureCard
              icon={<PenLine size={22} />}
              title="Rich Editor"
              description="Full-featured document editor with real-time auto-save, keyboard shortcuts, and slash commands."
            />
            <FeatureCard
              icon={<Shield size={22} />}
              title="Claim Verification"
              description="Mark verifiable assertions, link them to evidence, and track verification status across your document."
            />
            <FeatureCard
              icon={<Sparkles size={22} />}
              title="AI Assistant"
              description="Claude-powered rewriting, hedging improvement, claim extraction, and citation suggestions."
            />
            <FeatureCard
              icon={<BookOpen size={22} />}
              title="Bibliography"
              description="BibTeX import, citation insertion, and automatic reference list generation."
            />
            <FeatureCard
              icon={<Network size={22} />}
              title="Knowledge Graph"
              description="Obsidian-style linking between notes, documents, claims, and bibliography entries."
            />
            <FeatureCard
              icon={<Cloud size={22} />}
              title="Google Sync"
              description="Two-way sync with Google Docs and Slides. Push, pull, and resolve conflicts."
            />
            <FeatureCard
              icon={<MessageSquare size={22} />}
              title="Comments & Review"
              description="Inline comments, threaded replies, and AI-assisted review response workflows."
            />
            <FeatureCard
              icon={<Database size={22} />}
              title="Data & Charts"
              description="Upload datasets, create charts, and embed visualizations directly in your documents."
            />
          </div>
        </div>
      </section>

      {/* Quick actions */}
      <section className="py-12 border-t border-line bg-paper">
        <div className="container text-center">
          <h2 className="text-xl font-bold mb-2">Ready to start?</h2>
          <p className="text-muted mb-6">
            Choose a document type and begin writing immediately.
          </p>
          <div className="flex items-center justify-center gap-3 flex-wrap">
            <Link href="/dashboard" className="btn btn-primary">
              <FileText size={16} className="mr-2" />
              New Paper
            </Link>
            <Link href="/dashboard" className="btn">
              <Landmark size={16} className="mr-2" />
              Policy Brief
            </Link>
            <Link href="/dashboard" className="btn">
              <GraduationCap size={16} className="mr-2" />
              Thesis
            </Link>
            <Link href="/dashboard" className="btn">
              <Presentation size={16} className="mr-2" />
              Presentation
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 border-t border-line">
        <div className="container text-center text-sm text-muted space-y-3">
          <p>Scribe — Plataforma de escritura académica · illanes00</p>
          <nav className="flex items-center justify-center gap-4 text-xs">
            <Link href="/privacy" className="hover:text-ink hover:underline">
              Política de Privacidad
            </Link>
            <span className="opacity-40">·</span>
            <Link href="/terms" className="hover:text-ink hover:underline">
              Condiciones del Servicio
            </Link>
            <span className="opacity-40">·</span>
            <a
              href="mailto:martinillanesv@gmail.com"
              className="hover:text-ink hover:underline"
            >
              Contacto
            </a>
          </nav>
        </div>
      </footer>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Components                                                         */
/* ------------------------------------------------------------------ */

function StatBox({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="card text-center py-4">
      <div className="text-muted mb-1 flex items-center justify-center">
        {icon}
      </div>
      <div className="text-2xl font-bold">{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </div>
  );
}

function FeatureCard({
  icon,
  title,
  description,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
}) {
  return (
    <div className="card">
      <div className="text-c-blue mb-3">{icon}</div>
      <h3 className="font-bold mb-1.5">{title}</h3>
      <p className="text-sm text-muted leading-relaxed">{description}</p>
    </div>
  );
}
