"use client";

import { useState, useEffect, useCallback } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import {
  Plus,
  FileText,
  Presentation,
  Clock,
  Search,
  Filter,
  Trash2,
  RefreshCw,
  Cloud,
  BookOpen,
  Database,
  Settings,
  X,
  ChevronDown,
  MessageSquare,
  CheckCircle2,
  AlertCircle,
  PenLine,
  Eye,
  Shield,
  GraduationCap,
  Landmark,
  Upload,
} from "lucide-react";
import { Document, documentsApi } from "@/lib/api";
import { templates } from "@/lib/templates";

type DocTypeFilter = "all" | "paper" | "thesis" | "policy" | "presentation";
type StatusFilter = "all" | "draft" | "review" | "final";

const TYPE_ICONS: Record<string, typeof FileText> = {
  paper: FileText,
  thesis: GraduationCap,
  policy: Landmark,
  presentation: Presentation,
};

const TYPE_LABELS: Record<string, string> = {
  paper: "Paper",
  thesis: "Thesis",
  policy: "Policy Brief",
  presentation: "Presentation",
};

const TYPE_PILL_CLASSES: Record<string, string> = {
  paper: "pill-info",
  thesis: "bg-c-purple/10 text-c-purple border-transparent",
  policy: "bg-c-amber/10 text-c-amber border-transparent",
  presentation: "bg-c-green/10 text-c-green border-transparent",
};

const STATUS_CONFIG: Record<
  string,
  { label: string; dotClass: string; color: string }
> = {
  draft: { label: "Draft", dotClass: "bg-muted", color: "text-muted" },
  review: {
    label: "In Review",
    dotClass: "bg-c-amber",
    color: "text-c-amber",
  },
  final: {
    label: "Final",
    dotClass: "bg-c-green",
    color: "text-c-green",
  },
};

