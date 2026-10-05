import { useEffect, useMemo, useState, type ReactNode } from "react";
import {
  AlertTriangle,
  BookOpen,
  ChevronDown,
  CircleCheck,
  ExternalLink,
  FileText,
  Pencil,
  Search,
  X,
} from "lucide-react";
import { getManualPdfUrl, type ManualCatalogEntry, type ManualCatalogResponse } from "../api/search";
import { ManualPdfPager, ManualPdfPages } from "./ManualPdfViewer";

const GROUP_ORDER = [
  "당직근무자 준수사항",
  "청사 보안·시건",
  "비상 발령·소집",
  "재난유형별 대응",
  "민원유형별 대응",
  "부록",
];

const BRANCH_SECTION_PREFIX = "[구분] ";

function branchSectionTitle(action: string) {
  return action.startsWith(BRANCH_SECTION_PREFIX)
    ? action.slice(BRANCH_SECTION_PREFIX.length)
    : null;
}

function formatPages(pages: number[]) {
  if (pages.length === 0) return "쪽수 확인 필요";
  if (pages.length === 1) return `${pages[0]}쪽`;
  return `${Math.min(...pages)}-${Math.max(...pages)}쪽`;
}

function entryFieldChanged(entry: ManualCatalogEntry, field: string) {
  return entry.changedFields?.includes(field) ?? false;
}

function UpdateBadge({ added = false }: { added?: boolean }) {
  return (
    <span
      className="inline-flex flex-shrink-0 rounded-full px-2 py-0.5 text-[11px] font-bold"
      style={{
        background: added ? "#EAF3FF" : "#FFF1D6",
        color: added ? "#155A9C" : "#8A5600",
      }}
    >
      {added ? "추가됨" : "수정됨"}
    </span>
  );
}

function ChangeHighlight({ changed, children }: { changed: boolean; children: ReactNode }) {
  return (
    <div
      className={changed ? "rounded-xl border px-4 py-3" : ""}
      style={changed ? { background: "#FFF9EC", borderColor: "#E9B45B" } : undefined}
    >
      {changed && <div className="mb-2"><UpdateBadge /></div>}
      {children}
    </div>
  );
}

