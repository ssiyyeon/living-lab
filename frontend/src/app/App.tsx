import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUp,
  BookOpen,
  BookUser,
  ChevronDown,
  ClipboardList,
  ClipboardPlus,
  Clock3,
  Loader2,
  LogOut,
  MessageSquareText,
  MessagesSquare,
  Moon,
  NotebookPen,
  PhoneCall,
  Search,
  Settings,
  Siren,
  X,
} from "lucide-react";
import { SearchResults } from "./components/SearchResults";
import { QuickGuideView } from "./components/QuickGuideView";
import { DutyTimelineDrawer } from "./components/DutyTimelineDrawer";
import { ContactDirectoryDrawer } from "./components/ContactDirectoryDrawer";
import { MiniDutyChat } from "./components/MiniDutyChat";
import { ManualCatalogView } from "./components/ManualCatalogView";
import { AdminPage } from "./components/AdminPage";
import { LoginPage } from "./components/LoginPage";
import {
  fetchAuthStatus,
  fetchCurrentUser,
  fetchManualCatalog,
  fetchQuickGuides,
  logout,
  searchComplaints,
  type AuthUser,
  type ManualCatalogResponse,
  type QuickGuide,
  type SearchResponse,
} from "./api/search";
import yusungLogo from "@/imports/image.png";

const EXAMPLE_QUERIES = [
  "야간 소음",
  "건축 허가 문의",
  "도로 포트홀 신고",
  "불법 주정차 신고",
  "유기동물 발견",
  "쓰레기 수거 문의",
];

type ViewId =
  | "response"
  | "duty_timeline"
  | "duty_log"
  | "complaint_registration"
  | "duty_basics"
  | "disaster_response"
  | "emergency_contacts"
  | "full_manual"
  | "admin";

const DRAWER_GUIDE_IDS = new Set<ViewId>([
  "duty_timeline",
  "duty_basics",
  "disaster_response",
  "emergency_contacts",
]);

const NAV_ITEMS = [
  {
    id: "response" as const,
    label: "민원 대응",
    icon: MessageSquareText,
  },
  {
    id: "duty_timeline" as const,
    label: "근무 타임라인",
    icon: Clock3,
  },
  {
    id: "duty_log" as const,
    label: "당직근무일지",
    icon: NotebookPen,
  },
  {
    id: "complaint_registration" as const,
    label: "당직민원 등록",
    icon: ClipboardPlus,
  },
  {
    id: "duty_basics" as const,
    label: "당직 기본업무",
    icon: ClipboardList,
  },
  {
    id: "disaster_response" as const,
    label: "재난·비상 대응",
    icon: Siren,
  },
  {
    id: "emergency_contacts" as const,
    label: "긴급 연락망",
    icon: PhoneCall,
  },
  {
    id: "full_manual" as const,
    label: "전체 매뉴얼",
    icon: BookOpen,
  },
];

const HOME_GUIDES = [
  {
    id: "duty_timeline" as const,
    label: "근무 타임라인",
    description: "시간대별 해야 할 일",
    icon: Clock3,
  },
  {
    id: "duty_basics" as const,
    label: "당직 기본업무",
    description: "시건·순찰·기록·인계 확인",
    icon: ClipboardList,
  },
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
  const [user, setUser] = useState<AuthUser | null>(null);
  const [needsSetup, setNeedsSetup] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [authError, setAuthError] = useState("");
  const isMiniMode = new URLSearchParams(window.location.search).get("mini") === "1";

  useEffect(() => {
    let isMounted = true;
    const checkAuth = async () => {
      try {
        const status = await fetchAuthStatus();
        if (!isMounted) return;
        setNeedsSetup(status.needsSetup);
        if (!status.needsSetup) {
          try {
            const currentUser = await fetchCurrentUser();
            if (isMounted) setUser(currentUser);
          } catch {
            if (isMounted) setUser(null);
          }
        }
      } catch (error) {
        if (isMounted) {
          setAuthError(error instanceof Error ? error.message : "서버에 연결하지 못했습니다.");
        }
      } finally {
        if (isMounted) setIsCheckingAuth(false);
      }
    };
    void checkAuth();
    return () => {
      isMounted = false;
    };
  }, []);

  if (isCheckingAuth) {
    return (
      <div className="flex min-h-screen items-center justify-center gap-3 bg-[#F3F5F7] text-sm" style={{ color: "var(--muted-foreground)" }}>
        <Loader2 className="h-5 w-5 animate-spin" /> 로그인 상태를 확인하고 있습니다.
      </div>
    );
  }

  if (authError) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F3F5F7] px-5">
        <div className="max-w-md rounded-2xl border bg-white p-6 text-center" style={{ borderColor: "var(--brand-red)" }}>
          <h1 className="text-xl font-extrabold">백엔드 연결이 필요합니다</h1>
          <p className="mt-3 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>{authError}</p>
          <button type="button" onClick={() => window.location.reload()} className="mt-5 rounded-xl px-5 py-2.5 text-sm font-bold text-white" style={{ background: "var(--brand-green)" }}>다시 확인</button>
        </div>
      </div>
    );
  }

  if (!user) {
    return (
      <LoginPage
        needsSetup={needsSetup}
        onAuthenticated={(authenticatedUser) => {
          setUser(authenticatedUser);
          setNeedsSetup(false);
        }}
      />
    );
  }

  return isMiniMode ? <MiniDutyChat /> : <MainApp user={user} onLoggedOut={() => setUser(null)} />;
}