export default function Dashboard() {
  const router = useRouter();
  const pathname = usePathname();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [typeFilter, setTypeFilter] = useState<DocTypeFilter>("all");
  const [statusFilter, setStatusFilter] = useState<StatusFilter>("all");
  const [filterMenuOpen, setFilterMenuOpen] = useState(false);
  const [statusMenuOpen, setStatusMenuOpen] = useState(false);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [importing, setImporting] = useState(false);
  const [newDocMenuOpen, setNewDocMenuOpen] = useState(false);
  const perPage = 20;

  const loadDocuments = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await documentsApi.list(page, perPage);
      setDocuments(result.documents);
      setTotal(result.total);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [page, perPage]);

  useEffect(() => {
    loadDocuments();
  }, [loadDocuments]);

  async function handleDelete(slug: string, e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();

    if (!confirm("Delete this document? This cannot be undone.")) return;

    try {
      await documentsApi.delete(slug);
      setDocuments((prev) => prev.filter((d) => d.slug !== slug));
      setTotal((prev) => prev - 1);
    } catch {
      alert("Failed to delete document");
    }
  }

  async function handleCreate(
    docType: "paper" | "thesis" | "policy" | "presentation",
  ) {
    try {
      const doc = await documentsApi.create({
        title: "Untitled Document",
        doc_type: docType,
      });
      router.push(`/editor/${doc.slug}`);
    } catch {
      alert("Failed to create document");
    }
  }

  async function handleCreateFromTemplate(templateId: string) {
    const template = templates.find((t) => t.id === templateId);
    if (!template) return;
    try {
      const doc = await documentsApi.create({
        title: template.title,
        doc_type: template.doc_type,
        markdown: template.markdown,
      });
      router.push(`/editor/${doc.slug}`);
    } catch {
      alert("Failed to create document from template");
    }
  }

  async function handleImport(file: File) {
    try {
      setImporting(true);
      const doc = await documentsApi.import(file);
      router.push(`/editor/${doc.slug}`);
    } catch {
      alert("Failed to import document");
    } finally {
      setImporting(false);
    }
  }

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.title
      .toLowerCase()
      .includes(searchQuery.toLowerCase());
    const matchesType = typeFilter === "all" || doc.doc_type === typeFilter;
    const matchesStatus = statusFilter === "all" || doc.status === statusFilter;
    return matchesSearch && matchesType && matchesStatus;
  });

  const hasActiveFilters =
    typeFilter !== "all" || statusFilter !== "all" || searchQuery !== "";

  // Counts for filter badges
  const typeCounts = documents.reduce(
    (acc, doc) => {
      acc[doc.doc_type] = (acc[doc.doc_type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const statusCounts = documents.reduce(
    (acc, doc) => {
      acc[doc.status] = (acc[doc.status] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );

  const navLinks = [
    { href: "/dashboard", label: "Documents", icon: FileText },
    { href: "/knowledge", label: "Knowledge", icon: BookOpen },
    { href: "/data", label: "Data", icon: Database },
    { href: "/integrations", label: "Integrations", icon: Settings },
  ];

  return (
    <div className="min-h-screen bg-bg">
      {/* Header */}
      <header className="border-b border-line bg-paper">
        <div className="container flex items-center justify-between py-4">
          <Link href="/" className="flex items-center gap-2">
            <span className="text-xl font-bold text-ink">Scribe</span>
          </Link>
          <nav className="flex items-center gap-1">
            {navLinks.map(({ href, label, icon: Icon }) => {
              const isActive = pathname === href;
              return (
                <Link
                  key={href}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 py-1.5 text-sm transition-colors ${
                    isActive
                      ? "bg-bg text-ink font-medium"
                      : "text-muted hover:text-ink hover:bg-bg/50"
                  }`}
                >
                  <Icon size={14} />
                  {label}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main */}
      <main className="container py-8">
        {/* Page header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold mb-1">Documents</h1>
            <p className="text-sm text-muted">
              {total} document{total !== 1 ? "s" : ""}
              {hasActiveFilters && ` — ${filteredDocs.length} shown`}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={loadDocuments}
              className="btn btn-sm"
              disabled={loading}
              title="Refresh"
            >
              <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            </button>
            <label className="btn btn-sm cursor-pointer" title="Import file">
              <input
                type="file"
                accept=".md,.markdown,.docx,.pptx"
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    handleImport(file);
                    e.currentTarget.value = "";
                  }
                }}
              />
              <Upload size={14} className="mr-1.5" />
              {importing ? "Importing..." : "Import"}
            </label>

            {/* New Document dropdown */}
            <div className="relative">
              <button
                onClick={() => setNewDocMenuOpen((v) => !v)}
                className="btn btn-primary"
              >
                <Plus size={16} className="mr-1.5" />
                New Document
                <ChevronDown size={14} className="ml-1.5" />
              </button>
              {newDocMenuOpen && (
                <div className="absolute right-0 mt-1 w-72 bg-paper border border-line z-20">
                  <div className="px-3 py-2 border-b border-line">
                    <span className="text-xs font-semibold text-muted uppercase tracking-wide">
                      Blank document
                    </span>
                  </div>
                  {(["paper", "thesis", "policy", "presentation"] as const).map(
                    (type) => {
                      const Icon = TYPE_ICONS[type];
                      return (
                        <button
                          key={type}
                          className="w-full text-left px-3 py-2.5 text-sm hover:bg-bg flex items-center gap-3"
                          onClick={() => {
                            setNewDocMenuOpen(false);
                            handleCreate(type);
                          }}
                        >
                          <Icon
                            size={16}
                            className="text-muted flex-shrink-0"
                          />
                          <div>
                            <div className="font-medium text-ink">
                              {TYPE_LABELS[type]}
                            </div>
                          </div>
                        </button>
                      );
                    },
                  )}
                  {templates.length > 0 && (
                    <>
                      <div className="px-3 py-2 border-t border-b border-line">
                        <span className="text-xs font-semibold text-muted uppercase tracking-wide">
                          From template
                        </span>
                      </div>
                      {templates.map((template) => (
                        <button
                          key={template.id}
                          className="w-full text-left px-3 py-2.5 text-sm hover:bg-bg"
                          onClick={() => {
                            setNewDocMenuOpen(false);
                            handleCreateFromTemplate(template.id);
                          }}
                        >
                          <div className="font-medium text-ink">
                            {template.title}
                          </div>
                          <div className="text-xs text-muted">
                            {template.description}
                          </div>
                        </button>
                      ))}
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Search & Filters */}
        <div className="flex gap-3 mb-6">
          {/* Search */}
          <div className="flex-1 relative">
            <Search
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-muted"
            />
            <input
              type="text"
              placeholder="Search documents..."
              className="input pl-10"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-muted hover:text-ink"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Type filter */}
          <div className="relative">
            <button
              onClick={() => {
                setFilterMenuOpen((v) => !v);
                setStatusMenuOpen(false);
              }}
              className={`btn flex items-center gap-2 ${typeFilter !== "all" ? "border-c-blue text-c-blue" : ""}`}
            >
              <Filter size={14} />
              {typeFilter === "all"
                ? "Type"
                : TYPE_LABELS[typeFilter] || typeFilter}
              <ChevronDown size={12} />
            </button>
            {filterMenuOpen && (
              <div className="absolute right-0 mt-1 w-52 bg-paper border border-line z-10">
                {(
                  [
                    "all",
                    "paper",
                    "thesis",
                    "policy",
                    "presentation",
                  ] as DocTypeFilter[]
                ).map((type) => (
                  <button
                    key={type}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-bg flex items-center justify-between ${
                      typeFilter === type ? "bg-bg font-medium" : ""
                    }`}
                    onClick={() => {
                      setTypeFilter(type);
                      setFilterMenuOpen(false);
                    }}
                  >
                    <span>
                      {type === "all" ? "All Types" : TYPE_LABELS[type]}
                    </span>
                    {type !== "all" && (
                      <span className="text-xs text-muted">
                        {typeCounts[type] || 0}
                      </span>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Status filter */}
          <div className="relative">
            <button
              onClick={() => {
                setStatusMenuOpen((v) => !v);
                setFilterMenuOpen(false);
              }}
              className={`btn flex items-center gap-2 ${statusFilter !== "all" ? "border-c-blue text-c-blue" : ""}`}
            >
              {statusFilter === "all" ? (
                <Eye size={14} />
              ) : (
                <span
                  className={`w-2 h-2 ${STATUS_CONFIG[statusFilter]?.dotClass}`}
                />
              )}
              {statusFilter === "all"
                ? "Status"
                : STATUS_CONFIG[statusFilter]?.label}
              <ChevronDown size={12} />
            </button>
            {statusMenuOpen && (
              <div className="absolute right-0 mt-1 w-48 bg-paper border border-line z-10">
                {(["all", "draft", "review", "final"] as StatusFilter[]).map(
                  (status) => (
                    <button
                      key={status}
                      className={`w-full text-left px-3 py-2 text-sm hover:bg-bg flex items-center justify-between ${
                        statusFilter === status ? "bg-bg font-medium" : ""
                      }`}
                      onClick={() => {
                        setStatusFilter(status);
                        setStatusMenuOpen(false);
                      }}
                    >
                      <span className="flex items-center gap-2">
                        {status !== "all" && (
                          <span
                            className={`w-2 h-2 ${STATUS_CONFIG[status]?.dotClass}`}
                          />
                        )}
                        {status === "all"
                          ? "All Statuses"
                          : STATUS_CONFIG[status]?.label}
                      </span>
                      {status !== "all" && (
                        <span className="text-xs text-muted">
                          {statusCounts[status] || 0}
                        </span>
                      )}
                    </button>
                  ),
                )}
              </div>
            )}
          </div>

          {/* Clear filters */}
          {hasActiveFilters && (
            <button
              onClick={() => {
                setSearchQuery("");
                setTypeFilter("all");
                setStatusFilter("all");
              }}
              className="btn btn-sm text-muted hover:text-ink"
            >
              <X size={14} className="mr-1" />
              Clear
            </button>
          )}
        </div>

        {/* Error state */}
        {error && (
          <div className="card bg-c-red/10 text-c-red mb-6 flex items-center justify-between">
            <span>{error}</span>
            <button onClick={loadDocuments} className="text-sm underline">
              Retry
            </button>
          </div>
        )}

        {/* Loading state */}
        {loading && documents.length === 0 && (
          <div className="py-16 text-center">
            <RefreshCw
              size={24}
              className="mx-auto mb-4 text-muted animate-spin"
            />
            <p className="text-muted">Loading documents...</p>
          </div>
        )}

        {/* Document cards grid */}
        {!loading && (
          <>
            {filteredDocs.length > 0 && (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {filteredDocs.map((doc) => (
                  <DocumentCard
                    key={doc.slug}
                    document={doc}
                    onDelete={(e) => handleDelete(doc.slug, e)}
                  />
                ))}
              </div>
            )}

            {/* Empty state */}
            {filteredDocs.length === 0 && (
              <div className="border border-line bg-paper text-center py-20 px-8">
                {hasActiveFilters ? (
                  <>
                    <Search size={40} className="mx-auto mb-4 text-muted" />
                    <h3 className="font-bold text-lg mb-2">
                      No documents match your filters
                    </h3>
                    <p className="text-muted mb-6 max-w-md mx-auto">
                      {searchQuery
                        ? `No results for "${searchQuery}"`
                        : "Try adjusting your filter criteria"}
                      {typeFilter !== "all" &&
                        ` in ${TYPE_LABELS[typeFilter]?.toLowerCase() || typeFilter}`}
                      {statusFilter !== "all" &&
                        ` with status "${STATUS_CONFIG[statusFilter]?.label}"`}
                    </p>
                    <button
                      onClick={() => {
                        setSearchQuery("");
                        setTypeFilter("all");
                        setStatusFilter("all");
                      }}
                      className="btn"
                    >
                      Clear all filters
                    </button>
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 mx-auto mb-6 border-2 border-line flex items-center justify-center">
                      <PenLine size={28} className="text-muted" />
                    </div>
                    <h3 className="font-bold text-xl mb-2">Start writing</h3>
                    <p className="text-muted max-w-lg mx-auto mb-8">
                      Create academic papers, policy briefs, and presentations
                      with built-in claim verification, bibliography management,
                      and AI assistance.
                    </p>
                    <div className="flex items-center justify-center gap-3 flex-wrap">
                      <button
                        onClick={() => handleCreate("paper")}
                        className="btn btn-primary"
                      >
                        <FileText size={16} className="mr-2" />
                        New Paper
                      </button>
                      <button
                        onClick={() => handleCreate("policy")}
                        className="btn"
                      >
                        <Landmark size={16} className="mr-2" />
                        Policy Brief
                      </button>
                      <button
                        onClick={() => handleCreate("presentation")}
                        className="btn"
                      >
                        <Presentation size={16} className="mr-2" />
                        Presentation
                      </button>
                    </div>
                    {templates.length > 0 && (
                      <div className="mt-6 pt-6 border-t border-line">
                        <p className="text-xs text-muted uppercase tracking-wide mb-3 font-semibold">
                          Or start from a template
                        </p>
                        <div className="flex items-center justify-center gap-2 flex-wrap">
                          {templates.map((t) => (
                            <button
                              key={t.id}
                              onClick={() => handleCreateFromTemplate(t.id)}
                              className="btn btn-sm"
                            >
                              {t.title}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </>
        )}

        {/* Pagination */}
        {total > perPage && (
          <div className="flex items-center justify-center gap-2 mt-8">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="btn btn-sm"
            >
              Previous
            </button>
            <span className="text-sm text-muted">
              Page {page} of {Math.ceil(total / perPage)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page >= Math.ceil(total / perPage)}
              className="btn btn-sm"
            >
              Next
            </button>
          </div>
        )}
      </main>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Document Card                                                      */
/* ------------------------------------------------------------------ */

function DocumentCard({
  document,
  onDelete,
}: {
  document: Document;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const updatedDate = new Date(document.updated_at).toLocaleDateString(
    "en-US",
    {
      month: "short",
      day: "numeric",
      year: "numeric",
    },
  );

  const claimCount = document.claim_count || 0;
  const verifiedCount = document.verified_count || 0;
  const verifiedPercent =
    claimCount > 0 ? Math.round((verifiedCount / claimCount) * 100) : 0;

  const isLinkedToGoogle =
    document.source_provider === "google_docs" ||
    document.source_provider === "google_slides";

  const TypeIcon = TYPE_ICONS[document.doc_type] || FileText;
  const statusCfg = STATUS_CONFIG[document.status] || STATUS_CONFIG.draft;

  return (
    <Link href={`/editor/${document.slug}`} className="block group">
      <div className="card h-full flex flex-col hover:border-line-strong transition-colors">
        {/* Card top: type badge + status + google icon */}
        <div className="flex items-center justify-between mb-3">
          <span
            className={`pill text-xs ${TYPE_PILL_CLASSES[document.doc_type] || "pill-info"}`}
          >
            {TYPE_LABELS[document.doc_type] || document.doc_type}
          </span>
          <div className="flex items-center gap-2">
            {isLinkedToGoogle && (
              <span title="Synced with Google" className="text-c-blue">
                <Cloud size={14} />
              </span>
            )}
            <span className="flex items-center gap-1.5 text-xs">
              <span className={`w-2 h-2 inline-block ${statusCfg.dotClass}`} />
              <span className={statusCfg.color}>{statusCfg.label}</span>
            </span>
          </div>
        </div>

        {/* Title */}
        <div className="flex items-start gap-2.5 mb-3 flex-1">
          <TypeIcon size={18} className="text-muted mt-0.5 flex-shrink-0" />
          <h3 className="font-semibold leading-snug line-clamp-2 group-hover:text-c-blue transition-colors">
            {document.title}
          </h3>
        </div>

        {/* Stats row */}
        <div className="flex items-center gap-4 text-xs text-muted mt-auto pt-3 border-t border-line">
          {/* Last updated */}
          <span className="flex items-center gap-1">
            <Clock size={12} />
            {updatedDate}
          </span>

          {/* Claims */}
          {claimCount > 0 && (
            <span
              className="flex items-center gap-1"
              title={`${verifiedCount} of ${claimCount} claims verified (${verifiedPercent}%)`}
            >
              <Shield size={12} />
              <span>
                {verifiedCount}/{claimCount}
              </span>
              {verifiedPercent === 100 && (
                <CheckCircle2 size={10} className="text-c-green" />
              )}
              {verifiedPercent > 0 && verifiedPercent < 100 && (
                <AlertCircle size={10} className="text-c-amber" />
              )}
            </span>
          )}

          {/* Spacer + delete */}
          <span className="flex-1" />
          <button
            className="p-1 text-muted hover:text-c-red opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={onDelete}
            title="Delete document"
          >
            <Trash2 size={14} />
          </button>
        </div>
      </div>
    </Link>
  );
}
