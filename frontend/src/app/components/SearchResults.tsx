import { useState } from "react";
import {
  FileText,
  Tag,
  Building2,
  AlignLeft,
  Info,
  AlertCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Clock,
} from "lucide-react";

export interface SearchResult {
  id: string;
  category: string;
  documentName: string;
  civilType: string;
  department: string;
  paragraphSummary: string;
  guidance: string;
  note: string;
  updatedAt: string;
  relevance: number;
  tags: string[];
}

// API 연결 전 화면 동작을 확인하기 위한 샘플 결과입니다.
const SAMPLE_RESULTS: SearchResult[] = [
  {
    id: "1",
    category: "생활 불편",
    documentName: "야간 민원 처리 지침 (2024년 개정)",
    civilType: "생활 불편 신고",
    department: "총무과",
    paragraphSummary:
      "야간 시간대(18:00~09:00)에 접수된 생활 불편 민원은 당직자가 1차 접수하여 소관 부서에 다음 날 오전 9시까지 이관한다. 긴급 사안의 경우 즉시 해당 부서장에게 유선 보고한다.",
    guidance:
      "민원인에게 접수 번호를 발급하고, 처리 예정일을 안내한 뒤 시스템에 기록한다.",
    note: "소음·악취 등 환경 관련 민원은 환경과(내선 1523)로 즉시 연계.",
    updatedAt: "2024-11-15",
    relevance: 98,
    tags: ["야간민원", "생활불편", "당직처리", "긴급대응"],
  },
  {
    id: "2",
    category: "건축·토지",
    documentName: "건축·토지 민원 안내 매뉴얼",
    civilType: "건축 허가 문의",
    department: "건축과",
    paragraphSummary:
      "건축 허가 관련 문의는 건축과 인허가팀(담당자: 이수진, 내선 2341)으로 안내한다. 야간·주말에는 민원 처리 불가 사항을 명확히 고지하고, 다음 근무일 방문을 유도한다.",
    guidance:
      "건축물 용도변경, 증·개축 관련 사항은 건축과 소관이며, 토지분할은 지적과로 안내.",
    note: "허가 처리 기간: 소규모 14일, 일반 30일, 복합민원 최대 60일.",
    updatedAt: "2024-10-22",
    relevance: 85,
    tags: ["건축허가", "인허가", "토지", "처리기간"],
  },
  {
    id: "3",
    category: "도로·교통",
    documentName: "도로·교통 시설 민원 처리 절차서",
    civilType: "도로 파손 신고",
    department: "도로과",
    paragraphSummary:
      "도로 파손·함몰 신고는 긴급 여부를 우선 확인한다. 차량 통행에 위험이 있을 경우 도로과 긴급 담당(☎ 010-XXXX-XXXX)에 즉시 연락하고, 현장 안전 조치를 요청한다.",
    guidance:
      "신고자에게 현장 위치(도로명, 인근 지형지물 포함)를 정확히 확인하고 기록한다.",
    note: "국도·지방도는 도로공사(1588-2504), 고속도로는 한국도로공사(1588-2504)로 연계.",
    updatedAt: "2024-09-08",
    relevance: 72,
    tags: ["도로파손", "긴급출동", "안전조치", "신고처리"],
  },
  {
    id: "4",
    category: "복지",
    documentName: "복지 급여 및 지원 민원 안내 지침",
    civilType: "기초생활 수급 문의",
    department: "복지과",
    paragraphSummary:
      "기초생활보장 수급자 자격 문의는 복지과 소관이나, 야간에는 즉시 처리 불가. 한국복지재단 긴급복지 지원 핫라인(☎ 129)으로 우선 연계하고, 다음 날 복지과 상담을 예약한다.",
    guidance:
      "위기 상황(노숙, 아동방임 등)은 긴급복지지원법에 따라 즉시 관련 기관 신고 의무.",
    note: "아동학대: 112 / 노인학대: 1577-1389 / 장애인: 1644-0935",
    updatedAt: "2024-12-01",
    relevance: 61,
    tags: ["기초생활", "복지수급", "긴급복지", "위기상황"],
  },
];

