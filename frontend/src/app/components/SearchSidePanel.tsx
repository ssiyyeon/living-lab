import { FileText, Building2, Clock, Lightbulb, Star } from "lucide-react";

// 검색 API 연결 전 레이아웃 확인을 위한 샘플 데이터입니다.
const RECENT_DOCS = [
  "야간 민원 처리 지침 (2024 개정)",
  "비상 연락망 최신본",
  "불법 주정차 단속 안내",
];

const FREQUENT_DOCS = [
  { label: "당직 매뉴얼 전문", dept: "총무과" },
  { label: "민원 접수 양식 v3", dept: "민원과" },
  { label: "긴급 복지 지원 절차", dept: "복지과" },
  { label: "도로 파손 신고서", dept: "도로과" },
];

const RELATED_DEPTS = [
  { name: "총무과", ext: "1001", role: "야간 총괄" },
  { name: "민원과", ext: "1120", role: "민원 접수" },
  { name: "도로과", ext: "2210", role: "도로·교통" },
  { name: "복지과", ext: "3310", role: "복지 급여" },
  { name: "환경과", ext: "2523", role: "환경·위생" },
];

const SEARCH_TIPS = [
  "부서명을 함께 입력하면 정확도가 높아집니다",
  "민원 유형 키워드로 검색하면 빠른 결과를 얻을 수 있습니다",
  "긴급 사안은 '긴급' 키워드를 추가해 보세요",
];

export function SearchSidePanel() {
  return (
    <div className="flex flex-col gap-4">

      {/* 관련 부서 */}
      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <Building2 className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>관련 부서 연락처</p>
        </div>
        <ul>
          {RELATED_DEPTS.map((dept) => (
            <li key={dept.name} className="flex items-center justify-between px-5 py-3 border-b last:border-b-0" style={{ borderColor: "var(--border)" }}>
              <div>
                <p style={{ color: "var(--foreground)", fontSize: "13px", fontWeight: 600 }}>{dept.name}</p>
                <p style={{ color: "var(--muted-foreground)", fontSize: "11px" }}>{dept.role}</p>
              </div>
              <span
                className="px-2.5 py-1"
                style={{ borderRadius: "8px", background: "var(--brand-green-light)", color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 600, fontFamily: "var(--font-mono)" }}
              >
                {dept.ext}
              </span>
            </li>
          ))}
        </ul>
      </div>

      {/* 자주 찾는 문서 */}
      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <Star className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>자주 찾는 문서</p>
        </div>
        <ul>
          {FREQUENT_DOCS.map((doc) => (
            <li key={doc.label} className="flex items-center justify-between px-5 py-3.5 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 transition-colors" style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-2.5 min-w-0">
                <FileText className="w-3.5 h-3.5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
                <span style={{ color: "var(--foreground)", fontSize: "13px" }} className="truncate">{doc.label}</span>
              </div>
              <span style={{ color: "var(--muted-foreground)", fontSize: "11px", flexShrink: 0, marginLeft: "8px" }}>{doc.dept}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 최근 본 문서 */}
      <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.04)" }}>
        <div className="px-5 py-4 border-b flex items-center gap-2" style={{ borderColor: "var(--border)" }}>
          <Clock className="w-4 h-4" style={{ color: "var(--muted-foreground)" }} />
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700 }}>최근 본 문서</p>
        </div>
        <ul>
          {RECENT_DOCS.map((doc, i) => (
            <li key={i} className="flex items-center gap-2.5 px-5 py-3.5 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 transition-colors" style={{ borderColor: "var(--border)" }}>
              <span style={{ color: "var(--muted-foreground)", fontSize: "11px", fontWeight: 700, minWidth: "16px" }}>{i + 1}</span>
              <span style={{ color: "var(--foreground)", fontSize: "13px" }}>{doc}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* 검색 팁 */}
      <div className="p-5 border" style={{ borderRadius: "16px", background: "var(--brand-green-light)", borderColor: "var(--brand-green-light)" }}>
        <div className="flex items-center gap-2 mb-3">
          <Lightbulb className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
          <p style={{ color: "var(--brand-green-dark)", fontSize: "13px", fontWeight: 700 }}>검색 팁</p>
        </div>
        <ul className="space-y-2">
          {SEARCH_TIPS.map((tip, i) => (
            <li key={i} className="flex items-start gap-2">
              <span style={{ color: "var(--brand-green)", fontSize: "11px", fontWeight: 700, marginTop: "2px" }}>·</span>
              <span style={{ color: "var(--brand-green-dark)", fontSize: "12px", lineHeight: 1.6 }}>{tip}</span>
            </li>
          ))}
        </ul>
      </div>

    </div>
  );
}