function StructuredCaseContent({ entry }: { entry: ManualCatalogEntry }) {
  return (
    <div className="space-y-6">
      {entry.departments.length > 0 && (
        <ChangeHighlight changed={entryFieldChanged(entry, "departments")}>
          <section>
            <h3 className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>담당 부서</h3>
            <p className="mt-2 text-sm font-semibold">{entry.departments.join(" · ")}</p>
          </section>
        </ChangeHighlight>
      )}

      {(entry.intakeQuestions.length > 0 || entry.immediateActions.length > 0) && (
        <div className="grid gap-6 sm:grid-cols-2">
          {entry.intakeQuestions.length > 0 && (
            <ChangeHighlight changed={entryFieldChanged(entry, "intakeQuestions")}>
              <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
                <h3 className="text-sm font-bold">먼저 확인</h3>
                <ol className="mt-3 space-y-2 text-sm leading-6">
                  {entry.intakeQuestions.map((question, index) => (
                    <li key={question} className="flex gap-2.5">
                      <span className="font-bold" style={{ color: "var(--brand-green)" }}>{index + 1}.</span>
                      <span>{question}</span>
                    </li>
                  ))}
                </ol>
              </section>
            </ChangeHighlight>
          )}

          {entry.immediateActions.length > 0 && (
            <ChangeHighlight changed={entryFieldChanged(entry, "immediateActions")}>
              <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
                <h3 className="text-sm font-bold">즉시 조치</h3>
                <ul className="mt-3 space-y-2 text-sm leading-6">
                  {entry.immediateActions.map((action) => (
                    <li key={action} className="flex gap-2.5">
                      <CircleCheck className="mt-1 h-4 w-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                      <span>{action}</span>
                    </li>
                  ))}
                </ul>
              </section>
            </ChangeHighlight>
          )}
        </div>
      )}

      {entry.decisionBranches.length > 0 && (
        <ChangeHighlight changed={entryFieldChanged(entry, "decisionBranches")}>
          <section>
            <h3 className="text-sm font-bold">상황별 처리</h3>
            <div className="mt-3 divide-y border-y" style={{ borderColor: "var(--border)" }}>
              {entry.decisionBranches.map((branch) => (
                <div key={branch.condition} className="py-4" style={{ borderColor: "var(--border)" }}>
                  <p className="text-sm font-bold" style={{ color: "var(--brand-green-dark)" }}>{branch.condition}</p>
                  <ul className="mt-2 space-y-1.5 text-sm leading-6">
                    {branch.actions.map((action) => {
                      const sectionTitle = branchSectionTitle(action);
                      return sectionTitle ? (
                        <li key={action} className="pt-3 first:pt-0 font-extrabold" style={{ color: "var(--brand-green-dark)" }}>
                          {sectionTitle}
                        </li>
                      ) : <li key={action}>• {action}</li>;
                    })}
                  </ul>
                  {branch.response && (
                    <p className="mt-3 border-l-2 pl-3 text-sm leading-6" style={{ borderColor: "var(--brand-green)", color: "var(--muted-foreground)" }}>
                      안내 문구 · {branch.response}
                    </p>
                  )}
                </div>
              ))}
            </div>
          </section>
        </ChangeHighlight>
      )}

      {entry.escalationRules.length > 0 && (
        <ChangeHighlight changed={entryFieldChanged(entry, "escalationRules")}>
          <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
            <h3 className="text-sm font-bold">보고·상향 기준</h3>
            <ul className="mt-3 space-y-3 text-sm leading-6">
              {entry.escalationRules.map((rule) => (
                <li key={`${rule.condition}-${rule.action}`}>
                  <strong>{rule.condition}</strong>
                  <span className="mt-1 block" style={{ color: "var(--muted-foreground)" }}>{rule.action}</span>
                </li>
              ))}
            </ul>
          </section>
        </ChangeHighlight>
      )}

      {entry.responseScripts.length > 0 && (
        <ChangeHighlight changed={entryFieldChanged(entry, "responseScripts")}>
          <section>
            <h3 className="text-sm font-bold">민원인 안내 문구</h3>
            <div className="mt-3 space-y-3">
              {entry.responseScripts.map((script) => (
                <p
                  key={script}
                  className="border-l-2 pl-4 text-sm leading-6"
                  style={{ borderColor: "var(--brand-green)", color: "var(--muted-foreground)" }}
                >
                  {script}
                </p>
              ))}
            </div>
          </section>
        </ChangeHighlight>
      )}

      {entry.cautions.length > 0 && (
        <ChangeHighlight changed={entryFieldChanged(entry, "cautions")}>
          <section className="border-l-2 pl-4" style={{ borderColor: "var(--brand-red)" }}>
            <h3 className="flex items-center gap-2 text-sm font-bold" style={{ color: "var(--brand-red-dark)" }}>
              <AlertTriangle className="h-4 w-4" />
              주의사항
            </h3>
            <ul className="mt-2 space-y-1.5 text-sm leading-6">
              {entry.cautions.map((caution) => <li key={caution}>• {caution}</li>)}
            </ul>
          </section>
        </ChangeHighlight>
      )}
    </div>
  );
}

