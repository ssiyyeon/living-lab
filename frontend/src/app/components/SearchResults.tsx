import { useMemo, useState } from "react";
import {
  AlertCircle,
  AlignLeft,
  Building2,
  ChevronDown,
  ChevronUp,
  FileText,
  Info,
  MapPin,
  Phone,
  Tag,
} from "lucide-react";

export interface SearchResult {
  id: string;
  tier: string;
  documentName: string;
  civilType: string;
  department: string;
  paragraphSummary: string;
  note: string;
  contact: string;
  page: string;
  relevance: number | null;
  tags: string[];
}

interface SearchResultsProps {
  results: SearchResult[];
  notice: string;
}

export function SearchResults({ results, notice }: SearchResultsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("전체");

  const filters = useMemo(
    () => ["전체", ...Array.from(new Set(results.map((result) => result.tier)))],
    [results],
  );
  const visibleResults = activeFilter === "전체"
    ? results
    : results.filter((result) => result.tier === activeFilter);

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

      <div className="flex gap-2 mb-5 flex-wrap">
        {filters.map((filter) => (
          <button
            key={filter}
            onClick={() => setActiveFilter(filter)}
            className="px-4 py-2 transition-all duration-150"
            style={{
              borderRadius: "999px",
              background: activeFilter === filter ? "var(--brand-green)" : "var(--card)",
              color: activeFilter === filter ? "#fff" : "var(--muted-foreground)",
              border: `1px solid ${activeFilter === filter ? "var(--brand-green)" : "var(--border)"}`,
              fontSize: "13px",
              fontWeight: activeFilter === filter ? 600 : 400,
            }}
          >
            {filter}
          </button>
        ))}
      </div>

      <div className="space-y-4">
        {visibleResults.map((result, index) => {
          const isExpanded = expandedId === result.id;
          const relevanceLabel = result.relevance === null
            ? "키워드 일치"
            : `관련도 ${Math.round(result.relevance * 100)}%`;

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
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className="w-4 h-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                        <p style={{ color: "var(--foreground)", fontSize: "16px", fontWeight: 700, lineHeight: 1.4 }}>
                          {result.documentName}
                        </p>
                      </div>
                      <span
                        className="flex-shrink-0 px-3 py-1"
                        style={{ borderRadius: "999px", background: "var(--brand-green-light)", color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 700 }}
                      >
                        {relevanceLabel}
                      </span>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 mb-4">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1" style={{ borderRadius: "8px", background: "var(--muted)", fontSize: "12px", color: "var(--muted-foreground)" }}>
                        <Tag className="w-3 h-3" />
                        {result.civilType}
                      </span>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1" style={{ borderRadius: "8px", background: "var(--muted)", fontSize: "12px", color: "var(--muted-foreground)" }}>
                        <Building2 className="w-3 h-3" />
                        {result.department}
                      </span>
                      {result.page && (
                        <span className="inline-flex items-center gap-1.5" style={{ fontSize: "12px", color: "var(--muted-foreground)" }}>
                          <MapPin className="w-3 h-3" />
                          {result.page}쪽
                        </span>
                      )}
                    </div>

                    <div className="flex gap-3 mb-4 p-4" style={{ borderRadius: "12px", background: "var(--background)" }}>
                      <AlignLeft className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "var(--muted-foreground)", opacity: 0.5 }} />
                      <p className="whitespace-pre-line" style={{ color: "var(--card-foreground)", fontSize: "13px", lineHeight: 1.8 }}>
                        {result.paragraphSummary || "관련 문단 정보가 없습니다."}
                      </p>
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
                        {result.note && (
                          <div className="p-4 flex gap-3" style={{ borderRadius: "12px", background: "#FBF9F5", borderLeft: "3px solid #C8A96E" }}>
                            <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#A07840" }} />
                            <div>
                              <p style={{ color: "#7A5A28", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>참고 사항</p>
                              <p className="whitespace-pre-line" style={{ color: "#6B4F22", fontSize: "13px", lineHeight: 1.7 }}>{result.note}</p>
                            </div>
                          </div>
                        )}
                        {result.contact && (
                          <div className="p-4 flex gap-3" style={{ borderRadius: "12px", background: "#F5F5F7", borderLeft: "3px solid #636366" }}>
                            <Phone className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#636366" }} />
                            <div>
                              <p style={{ color: "#3A3A3C", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>담당자 연락처</p>
                              <p className="whitespace-pre-line" style={{ color: "#3A3A3C", fontSize: "13px", lineHeight: 1.7 }}>{result.contact}</p>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    <button
                      onClick={() => setExpandedId(isExpanded ? null : result.id)}
                      className="inline-flex items-center gap-1.5 transition-colors duration-150"
                      style={{ color: "var(--muted-foreground)", fontSize: "13px" }}
                    >
                      {isExpanded ? <><ChevronUp className="w-4 h-4" />접기</> : <><ChevronDown className="w-4 h-4" />참고사항 보기</>}
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
