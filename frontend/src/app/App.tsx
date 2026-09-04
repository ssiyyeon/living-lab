import { useState } from "react";
import { Search, X, Loader2, Menu } from "lucide-react";
import { Sidebar } from "./components/Sidebar";
import { SearchResults, type SearchResult } from "./components/SearchResults";
import { searchManual, SearchApiError, type ApiSearchResult } from "@/api/search";
import yusungLogo from "@/imports/image.png";

{/* MARKER-MAKE-KIT-INVOKED */}

const EXAMPLE_QUERIES = [
  "지하차도에 물이 차서 차가 못 지나가요",
  "가스가 터진 것 같아요 냄새나요",
  "고양이가 로드킬 당했어요 사체를 치워주세요",
  "포트홀 때문에 타이어가 터질 뻔했어요",
  "불법으로 주차한 차를 단속해 주세요",
  "가로등이 고장 나서 어두워요",
];

function toSearchResult(result: ApiSearchResult, tier: string): SearchResult {
  const department = result.department || result.departments.join(" · ") || "관련 부서 확인 필요";
  return {
    id: result.id,
    tier,
    kind: result.kind,
    category: result.category,
    documentName: result.documentName,
    civilType: result.civilType,
    department,
    departments: result.departments,
    departmentContacts: result.departmentContacts,
    operatorGuidance: result.operatorGuidance,
    paragraphSummary: result.paragraphSummary,
    keyActions: result.keyActions,
    originalText: result.originalText,
    guidance: result.guidance,
    note: result.note,
    updatedAt: result.updatedAt,
    relevance: result.relevance,
    tags: result.tags,
    evidenceLevel: result.evidenceLevel,
    sourceReference: result.sourceReference,
    sourcePages: result.sourcePages,
    page: result.matchedPage ?? result.sourcePages[0] ?? null,
    originalUrl: result.originalUrl,
    candidateCount: result.candidateCount,
    departmentRouting: result.departmentRouting,
  };
}

export default function App() {
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searchNotice, setSearchNotice] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);

  const handleSearch = async (q?: string) => {
    const searchQuery = q ?? query;
    if (!searchQuery.trim()) return;
    if (q) setQuery(q);
    setIsSearching(true);
    setHasSearched(false);
    setSearchNotice("");
    try {
      const response = await searchManual(searchQuery.trim());
      setResults(response.results.map((result) => toSearchResult(result, response.tier)));
      setSearchNotice(response.message);
    } catch (error) {
      const apiError = error instanceof SearchApiError ? error : null;
      setResults([]);
      setSearchNotice(apiError?.message ?? "검색 요청에 실패했습니다.");
    } finally {
      setIsSearching(false);
      setHasSearched(true);
    }
  };

  const handleClear = () => {
    setQuery("");
    setHasSearched(false);
    setResults([]);
    setSearchNotice("");
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
                민원 대응 검색
              </span>
            </div>
          </div>
          <div className="flex items-center gap-2">
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
              당직 근무 지원
            </div>
          </div>
        </header>

        {/* Scrollable body */}
        <main className="flex-1 overflow-y-auto flex flex-col">
          <div
            className={`w-full px-10 ${!hasSearched && !isSearching ? "flex-1 flex flex-col justify-center" : "py-8"}`}
            style={{ maxWidth: "1220px", margin: "0 auto", alignSelf: "center", width: "100%" }}
          >

            {/* 검색창 */}
            <div className="mb-6">
              {!hasSearched && (
                <div className="mb-7 text-center">
                  <h1 style={{ color: "var(--foreground)", fontWeight: 800, lineHeight: 1.3, fontSize: "32px" }}>
                    민원 내용을 입력하면
                    <br />
                    <span style={{ color: "var(--brand-green)" }}>필요한 대응 절차를 안내합니다.</span>
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
              {!hasSearched && (
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

            </div>

            {/* 로딩 */}
            {isSearching && (
              <div className="flex flex-col items-center py-24 gap-4">
                <Loader2 className="w-10 h-10 animate-spin" style={{ color: "var(--brand-green)" }} />
                <p style={{ color: "var(--muted-foreground)", fontSize: "15px" }}>대응 절차를 확인하고 있습니다...</p>
              </div>
            )}

            {/* 검색 결과 */}
            {hasSearched && !isSearching && (
              <div className="mx-auto w-full" style={{ maxWidth: "820px" }}>
                <SearchResults results={results} notice={searchNotice} />
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
            당직 민원 검색 시스템 · 관리부서: 총무과
          </p>
          <p style={{ color: "var(--muted-foreground)", fontSize: "10px", fontFamily: "var(--font-mono)" }}>
            {new Date().toLocaleDateString("ko-KR", { year: "numeric", month: "long", day: "numeric", weekday: "short" })}
          </p>
        </footer>
      </div>
    </div>
  );
}
