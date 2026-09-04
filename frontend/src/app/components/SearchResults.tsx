import { useMemo, useState } from "react";
import {
  AlertCircle,
  AlignLeft,
  BookOpen,
  Building2,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  FileText,
  Info,
  ListChecks,
  Route,
  Tag,
} from "lucide-react";
import type { DepartmentRouting } from "@/api/search";

export interface SearchResult {
  id: string;
  tier: string;
  kind: string;
  category: string;
  documentName: string;
  civilType: string;
  department: string;
  departments: string[];
  paragraphSummary: string;
  keyActions: string[];
  originalText: string;
  guidance: string;
  note: string;
  updatedAt: string;
  relevance: number;
  tags: string[];
  evidenceLevel: string;
  sourceReference: string;
  sourcePages: number[];
  page: number | null;
  originalUrl: string | null;
  candidateCount: number | null;
  departmentRouting: DepartmentRouting[];
}

interface SearchResultsProps {
  results: SearchResult[];
  notice: string;
  relevanceNotice: string;
}

const TIER_LABELS: Record<string, string> = {
  manual_exact: "공식 매뉴얼",
  historical_case: "과거 민원 참고",
  no_match: "검색 결과 없음",
};

export function getTierLabel(tier: string) {
  return TIER_LABELS[tier] ?? tier;
}