function MainApp({ user, onLoggedOut }: { user: AuthUser; onLoggedOut: () => void }) {
  const [activeView, setActiveView] = useState<ViewId>("response");
  const [drawerGuideId, setDrawerGuideId] = useState<ViewId | null>(null);
  const [isContactDirectoryOpen, setIsContactDirectoryOpen] = useState(false);
  const [homeGuideId, setHomeGuideId] = useState<(typeof HOME_GUIDES)[number]["id"] | null>(null);
  const [query, setQuery] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const [searchResponse, setSearchResponse] = useState<SearchResponse | null>(null);
  const [searchError, setSearchError] = useState("");
  const [quickGuides, setQuickGuides] = useState<QuickGuide[]>([]);
  const [quickGuideSource, setQuickGuideSource] = useState("");
  const [guideError, setGuideError] = useState("");
  const [manualCatalog, setManualCatalog] = useState<ManualCatalogResponse | null>(null);
  const [manualCatalogError, setManualCatalogError] = useState("");

  useEffect(() => {
    let isMounted = true;

    fetchQuickGuides()
      .then((response) => {
        if (!isMounted) return;
        setQuickGuides(response.guides);
        setQuickGuideSource(response.source);
      })
      .catch((error) => {
        if (!isMounted) return;
        setGuideError(
          error instanceof Error
            ? error.message
            : "업무 가이드를 불러오지 못했습니다.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (activeView !== "full_manual" || manualCatalog) return;

    let isMounted = true;
    setManualCatalogError("");

    fetchManualCatalog()
      .then((response) => {
        if (isMounted) setManualCatalog(response);
      })
      .catch((error) => {
        if (!isMounted) return;
        setManualCatalogError(
          error instanceof Error
            ? error.message
            : "전체 매뉴얼을 불러오지 못했습니다.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, [activeView, manualCatalog]);

  useEffect(() => {
    if (!drawerGuideId && !isContactDirectoryOpen) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setDrawerGuideId(null);
        setIsContactDirectoryOpen(false);
      }
    };

    const shouldLockScroll = Boolean(drawerGuideId || isContactDirectoryOpen);

    if (shouldLockScroll) document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [drawerGuideId, isContactDirectoryOpen]);

  const selectedGuide = quickGuides.find((guide) => guide.id === activeView);
  const drawerGuide = quickGuides.find((guide) => guide.id === drawerGuideId);
  const homeGuide = quickGuides.find((guide) => guide.id === homeGuideId);

  const handleSearch = async (nextQuery?: string) => {
    const searchQuery = (nextQuery ?? query).trim();
    if (!searchQuery) return;

    if (nextQuery) setQuery(nextQuery);
    setIsSearching(true);
    setHasSearched(false);
    setSearchError("");

    try {
      const response = await searchComplaints(searchQuery, 1);
      setSearchResponse(response);
      setHasSearched(true);
    } catch (error) {
      setSearchResponse(null);
      setSearchError(
        error instanceof Error
          ? error.message
          : "검색 서버에 연결하지 못했습니다.",
      );
    } finally {
      setIsSearching(false);
    }
  };

  const handleClear = () => {
    setQuery("");
    setHasSearched(false);
    setSearchResponse(null);
    setSearchError("");
  };

  const handleGoHome = () => {
    setActiveView("response");
    setDrawerGuideId(null);
    setIsContactDirectoryOpen(false);
    setHomeGuideId(null);
    handleClear();
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const handleCompactSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!query.trim() || isSearching) return;

    setActiveView("response");
    void handleSearch();
  };

  const openMiniChat = () => {
    const miniChatUrl = new URL(window.location.href);
    miniChatUrl.search = "?mini=1";
    window.open(
      miniChatUrl.toString(),
      "yuseong-duty-mini-chat",
      "popup=yes,width=430,height=720,resizable=yes,scrollbars=no",
    )?.focus();
  };

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      onLoggedOut();
    }
  };

  return (
    <div
      className="min-h-screen"
      style={{
        background: "var(--background)",
        color: "var(--foreground)",
        fontFamily: "var(--font-family)",
      }}
    >
      <aside
        id="work-sidebar"
        aria-label="업무 메뉴"
        data-state="expanded"
        className={`fixed inset-y-0 left-0 flex w-[180px] bg-[var(--sidebar)] p-2 ${
          drawerGuideId || isContactDirectoryOpen ? "z-30" : "z-50"
        }`}
      >
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[24px] border bg-white" style={{ borderColor: "var(--border)" }}>
          <button
            type="button"
            onClick={handleGoHome}
            aria-label="민원 응대 홈으로 이동"
            className="border-b px-4 py-6 text-center transition-colors hover:bg-[#F7FCFF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#036EB8]"
            style={{ borderColor: "var(--border)" }}
          >
            <img src={yusungLogo} alt="유성구 로고" className="mx-auto h-11 w-auto object-contain" />
            <span className="mt-3 block text-xs font-semibold" style={{ color: "var(--muted-foreground)" }}>
              당직 근무 지원
            </span>
          </button>

          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-4">
            <p className="mb-2 px-3 text-[11px] font-bold" style={{ color: "var(--muted-foreground)" }}>
              업무 메뉴
            </p>
            <nav className="space-y-1" aria-label="업무 카테고리">
              {[
                ...NAV_ITEMS,
                ...(user.role === "admin"
                  ? [{ id: "admin" as const, label: "관리자", icon: Settings }]
                  : []),
              ].map(({ id, label, icon: Icon }) => {
                const isActive = DRAWER_GUIDE_IDS.has(id)
                  ? drawerGuideId === id
                  : activeView === id && !isContactDirectoryOpen;

                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => {
                      setIsContactDirectoryOpen(false);
                      if (DRAWER_GUIDE_IDS.has(id)) {
                        setDrawerGuideId(id);
                      } else {
                        setDrawerGuideId(null);
                        setActiveView(id);
                      }
                    }}
                    aria-current={isActive ? "page" : undefined}
                    className="flex w-full items-center gap-2.5 rounded-xl px-3 py-3 text-left text-sm font-bold transition-colors"
                    style={{
                      background: isActive ? "#E7F0FC" : "transparent",
                      color: isActive ? "#0B4DA2" : "var(--muted-foreground)",
                    }}
                  >
                    <Icon className="h-[18px] w-[18px] flex-shrink-0" />
                    <span className="whitespace-nowrap">{label}</span>
                  </button>
                );
              })}
            </nav>

            <div className="mt-4 border-t pt-4" style={{ borderColor: "var(--border)" }}>
              <p className="mb-2 px-3 text-[11px] font-bold" style={{ color: "var(--muted-foreground)" }}>
                지원 도구
              </p>
              <button
                type="button"
                onClick={openMiniChat}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-3 text-left text-sm font-bold transition-colors hover:bg-[#F2F7FC]"
                style={{ color: "var(--muted-foreground)" }}
              >
                <MessagesSquare className="h-[18px] w-[18px] flex-shrink-0" />
                <span>미니 응대</span>
              </button>
              <button
                type="button"
                onClick={() => {
                  setDrawerGuideId(null);
                  setIsContactDirectoryOpen(true);
                }}
                aria-expanded={isContactDirectoryOpen}
                aria-controls="contact-directory-drawer"
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-3 text-left text-sm font-bold transition-colors"
                style={{
                  background: isContactDirectoryOpen ? "#E7F0FC" : "transparent",
                  color: isContactDirectoryOpen ? "#0B4DA2" : "var(--muted-foreground)",
                }}
              >
                <BookUser className="h-[18px] w-[18px] flex-shrink-0" />
                <span>연락처</span>
              </button>
            </div>
          </div>

          <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
            <div className="rounded-2xl px-3 py-3" style={{ background: "#F2F6FC" }}>
              <div className="flex items-center gap-2 text-sm font-extrabold" style={{ color: "var(--foreground)" }}>
                <Moon className="h-4 w-4" style={{ color: "var(--brand-red)" }} />
                <span className="min-w-0 flex-1 truncate">{user.displayName}</span>
                <button type="button" onClick={() => void handleLogout()} aria-label="로그아웃" title="로그아웃" className="rounded-lg p-1" style={{ color: "var(--muted-foreground)" }}>
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-1 pl-6 text-[11px]" style={{ color: "var(--muted-foreground)" }}>
                {user.role === "admin" ? "관리자 · 야간당직" : "야간당직"}
              </p>
            </div>
          </div>
        </div>
      </aside>

      {drawerGuideId && (
        <>
          <button
            type="button"
            aria-label={`${drawerGuide?.title ?? "업무 안내"} 닫기`}
            className="fixed inset-0 z-40"
            onClick={() => setDrawerGuideId(null)}
            style={{ background: "rgba(17, 24, 39, 0.32)", backdropFilter: "blur(2px)" }}
          />
          <aside
            id="guide-drawer"
            role="dialog"
            aria-modal="true"
            aria-label={drawerGuide?.title ?? "업무 안내"}
            className="fixed inset-x-0 bottom-0 z-50 flex max-h-[88vh] flex-col overflow-hidden rounded-t-3xl border bg-white sm:inset-x-auto sm:bottom-3 sm:right-3 sm:top-3 sm:max-h-none sm:w-[min(500px,calc(100vw-24px))] sm:rounded-3xl"
            style={{ borderColor: "var(--border)" }}
          >
            <div
              className="flex items-start justify-between gap-4 border-b bg-white px-5 py-5"
              style={{ borderColor: "var(--border)" }}
            >
              <div>
                <h2 className="text-xl font-extrabold">
                  {drawerGuideId === "duty_timeline"
                    ? "근무 시간대를 선택하세요"
                    : drawerGuide?.title ?? "업무 안내"}
                </h2>
                <p
                  className="mt-1.5 text-xs leading-5"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  {drawerGuideId === "duty_timeline"
                    ? "시간대를 누르면 지금 해야 할 일을 바로 확인할 수 있습니다."
                    : drawerGuide?.description}
                </p>
              </div>
              <button
                type="button"
                onClick={() => setDrawerGuideId(null)}
                aria-label={`${drawerGuide?.title ?? "업무 안내"} 닫기`}
                className="inline-flex h-10 w-10 items-center justify-center rounded-xl border bg-white transition-colors hover:bg-[#EAF6FC]"
                style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="min-h-0 flex-1 overflow-y-auto pt-4 sm:pt-5">
              {drawerGuide ? (
                drawerGuideId === "duty_timeline" ? (
                  <DutyTimelineDrawer guide={drawerGuide} source={quickGuideSource} />
                ) : (
                  <div className="px-4 pb-5 sm:px-5">
                    <QuickGuideView guide={drawerGuide} source={quickGuideSource} compact />
                  </div>
                )
              ) : (
                <div
                  role={guideError ? "alert" : "status"}
                  className="mx-4 flex min-h-[240px] items-center justify-center rounded-2xl border bg-white px-6 text-center text-sm sm:mx-5"
                  style={{ borderColor: "var(--border)", color: guideError ? "#9B2C22" : "var(--muted-foreground)" }}
                >
                  {guideError || (
                    <span className="inline-flex items-center gap-3">
                      <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />
                      업무 안내를 불러오고 있습니다.
                    </span>
                  )}
                </div>
              )}
            </div>

            <div className="border-t bg-white p-3" style={{ borderColor: "var(--border)" }}>
              <button
                type="button"
                onClick={() => setDrawerGuideId(null)}
                className="w-full rounded-xl py-3 text-sm font-bold text-white"
                style={{ background: "var(--brand-green)" }}
              >
                확인 완료
              </button>
            </div>
          </aside>
        </>
      )}

      {isContactDirectoryOpen && (
        <>
          <button
            type="button"
            aria-label="전화번호부 닫기"
            className="fixed inset-0 z-40"
            onClick={() => setIsContactDirectoryOpen(false)}
            style={{ background: "rgba(17, 24, 39, 0.32)", backdropFilter: "blur(2px)" }}
          />
          <ContactDirectoryDrawer onClose={() => setIsContactDirectoryOpen(false)} />
        </>
      )}

      <div className="pl-[180px]">
        <main
          className={`mx-auto w-full max-w-[960px] px-5 py-10 ${activeView === "response" ? "" : "pb-28"}`}
        >
        <div className="min-w-0">
          {activeView === "response" ? (
            <>
              <section
                className="mx-auto max-w-[880px] rounded-full border-2 bg-white p-2"
                style={{ borderColor: "var(--brand-green)" }}
              >
                <div className="flex items-stretch gap-2">
                  <div className="flex min-w-0 flex-1 items-center rounded-full px-4">
                    <Search className="mr-3 h-5 w-5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
                    <input
                      type="text"
                      value={query}
                      onChange={(event) => setQuery(event.target.value)}
                      onKeyDown={(event) => event.key === "Enter" && handleSearch()}
                      placeholder="예: 건축 허가를 어디에 문의하나요?"
                      aria-label="민원 내용"
                      className="min-w-0 flex-1 bg-transparent py-3 text-[15px] outline-none"
                    />
                    {query && (
                      <button
                        type="button"
                        onClick={handleClear}
                        aria-label="검색어 지우기"
                        className="rounded-lg p-2"
                        style={{ color: "var(--muted-foreground)" }}
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => handleSearch()}
                    disabled={isSearching || !query.trim()}
                    className="inline-flex items-center justify-center gap-2 rounded-full px-5 py-3 text-sm font-bold text-white disabled:cursor-not-allowed"
                    style={{ background: "var(--brand-green)" }}
                  >
                    {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />}
                    안내 보기
                  </button>
                </div>
              </section>

              {searchError && (
                <div
                  role="alert"
                  className="mt-4 rounded-xl border px-4 py-3 text-sm"
                  style={{ background: "var(--brand-red-light)", borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}
                >
                  {searchError}
                </div>
              )}

              {!hasSearched && !isSearching && (
                <>
                  <div className="mx-auto mt-5 flex max-w-[880px] flex-wrap gap-2">
                    {EXAMPLE_QUERIES.map((example) => (
                      <button
                        type="button"
                        key={example}
                        onClick={() => handleSearch(example)}
                        className="rounded-full border bg-white px-4 py-2 text-sm transition-colors hover:border-blue-300 hover:text-blue-700"
                        style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
                      >
                        {example}
                      </button>
                    ))}
                  </div>

                  <div className="mx-auto mt-10 max-w-[880px] border-y" style={{ borderColor: "var(--border)" }}>
                    <div className="grid sm:grid-cols-2">
                      {HOME_GUIDES.map(({ id, label, description, icon: Icon }, index) => {
                        const isTimelineDrawer = id === "duty_timeline";
                        const isExpanded = isTimelineDrawer
                          ? drawerGuideId === id
                          : homeGuideId === id;

                        return (
                          <button
                            key={id}
                            type="button"
                            onClick={() => {
                              if (isTimelineDrawer) {
                                setHomeGuideId(null);
                                setDrawerGuideId(id);
                                return;
                              }

                              setHomeGuideId((current) => current === id ? null : id);
                            }}
                            aria-expanded={isExpanded}
                            aria-controls={isTimelineDrawer ? "guide-drawer" : "home-guide-panel"}
                            className={`group flex items-center gap-4 px-3 py-6 text-left transition-colors hover:text-[#036EB8] sm:px-5 ${
                              index === 0
                                ? "border-b sm:border-b-0 sm:border-r"
                                : ""
                            }`}
                            style={{
                              borderColor: "var(--border)",
                              color: isExpanded ? "var(--brand-green-dark)" : undefined,
                            }}
                          >
                            <Icon
                              className="h-6 w-6 flex-shrink-0"
                              style={{ color: "var(--brand-green)" }}
                            />
                            <span className="min-w-0 flex-1">
                              <strong className="block text-[15px]">{label}</strong>
                              <span
                                className="mt-1 block text-xs"
                                style={{ color: "var(--muted-foreground)" }}
                              >
                                {description}
                              </span>
                            </span>
                            {isTimelineDrawer ? (
                              <ArrowRight
                                className="h-4 w-4 flex-shrink-0"
                                style={{ color: "var(--brand-green)" }}
                              />
                            ) : (
                              <ChevronDown
                                className={`h-4 w-4 flex-shrink-0 transition-transform duration-200 ${
                                  isExpanded ? "rotate-180" : ""
                                }`}
                                style={{ color: "var(--brand-green)" }}
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>

                    {homeGuideId && (
                      <div
                        id="home-guide-panel"
                        className="border-t px-3 py-6 sm:px-5 sm:py-7"
                        style={{ borderColor: "var(--border)" }}
                      >
                        {homeGuide ? (
                          <QuickGuideView guide={homeGuide} source={quickGuideSource} compact />
                        ) : (
                          <div
                            role={guideError ? "alert" : "status"}
                            className="flex min-h-32 items-center justify-center text-center text-sm"
                            style={{ color: guideError ? "#9B2C22" : "var(--muted-foreground)" }}
                          >
                            {guideError || (
                              <span className="inline-flex items-center gap-3">
                                <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />
                                업무 안내를 불러오고 있습니다.
                              </span>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </>
              )}

              {isSearching && (
                <div className="flex items-center justify-center gap-3 py-20 text-sm" style={{ color: "var(--muted-foreground)" }}>
                  <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />
                  대응 절차를 정리하고 있습니다.
                </div>
              )}

              {hasSearched && !isSearching && (
                <section className="mt-7">
                  <div className="mb-3 flex items-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
                    <span>입력한 민원</span>
                    <span>·</span>
                    <strong style={{ color: "var(--foreground)" }}>{searchResponse?.query}</strong>
                  </div>
                  <SearchResults
                    results={searchResponse?.results ?? []}
                    emptyMessage={searchResponse?.message}
                  />
                </section>
              )}
            </>
          ) : activeView === "admin" && user.role === "admin" ? (
            <AdminPage
              onGuidesChanged={() => {
                fetchQuickGuides()
                  .then((response) => {
                    setQuickGuides(response.guides);
                    setQuickGuideSource(response.source);
                  })
                  .catch(() => undefined);
              }}
            />
          ) : activeView === "full_manual" ? (
            manualCatalog ? (
              <ManualCatalogView catalog={manualCatalog} />
            ) : (
              <div
                role={manualCatalogError ? "alert" : "status"}
                className="flex min-h-[240px] items-center justify-center border-y px-6 text-center text-sm"
                style={{ borderColor: "var(--border)", color: manualCatalogError ? "#9B2C22" : "var(--muted-foreground)" }}
              >
                {manualCatalogError || (
                  <span className="inline-flex items-center gap-3">
                    <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />
                    전체 매뉴얼 71개 항목을 불러오고 있습니다.
                  </span>
                )}
              </div>
            )
          ) : selectedGuide ? (
            <QuickGuideView guide={selectedGuide} source={quickGuideSource} />
          ) : (
            <div
              role={guideError ? "alert" : "status"}
              className="flex min-h-[240px] items-center justify-center rounded-2xl border bg-white px-6 text-center text-sm"
              style={{ borderColor: "var(--border)", color: guideError ? "#9B2C22" : "var(--muted-foreground)" }}
            >
              {guideError || (
                <span className="inline-flex items-center gap-3">
                  <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />
                  공식 매뉴얼을 불러오고 있습니다.
                </span>
              )}
            </div>
          )}
        </div>
        </main>

      {activeView !== "response" && (
        <form
          onSubmit={handleCompactSearch}
          className="pointer-events-none fixed inset-x-0 bottom-4 z-20 px-4"
          role="search"
        >
          <div
            className="pointer-events-auto mx-auto flex w-full max-w-[560px] items-center gap-2 rounded-2xl border-2 bg-white p-2"
            style={{ borderColor: "var(--brand-green)" }}
          >
            <Search
              className="ml-2 h-4.5 w-4.5 flex-shrink-0"
              style={{ color: "var(--muted-foreground)" }}
            />
            <input
              type="text"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="민원 내용을 바로 검색하세요"
              aria-label="빠른 민원 검색"
              className="min-w-0 flex-1 bg-transparent px-1 py-2.5 text-sm outline-none"
            />
            <button
              type="submit"
              disabled={isSearching || !query.trim()}
              aria-label="민원 검색"
              className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-white transition-opacity disabled:cursor-not-allowed disabled:opacity-40"
              style={{ background: "var(--brand-green)" }}
            >
              {isSearching ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <ArrowUp className="h-5 w-5" />
              )}
            </button>
          </div>
        </form>
      )}

        <footer className="mx-auto max-w-[960px] px-5 pb-8 text-xs" style={{ color: "var(--muted-foreground)" }}>
          안내 결과는 공식 매뉴얼과 과거 당직민원 이첩 사례를 구분해 표시합니다.
        </footer>
      </div>
    </div>
  );
}