export function SearchResults() {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState("전체");

  const filters = ["전체", "생활 불편", "건축·토지", "도로·교통", "복지"];
  const visibleResults = activeFilter === "전체"
    ? SAMPLE_RESULTS
    : SAMPLE_RESULTS.filter((result) => result.category === activeFilter);

  return (
    <div>
      {/* Filter tabs */}
      <div className="flex gap-2 mb-5 flex-wrap">
        {filters.map((f) => (
          <button
            key={f}
            onClick={() => setActiveFilter(f)}
            className="px-4 py-2 transition-all duration-150"
            style={{
              borderRadius: "999px",
              background: activeFilter === f ? "var(--brand-green)" : "var(--card)",
              color: activeFilter === f ? "#fff" : "var(--muted-foreground)",
              border: `1px solid ${activeFilter === f ? "var(--brand-green)" : "var(--border)"}`,
              fontSize: "13px",
              fontWeight: activeFilter === f ? 600 : 400,
            }}
          >
            {f}
          </button>
        ))}
      </div>

      {/* Result cards */}
      <div className="space-y-4">
        {visibleResults.map((result, idx) => {
          const isExpanded = expandedId === result.id;
          return (
            <div
              key={result.id}
              className="overflow-hidden transition-all duration-200"
              style={{
                borderRadius: "18px",
                background: "var(--card)",
                border: `1px solid ${isExpanded ? "var(--brand-green)" : "var(--border)"}`,
                boxShadow: isExpanded
                  ? "0 4px 20px rgba(0,0,0,0.09)"
                  : "0 1px 6px rgba(0,0,0,0.05)",
              }}
            >
              <div className="px-7 py-6">
                <div className="flex items-start gap-4">
                  {/* Rank badge */}
                  <div
                    className="flex-shrink-0 w-8 h-8 flex items-center justify-center mt-0.5"
                    style={{
                      borderRadius: "10px",
                      background: idx === 0 ? "var(--brand-green)" : "var(--muted)",
                      color: idx === 0 ? "#fff" : "var(--muted-foreground)",
                      fontSize: "13px",
                      fontWeight: 700,
                    }}
                  >
                    {idx + 1}
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Title row */}
                    <div className="flex items-start justify-between gap-3 mb-3">
                      <div className="flex items-center gap-2.5 min-w-0">
                        <FileText className="w-4.5 h-4.5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                        <p style={{ color: "var(--foreground)", fontSize: "16px", fontWeight: 700, lineHeight: 1.4 }}>
                          {result.documentName}
                        </p>
                      </div>
                      <div
                        className="flex-shrink-0 px-3 py-1"
                        style={{
                          borderRadius: "999px",
                          background: idx === 0 ? "var(--brand-green-light)" : "var(--muted)",
                          color: idx === 0 ? "var(--brand-green-dark)" : "var(--muted-foreground)",
                          fontSize: "12px",
                          fontWeight: 700,
                        }}
                      >
                        관련도 {result.relevance}%
                      </div>
                    </div>

                    {/* Meta row */}
                    <div className="flex flex-wrap items-center gap-3 mb-4">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1" style={{ borderRadius: "8px", background: "var(--muted)", fontSize: "12px", color: "var(--muted-foreground)" }}>
                        <Tag className="w-3 h-3" />
                        {result.civilType}
                      </span>
                      <span className="inline-flex items-center gap-1.5 px-3 py-1" style={{ borderRadius: "8px", background: "var(--muted)", fontSize: "12px", color: "var(--muted-foreground)" }}>
                        <Building2 className="w-3 h-3" />
                        {result.department}
                      </span>
                      <span className="inline-flex items-center gap-1.5" style={{ fontSize: "12px", color: "var(--muted-foreground)" }}>
                        <Clock className="w-3 h-3" />
                        수정 {result.updatedAt}
                      </span>
                    </div>

                    {/* Summary */}
                    <div className="flex gap-3 mb-4 p-4" style={{ borderRadius: "12px", background: "var(--background)" }}>
                      <AlignLeft className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "var(--muted-foreground)", opacity: 0.5 }} />
                      <p style={{ color: "var(--card-foreground)", fontSize: "13px", lineHeight: 1.8 }}>
                        {result.paragraphSummary}
                      </p>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1.5 mb-4">
                      {result.tags.map((tag) => (
                        <span
                          key={tag}
                          style={{
                            borderRadius: "6px",
                            background: "var(--brand-green-light)",
                            color: "var(--brand-green-dark)",
                            fontSize: "11px",
                            fontWeight: 600,
                            padding: "3px 10px",
                          }}
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>

                    {/* Expanded content */}
                    {isExpanded && (
                      <div className="space-y-3 mb-4">
                        <div
                          className="p-4 flex gap-3"
                          style={{ borderRadius: "12px", background: "#F5F5F7", borderLeft: "3px solid #636366" }}
                        >
                          <Info className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#636366" }} />
                          <div>
                            <p style={{ color: "#3A3A3C", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>처리 안내</p>
                            <p style={{ color: "#3A3A3C", fontSize: "13px", lineHeight: 1.7 }}>{result.guidance}</p>
                          </div>
                        </div>
                        <div
                          className="p-4 flex gap-3"
                          style={{ borderRadius: "12px", background: "#FBF9F5", borderLeft: "3px solid #C8A96E" }}
                        >
                          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" style={{ color: "#A07840" }} />
                          <div>
                            <p style={{ color: "#7A5A28", fontSize: "12px", fontWeight: 700, marginBottom: "4px" }}>참고 사항</p>
                            <p style={{ color: "#6B4F22", fontSize: "13px", lineHeight: 1.7 }}>{result.note}</p>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Action row */}
                    <div className="flex items-center justify-between">
                      <button
                        onClick={() => setExpandedId(isExpanded ? null : result.id)}
                        className="inline-flex items-center gap-1.5 transition-colors duration-150"
                        style={{ color: "var(--muted-foreground)", fontSize: "13px" }}
                      >
                        {isExpanded ? (
                          <><ChevronUp className="w-4 h-4" />접기</>
                        ) : (
                          <><ChevronDown className="w-4 h-4" />처리 안내 · 참고사항 보기</>
                        )}
                      </button>
                      <button
                        className="inline-flex items-center gap-2 px-5 py-2.5 transition-all duration-150"
                        style={{
                          borderRadius: "10px",
                          background: "var(--brand-green)",
                          color: "#fff",
                          fontSize: "13px",
                          fontWeight: 600,
                        }}
                      >
                        <ExternalLink className="w-3.5 h-3.5" />
                        원문 확인
                      </button>
                    </div>
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
