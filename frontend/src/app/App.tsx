import { useState } from "react";
import { Search, X, Loader2, Bell, HelpCircle, Menu } from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { SearchResults } from "./components/SearchResults";
import { SearchSidePanel } from "./components/SearchSidePanel";
import yusungLogo from "@/imports/image.png";

{/* MARKER-MAKE-KIT-INVOKED */}

const EXAMPLE_QUERIES = [
  "야간 소음 민원 처리 절차",
  "건축 허가 문의 담당 부서",
  "기초생활수급 긴급 지원",
  "도로 파손 신고 방법",
  "불법 주정차 단속 안내",
  "위생 점검 민원 접수",
];

export default function App() {
  const [activeCategory, setActiveCategory] = useState("manual");
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasResults, setHasResults] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSearch = (q?: string) => {
    const searchQuery = q ?? query;
    if (!searchQuery.trim()) return;
    if (q) setQuery(q);
    setIsSearching(true);
    setHasResults(false);
    setTimeout(() => {
      setIsSearching(false);
      setHasResults(true);
    }, 900);
  };

  const handleClear = () => {
    setQuery("");
    setHasResults(false);
  };

  return (
    <div className="flex h-screen overflow-hidden" style={{ background: "var(--background)", fontFamily: "var(--font-family)" }}>
      {/* Sidebar */}
      <div
        className="flex-shrink-0 transition-all duration-200"
        style={{
          width: sidebarOpen ? "256px" : "0px",
          overflow: "hidden",
          padding: sidebarOpen ? "12px 0 12px 12px" : "0",
        }}
      >
        <div
          style={{
            width: "232px",
            height: "100%",
            borderRadius: "16px",
            overflow: "hidden",
            boxShadow: "0 2px 12px rgba(0,0,0,0.08)",
          }}
        >
          <Sidebar
            activeCategory={activeCategory}
            onCategoryChange={setActiveCategory}
            logoSrc={yusungLogo}
          />
        </div>
      </div>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden min-w-0">
        {/* Top header */}
        <header
          className="flex-shrink-0 flex items-center justify-between px-5 py-3 border-b"
          style={{ background: "var(--card)", borderColor: "var(--border)" }}
        >
          <div className="flex items-center gap-3">
            <button
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-1.5 transition-colors duration-150"
              style={{ borderRadius: "8px", color: "var(--muted-foreground)" }}
            >
              <Menu className="w-4 h-4" />
            </button>
            <div className="flex items-center gap-2">
              <span style={{ color: "var(--muted-foreground)", fontSize: "12px" }}>총무과</span>
              <span style={{ color: "var(--border)" }}>/</span>
              <span style={{ color: "var(--foreground)", fontSize: "12px", fontWeight: 500 }}>
                {{
                  dept: "부서 정보",
                  manual: "당직 매뉴얼",
                  civil: "민원 유형",
                  frequent: "자주 찾는 자료",
                  notice: "공지사항",
                  reference: "참고 문서",
                }[activeCategory] ?? "민원 검색"}
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button className="relative p-1.5 transition-colors duration-150" style={{ borderRadius: "8px", color: "var(--muted-foreground)" }}>
              <Bell className="w-4 h-4" />
              <span
                className="absolute top-1 right-1 w-1.5 h-1.5 rounded-full"
                style={{ background: "#C0392B" }}
              />
            </button>
            <button className="p-1.5 transition-colors duration-150" style={{ borderRadius: "8px", color: "var(--muted-foreground)" }}>
              <HelpCircle className="w-4 h-4" />
            </button>
            <div
              className="h-5 w-px mx-1"
              style={{ background: "var(--border)" }}
            />
            <div
              className="px-2.5 py-1 text-xs"
              style={{
                borderRadius: "999px",
                background: "var(--brand-green-light)",
                color: "var(--brand-green-dark)",
                fontWeight: 600,
                fontFamily: "var(--font-mono)",
              }}
            >
              야간당직 중
            </div>
          </div>
        </header>

        {/* Scrollable body */}
        <main className="flex-1 overflow-y-auto flex flex-col">
          <div
            className={`w-full px-10 ${!hasResults && !isSearching ? "flex-1 flex flex-col justify-center" : "py-8"}`}
            style={{ maxWidth: "1220px", margin: "0 auto", alignSelf: "center", width: "100%" }}
          >

            {/* 검색창 */}
            <div className="mb-6">
              {!hasResults && (
                <div className="mb-7 text-center">
                  <h1 style={{ color: "var(--foreground)", fontWeight: 800, lineHeight: 1.3, fontSize: "32px" }}>
                    민원 내용을 입력하면
                    <br />
                    <span style={{ color: "var(--brand-green)" }}>관련 문서를 즉시 찾아드립니다.</span>
                  </h1>
                </div>
              )}

              <div
                className="flex items-stretch border-2 overflow-hidden transition-all duration-200"
                style={{ borderRadius: "14px", background: "#fff", borderColor: "var(--brand-green)" }}
              >
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                  placeholder="무엇을 찾고 계신가요?"
                  className="flex-1 outline-none bg-transparent px-5"
                  style={{ color: "var(--foreground)", fontSize: "15px", fontFamily: "var(--font-family)", paddingTop: "13px", paddingBottom: "13px" }}
                />
                {query && (
                  <button onClick={handleClear} className="flex items-center px-3" style={{ color: "var(--muted-foreground)" }}>
                    <X className="w-4 h-4" />
                  </button>
                )}
                <button
                  onClick={() => handleSearch()}
                  disabled={isSearching}
                  className="flex-shrink-0 flex items-center justify-center gap-2 px-7 transition-all duration-150"
                  style={{ background: "var(--brand-green)", color: "#fff", cursor: "pointer", fontSize: "14px", fontWeight: 600 }}
                >
                  {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
                  검색
                </button>
              </div>

              {/* 검색 예시 (초기 상태) */}
              {!hasResults && (
                <div className="mt-4">
                  <p style={{ color: "var(--muted-foreground)", fontSize: "13px", marginBottom: "10px" }}>검색 예시</p>
                  <div className="flex flex-wrap gap-2">
                    {EXAMPLE_QUERIES.map((ex) => (
                      <button
                        key={ex}
                        onClick={() => handleSearch(ex)}
                        className="px-4 py-2 border transition-all duration-150"
                        style={{ borderRadius: "999px", background: "#fff", borderColor: "var(--border)", color: "var(--muted-foreground)", fontSize: "13px" }}
                      >
                        {ex}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* 검색 요약바 (결과 있을 때) */}
              {hasResults && !isSearching && (
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <span
                    className="px-3.5 py-1.5"
                    style={{ borderRadius: "999px", background: "var(--brand-green)", color: "#fff", fontSize: "13px", fontWeight: 700 }}
                  >
                    총 4건
                  </span>
                  <div className="flex-1" />
                  <span style={{ color: "var(--muted-foreground)", fontSize: "12px" }}>
                    추천 담당부서: <strong style={{ color: "var(--foreground)" }}>총무과 · 민원과</strong>
                  </span>
                  <span
                    className="px-3 py-1.5"
                    style={{ borderRadius: "8px", background: "#FFF7E6", color: "#A07020", fontSize: "12px", fontWeight: 600 }}
                  >
                    ⚡ 야간 긴급 시 총무과 즉시 연계
                  </span>
                </div>
              )}
            </div>

            {/* 로딩 */}
            {isSearching && (
              <div className="flex flex-col items-center py-24 gap-4">
                <Loader2 className="w-10 h-10 animate-spin" style={{ color: "var(--brand-green)" }} />
                <p style={{ color: "var(--muted-foreground)", fontSize: "15px" }}>관련 문서를 검색하고 있습니다...</p>
              </div>
            )}

            {/* 검색 결과 — 2단 레이아웃 */}
            {hasResults && !isSearching && (
              <div className="flex gap-6 items-start">
                <div className="flex-1 min-w-0">
                  <SearchResults />
                </div>
                <div className="flex-shrink-0" style={{ width: "300px" }}>
                  <SearchSidePanel />
                </div>
              </div>
            )}

            {/* 초기 상태 — 2단 카드 */}
            {!hasResults && !isSearching && (
              <div className="grid grid-cols-2 gap-6">

                {/* 최근 공지사항 */}
                <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.05)" }}>
                  <div className="px-7 py-5 border-b flex items-center justify-between" style={{ borderColor: "var(--border)" }}>
                    <p style={{ color: "var(--foreground)", fontSize: "17px", fontWeight: 700 }}>최근 공지사항</p>
                    <button style={{ color: "var(--brand-green)", fontSize: "14px", fontWeight: 500 }}>전체 보기</button>
                  </div>
                  <ul>
                    {[
                      { label: "[긴급] 야간 당직 연락망 변경 안내", date: "2024-12-10", badge: "긴급" },
                      { label: "2025년 1월 당직 일정 공지", date: "2024-12-05", badge: "일반" },
                      { label: "민원 처리 시스템 업데이트 안내", date: "2024-11-28", badge: "시스템" },
                      { label: "연말 당직 비상연락망 배포", date: "2024-11-20", badge: "일반" },
                      { label: "민원서류 보존기간 변경 안내", date: "2024-11-10", badge: "시스템" },
                    ].map((notice, i) => (
                      <li key={i} className="flex items-center justify-between px-7 py-5 border-b last:border-b-0 cursor-pointer hover:bg-gray-50 transition-colors" style={{ borderColor: "var(--border)" }}>
                        <div className="flex items-center gap-3">
                          <span className="px-3 py-1.5 flex-shrink-0" style={{ borderRadius: "8px", background: notice.badge === "긴급" ? "#FBEAEA" : "var(--muted)", color: notice.badge === "긴급" ? "#A02020" : "var(--muted-foreground)", fontSize: "13px", fontWeight: 600 }}>
                            {notice.badge}
                          </span>
                          <span style={{ color: "var(--foreground)", fontSize: "15px" }}>{notice.label}</span>
                        </div>
                        <span style={{ color: "var(--muted-foreground)", fontSize: "13px", flexShrink: 0 }}>{notice.date}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 업무 바로가기 */}
                <div className="overflow-hidden border" style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)", boxShadow: "0 1px 6px rgba(0,0,0,0.05)" }}>
                  <div className="px-7 py-5 border-b" style={{ borderColor: "var(--border)" }}>
                    <p style={{ color: "var(--foreground)", fontSize: "17px", fontWeight: 700 }}>업무 바로가기</p>
                  </div>
                  <div className="grid grid-cols-3 gap-0">
                    {[
                      { label: "비상 연락망", icon: "📞" },
                      { label: "야간 처리 절차", icon: "🌙" },
                      { label: "민원 접수 양식", icon: "📋" },
                      { label: "당직 일지 작성", icon: "📝" },
                      { label: "부서 안내도", icon: "🏢" },
                      { label: "긴급 신고 연계", icon: "🚨" },
                    ].map((item) => (
                      <button
                        key={item.label}
                        className="flex flex-col items-center justify-center gap-3 border-b border-r transition-colors hover:bg-gray-50"
                        style={{ borderColor: "var(--border)", paddingTop: "36px", paddingBottom: "36px" }}
                      >
                        <span style={{ fontSize: "32px" }}>{item.icon}</span>
                        <span style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 500 }}>{item.label}</span>
                      </button>
                    ))}
                  </div>
                </div>

              </div>
            )}

          </div>
        </main>

        {/* Footer */}
        <footer
          className="flex-shrink-0 flex items-center justify-between px-6 py-2 border-t"
          style={{ background: "var(--card)", borderColor: "var(--border)" }}
        >
          <p style={{ color: "var(--muted-foreground)", fontSize: "10px" }}>
            당직 민원 검색 시스템 v2.4.1 · 관리부서: 정보화담당관실
          </p>
          <p style={{ color: "var(--muted-foreground)", fontSize: "10px", fontFamily: "var(--font-mono)" }}>
            {new Date().toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "short" })}
          </p>
        </footer>
      </div>
    </div>
  );
}
