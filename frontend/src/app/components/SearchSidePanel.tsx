import { Building2, FileText, Lightbulb, ShieldCheck } from "lucide-react";
import type { SearchResult } from "./SearchResults";

interface SearchSidePanelProps {
  results: SearchResult[];
}

const SEARCH_TIPS = [
  "민원 대상과 상황을 구체적으로 입력해 주세요",
  "공식 매뉴얼과 과거 민원 참고자료는 근거 수준이 다릅니다",
  "결과가 없으면 임의로 안내하지 말고 담당 부서에 확인해 주세요",
];

export function SearchSidePanel({ results }: SearchSidePanelProps) {
  const departments = Array.from(new Set(results.map((result) => result.department)));
  const sources = Array.from(new Set(results.map((result) => result.documentName)));
  const tiers = Array.from(new Set(results.map((result) => result.tier)));

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <Building2 className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>검색된 관련 부서</p>
        </div>
        <ul>
          {departments.map((department) => (
            <li key={department} className="px-5 py-3.5 border-b last:border-b-0" style={{ borderColor: "var(--border)" }}>
              <p style={{ color: "var(--foreground)", fontSize: "13px", fontWeight: 600 }}>{department}</p>
              <p style={{ color: "var(--muted-foreground)", fontSize: "11px", marginTop: "3px" }}>
                상세 연락처는 검색 결과 원문에서 확인
              </p>
            </li>
          ))}
        </ul>
      </div>

      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <ShieldCheck className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>근거 수준</p>
        </div>
        <div className="px-5 py-4 flex flex-wrap gap-2">
          {tiers.map((tier) => (
            <span key={tier} className="px-3 py-1.5" style={{ borderRadius: "999px", background: "var(--brand-green-light)", color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 700 }}>
              {tier}
            </span>
          ))}
        </div>
      </div>

      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <FileText className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>검색 근거 문서</p>
        </div>
        <ul>
          {sources.map((source) => (
            <li key={source} className="px-5 py-3.5 border-b last:border-b-0" style={{ borderColor: "var(--border)" }}>
              <p style={{ color: "var(--foreground)", fontSize: "12px", lineHeight: 1.6 }}>{source}</p>
            </li>
          ))}
        </ul>
      </div>

      <div className="p-5 border" style={{ borderRadius: "16px", background: "var(--brand-green-light)", borderColor: "var(--brand-green-light)" }}>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--brand-green-dark)", fontSize: "13px", fontWeight: 700 }}>검색 팁</p>
        </div>
        <ul className="space-y-2">
          {SEARCH_TIPS.map((tip) => (
            <li key={tip} className="flex items-start gap-2">
              <span style={{ color: "var(--brand-green)", fontSize: "11px", fontWeight: 700, marginTop: "2px" }}>·</span>
              <span style={{ color: "var(--brand-green-dark)", fontSize: "12px", lineHeight: 1.6 }}>{tip}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