export function ManualCatalogView({
  catalog,
  requestedEntryId,
  canEdit = false,
  onEditEntry,
}: {
  catalog: ManualCatalogResponse;
  requestedEntryId?: string;
  canEdit?: boolean;
  onEditEntry?: (entryId: string) => void;
}) {
  const requestedEntry = catalog.entries.find((entry) => entry.id === requestedEntryId);
  const [activeGroup, setActiveGroup] = useState(requestedEntry?.group ?? "전체");
  const [query, setQuery] = useState("");
  const [pdfPage, setPdfPage] = useState<number | null>(null);
  const [openEntryId, setOpenEntryId] = useState<string | null>(requestedEntryId ?? null);

  useEffect(() => {
    if (!requestedEntryId) return;
    const entry = catalog.entries.find((item) => item.id === requestedEntryId);
    if (!entry) return;
    setActiveGroup(entry.group);
    setQuery("");
    setOpenEntryId(entry.id);
    window.requestAnimationFrame(() => {
      document.getElementById(`manual-entry-${requestedEntryId}`)?.scrollIntoView({ behavior: "smooth", block: "center" });
    });
  }, [catalog.entries, requestedEntryId]);

  useEffect(() => {
    if (pdfPage === null) return;
    const previousOverflow = document.body.style.overflow;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") setPdfPage(null);
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleEscape);
    };
  }, [pdfPage]);

  const groupCounts = useMemo(() => {
    const counts = new Map<string, number>();
    catalog.entries.forEach((entry) => counts.set(entry.group, (counts.get(entry.group) ?? 0) + 1));
    return counts;
  }, [catalog.entries]);

  const filteredEntries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return catalog.entries.filter((entry) => {
      if (activeGroup !== "전체" && entry.group !== activeGroup) return false;
      if (!normalizedQuery) return true;

      return [
        entry.title,
        entry.topic,
        entry.summary,
        entry.content,
        entry.breadcrumb.join(" "),
        entry.departments.join(" "),
      ].some((value) => value.toLowerCase().includes(normalizedQuery));
    });
  }, [activeGroup, catalog.entries, query]);

  const visibleGroups = GROUP_ORDER.filter((group) =>
    filteredEntries.some((entry) => entry.group === group),
  );

  return (
    <article>
      <header className="border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold" style={{ color: "var(--brand-green)" }}>공식 매뉴얼 전체보기</p>
            <h1 className="mt-2 text-2xl font-extrabold">전체 매뉴얼</h1>
            <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
              PDF 85쪽에서 정리한 일반 문서 40개와 상황별 대응 31개를 확인합니다.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="text-sm font-bold" style={{ color: "var(--brand-green-dark)" }}>{catalog.totalCount}개 문서</span>
            <button
              type="button"
              onClick={() => setPdfPage(1)}
              className="inline-flex items-center gap-2 rounded-full border bg-white px-4 py-2 text-sm font-bold"
              style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
            >
              <FileText className="h-4 w-4" />
              PDF 전체 보기
            </button>
          </div>
        </div>

        <div className="mt-5 flex items-center gap-3 rounded-full border bg-white px-4" style={{ borderColor: "var(--border)" }}>
          <Search className="h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="매뉴얼 제목, 담당 부서 또는 내용 검색"
            aria-label="전체 매뉴얼 검색"
            className="min-w-0 flex-1 bg-transparent py-3 text-sm outline-none"
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
          {["전체", ...GROUP_ORDER].map((group) => {
            const count = group === "전체" ? catalog.totalCount : (groupCounts.get(group) ?? 0);
            if (group !== "전체" && count === 0) return null;

            return (
              <button
                key={group}
                type="button"
                onClick={() => setActiveGroup(group)}
                className="border-b-2 py-1 text-xs font-bold transition-colors"
                style={{
                  borderColor: activeGroup === group ? "var(--brand-green)" : "transparent",
                  color: activeGroup === group ? "var(--brand-green-dark)" : "var(--muted-foreground)",
                }}
              >
                {group} {count}
              </button>
            );
          })}
        </div>
      </header>

      {visibleGroups.length === 0 ? (
        <p className="py-16 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>
          일치하는 매뉴얼 항목이 없습니다.
        </p>
      ) : (
        <div className="mt-8 space-y-10">
          {visibleGroups.map((group) => {
            const entries = filteredEntries.filter((entry) => entry.group === group);

            return (
              <section key={group}>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-base font-extrabold">{group}</h2>
                  <span className="text-xs" style={{ color: "var(--muted-foreground)" }}>{entries.length}개</span>
                </div>

                <div className="divide-y border-y" style={{ borderColor: "var(--border)" }}>
                  {entries.map((entry) => {
                    const isOpen = openEntryId === entry.id;
                    return (
                    <div
                      key={entry.id}
                      id={`manual-entry-${entry.id}`}
                      style={{ background: entry.isCustom ? "#F5F9FF" : undefined }}
                    >
                      <button
                        type="button"
                        aria-expanded={isOpen}
                        onClick={() => setOpenEntryId((current) => current === entry.id ? null : entry.id)}
                        className="flex w-full items-center gap-4 py-4 text-left"
                      >
                        <BookOpen className="h-4.5 w-4.5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                        <span className="min-w-0 flex-1">
                          <span className="flex flex-wrap items-center gap-2">
                            <strong
                              className={`block text-sm ${entryFieldChanged(entry, "title") ? "rounded px-1.5 py-0.5" : ""}`}
                              style={entryFieldChanged(entry, "title") ? { background: "#FFF1D6" } : undefined}
                            >
                              {entry.title}
                            </strong>
                            {entry.isCustom ? <UpdateBadge added /> : entry.isModified ? <UpdateBadge /> : null}
                          </span>
                          <span
                            className={`mt-1 block text-xs ${entryFieldChanged(entry, "topic") ? "rounded px-1.5 py-0.5" : ""}`}
                            style={{
                              color: "var(--muted-foreground)",
                              background: entryFieldChanged(entry, "topic") ? "#FFF9EC" : undefined,
                            }}
                          >
                            {entry.topic} · {formatPages(entry.sourcePages)}
                          </span>
                        </span>
                        <ChevronDown className={`h-4 w-4 flex-shrink-0 transition-transform ${isOpen ? "rotate-180" : ""}`} style={{ color: "var(--muted-foreground)" }} />
                      </button>

                      {isOpen && (
                        <div className="pb-6 pl-8 sm:pl-9">
                          <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                            <span className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>
                              {entry.sourcePages.length > 0 ? `공식 PDF ${formatPages(entry.sourcePages)}` : "관리자 추가 내용"}
                            </span>
                            {canEdit && onEditEntry && (
                              <button
                                type="button"
                                onClick={() => onEditEntry(entry.id)}
                                className="inline-flex items-center gap-1.5 rounded-full border bg-white px-3 py-2 text-xs font-bold"
                                style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
                              >
                                <Pencil className="h-3.5 w-3.5" /> 수정
                              </button>
                            )}
                          </div>
                          {entry.sourcePages.length > 0 ? (
                            <ManualPdfPages pages={entry.sourcePages} />
                          ) : (
                            <div className="whitespace-pre-line rounded-xl border bg-white p-5 text-sm leading-7" style={{ borderColor: "var(--border)" }}>
                              {entry.content || entry.summary || "등록된 내용이 없습니다."}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                    );
                  })}
                </div>
              </section>
            );
          })}
        </div>
      )}

      <footer className="mt-10 border-t pt-4 text-xs leading-5" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
        {catalog.source} · 표지와 목차를 제외한 전체 실무 페이지를 분류해 표시합니다.
      </footer>

      {pdfPage !== null && (
        <div className="fixed inset-0 z-50 flex justify-end" role="dialog" aria-modal="true" aria-label={`공식 매뉴얼 PDF ${pdfPage}쪽`}>
          <button
            type="button"
            aria-label="PDF 닫기"
            className="absolute inset-0"
            onClick={() => setPdfPage(null)}
            style={{ background: "rgba(17, 24, 39, 0.48)", backdropFilter: "blur(2px)" }}
          />
          <section className="relative flex h-full w-full max-w-[920px] flex-col bg-white">
            <header className="flex items-center justify-between gap-3 border-b px-4 py-3 sm:px-5" style={{ borderColor: "var(--border)" }}>
              <div className="min-w-0">
                <h2 className="truncate text-base font-extrabold">공식 매뉴얼 원문</h2>
                <p className="mt-0.5 text-xs" style={{ color: "var(--muted-foreground)" }}>PDF {pdfPage}쪽부터 표시합니다.</p>
              </div>
              <div className="flex items-center gap-2">
                <a
                  href={getManualPdfUrl(pdfPage)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-xl border px-3 py-2 text-xs font-bold"
                  style={{ borderColor: "var(--border)", color: "var(--brand-green-dark)" }}
                >
                  <ExternalLink className="h-4 w-4" />
                  새 탭
                </a>
                <button type="button" onClick={() => setPdfPage(null)} aria-label="PDF 닫기" className="rounded-xl border p-2" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
                  <X className="h-5 w-5" />
                </button>
              </div>
            </header>
            <ManualPdfPager initialPage={pdfPage} />
          </section>
        </div>
      )}
    </article>
  );
}