export function SearchResults({ results, notice, relevanceNotice }: SearchResultsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("전체");

  const filters = useMemo(
    () => ["전체", ...Array.from(new Set(results.map((result) => result.tier)))],
    [results],
  );
  const effectiveFilter = filters.includes(activeFilter) ? activeFilter : "전체";
  const visibleResults = effectiveFilter === "전체"
    ? results
    : results.filter((result) => result.tier === effectiveFilter);

  if (results.length === 0) {
    return (
      <div
        className="p-8 border text-center"
        style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)" }}
      >
        <AlertCircle className="w-7 h-7 mx-auto mb-3" style={{ color: "var(--muted-foreground)" }} />
        <p style={{ color: "var(--foreground)", fontSize: "14px", lineHeight: 1.7 }}>
          {notice || "관련 문서를 찾지 못했습니다. 검색어를 바꿔 다시 시도해 주세요."}
        </p>
      </div>
    );
  }

  return (
    <div>
      {notice && (
        <div className="mb-4 p-4 flex gap-3" style={{ borderRadius: "12px", background: "#FFF7E6", color: "#7A5A28" }}>
          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <p style={{ fontSize: "13px", lineHeight: 1.7 }}>{notice}</p>
        </div>
      )}

      {relevanceNotice && (
        <div className="mb-4 px-1 flex items-start gap-2" style={{ color: "var(--muted-foreground)" }}>
          <Info className="w-3.5 h-3.5 flex-shrink-0 mt-0.5" />
          <p style={{ fontSize: "11px", lineHeight: 1.6 }}>{relevanceNotice}</p>
        </div>
      )}

      <div className="flex gap-2 mb-5 flex-wrap">
        {filters.map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className="px-4 py-2 transition-all duration-150"
            style={{
              borderRadius: "999px",
              background: effectiveFilter === filter ? "var(--brand-green)" : "var(--card)",
              color: effectiveFilter === filter ? "#fff" : "var(--muted-foreground)",
              border: `1px solid ${effectiveFilter === filter ? "var(--brand-green)" : "var(--border)"}`,
              fontSize: "13px",
              fontWeight: effectiveFilter === filter ? 600 : 400,
            }}
          >
            {filter === "전체" ? filter : getTierLabel(filter)}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {visibleResults.map((result, index) => {
          const isExpanded = expandedId === result.id;
          const relevanceLabel = `관련도 ${Math.round(result.relevance)}%`;

          return (
            <div
              key={result.id}
              className="overflow-hidden transition-all duration-200"
              style={{
                borderRadius: "18px",
                background: "var(--card)",
                border: `1px solid ${isExpanded ? "var(--brand-green)" : "var(--border)"}`,
                boxShadow: isExpanded ? "0 4px 20px rgba(0,0,0,0.09)" : "0 1px 6px rgba(0,0,0,0.05)",
              }}
            >
              <div className="px-7 py-6">
                <div className="flex items-start gap-4">
                  <div
                    className="flex-shrink-0 w-8 h-8 flex items-center justify-center mt-0.5"
                    style={{
                      borderRadius: "10px",
                      background: index === 0 ? "var(--brand-green)" : "var(--muted)",
                      color: index === 0 ? "#fff" : "var(--muted-foreground)",
                      fontSize: "13px",
                      fontWeight: 700,
                    }}
                  >
                    {index + 1}
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4 mb-5">
                      <div className="min-w-0">
                        <div className="flex items-center gap-2 mb-1.5" style={{ color: "var(--muted-foreground)" }}>
                          <FileText className="w-3.5 h-3.5 flex-shrink-0" />
                          <p style={{ fontSize: "12px" }}>{result.documentName}</p>
                          {result.category && <span style={{ fontSize: "11px" }}>· {result.category}</span>}
                        </div>
                        <h2 style={{ color: "var(--foreground)", fontSize: "19px", fontWeight: 800, lineHeight: 1.45 }}>
                          {result.civilType}
                        </h2>
                      </div>
                      <span
                        className="flex-shrink-0 px-3 py-1"
                        style={{ borderRadius: "999px", background: "var(--brand-green-light)", color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 700 }}
                      >
                        {relevanceLabel}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-4">
                      <div className="p-3.5" style={{ borderRadius: "12px", background: "var(--background)" }}>
                        <div className="flex items-center gap-1.5 mb-1.5" style={{ color: "var(--muted-foreground)" }}>
                          <Building2 className="w-3.5 h-3.5" />
                          <span style={{ fontSize: "11px", fontWeight: 700 }}>담당 부서</span>
                        </div>
                        <p style={{ color: "var(--foreground)", fontSize: "13px", fontWeight: 650, lineHeight: 1.6 }}>
                          {result.department}
                        </p>
                      </div>
                      <div className="p-3.5" style={{ borderRadius: "12px", background: "var(--background)" }}>
                        <div className="flex items-center gap-1.5 mb-1.5" style={{ color: "var(--muted-foreground)" }}>
                          <BookOpen className="w-3.5 h-3.5" />
                          <span style={{ fontSize: "11px", fontWeight: 700 }}>근거</span>
                        </div>
                        <p style={{ color: "var(--foreground)", fontSize: "12px", lineHeight: 1.6 }}>
                          {result.sourceReference || (result.page !== null ? `${result.documentName} · ${result.page}쪽` : result.documentName)}
                        </p>
                      </div>
                    </div>

                    <div className="mb-4 p-4" style={{ borderRadius: "12px", background: "var(--brand-green-light)" }}>
                      <div className="flex items-center gap-2 mb-2" style={{ color: "var(--brand-green-dark)" }}>
                        <AlignLeft className="w-4 h-4" />
                        <p style={{ fontSize: "12px", fontWeight: 800 }}>핵심 내용</p>
                      </div>
                      <p style={{ color: "var(--brand-green-dark)", fontSize: "13px", lineHeight: 1.75 }}>
                        {result.paragraphSummary || "관련 내용을 확인해 주세요."}
                      </p>
                      {result.keyActions.length > 0 && (
                        <div className="mt-3 pt-3" style={{ borderTop: "1px solid rgba(22, 101, 52, 0.14)" }}>
                          <div className="flex items-center gap-2 mb-2" style={{ color: "var(--brand-green-dark)" }}>
                            <ListChecks className="w-4 h-4" />
                            <p style={{ fontSize: "12px", fontWeight: 800 }}>핵심 대응</p>
                          </div>
                          <ul className="space-y-1.5">
                            {result.keyActions.map((action) => (
                              <li key={action} className="flex items-start gap-2" style={{ color: "var(--brand-green-dark)", fontSize: "13px", lineHeight: 1.65 }}>
                                <span aria-hidden="true" style={{ fontWeight: 800 }}>•</span>
                                <span>{action}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {result.tags.map((tag) => (
                        <span key={tag} style={{ borderRadius: "6px", background: "var(--brand-green-light)", color: "var(--brand-green-dark)", fontSize: "11px", fontWeight: 600, padding: "3px 10px" }}>
                          #{tag}
                        </span>
                      ))}
                    </div>

                    {isExpanded && (
                      <div className="space-y-3 mb-4">
                        {result.originalText && (
                          <div className="p-5" style={{ borderRadius: "12px", background: "#F7F8F7", border: "1px solid var(--border)" }}>
                            <div className="flex items-center gap-2 mb-3">
                              <BookOpen className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
                              <p style={{ color: "var(--foreground)", fontSize: "13px", fontWeight: 800 }}>상세 원문</p>
                            </div>
                            <p className="whitespace-pre-wrap" style={{ color: "var(--card-foreground)", fontSize: "12px", lineHeight: 1.85 }}>
                              {result.originalText}
                            </p>
                          </div>
                        )}
                        {result.note && (
                          <div className="p-4 flex gap-3" style={{ borderRadius: "12px", background: "#FBF9F5", borderLeft: "3px solid #C8A96E" }}>
                            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#A07840" }} />
                            <div>
                              <p style={{ color: "#7A5A28", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>참고 사항</p>
                              <p className="whitespace-pre-line" style={{ color: "#6B4F22", fontSize: "13px", lineHeight: 1.7 }}>{result.note}</p>
                            </div>
                          </div>
                        )}
                        {result.guidance && (
                          <div className="p-4 flex gap-3" style={{ borderRadius: "12px", background: "#F5F5F7", borderLeft: "3px solid #636366" }}>
                            <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#636366" }} />
                            <div>
                              <p style={{ color: "#3A3A3C", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>처리 안내</p>
                              <p className="whitespace-pre-line" style={{ color: "#3A3A3C", fontSize: "13px", lineHeight: 1.7 }}>{result.guidance}</p>
                            </div>
                          </div>
                        )}
                        {result.departmentRouting.length > 0 && (
                          <div className="p-4" style={{ borderRadius: "12px", background: "var(--background)" }}>
                            <div className="flex items-center gap-2 mb-3">
                              <Route className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
                              <p style={{ color: "var(--foreground)", fontSize: "12px", fontWeight: 700 }}>부서 배정 기준</p>
                            </div>
                            <ul className="space-y-2">
                              {result.departmentRouting.map((route) => (
                                <li key={`${route.department}-${route.condition}`} style={{ color: "var(--card-foreground)", fontSize: "12px", lineHeight: 1.6 }}>
                                  <strong>{route.department}</strong> · {route.condition} ({route.confidence})
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 px-1" style={{ color: "var(--muted-foreground)", fontSize: "11px" }}>
                          {result.sourceReference && <span>출처: {result.sourceReference}</span>}
                          {result.updatedAt && <span>기준연도: {result.updatedAt}</span>}
                          {result.candidateCount !== null && <span>참고 사례: {result.candidateCount}건</span>}
                          {result.originalUrl && (
                            <a
                              href={result.originalUrl}
                              target="_blank"
                              rel="noreferrer"
                              className="inline-flex items-center gap-1"
                              style={{ color: "var(--brand-green)", fontWeight: 600 }}
                            >
                              원문 확인 <ExternalLink className="w-3 h-3" />
                            </a>
                          )}
                        </div>
                      </div>
                    )}

                    <button
                      aria-expanded={isExpanded}
                      onClick={() => setExpandedId(isExpanded ? null : result.id)}
                      className="inline-flex items-center gap-1.5 transition-colors duration-150"
                      style={{ color: "var(--muted-foreground)", fontSize: "13px" }}
                    >
                      {isExpanded
                        ? <><ChevronUp className="w-4 h-4" />{result.originalText ? "상세 원문 닫기" : "상세 정보 닫기"}</>
                        : <><ChevronDown className="w-4 h-4" />{result.originalText ? "상세 원문 보기" : "상세 정보 보기"}</>}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
