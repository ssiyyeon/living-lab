import { useEffect, useState } from "react";
import {
  ArrowRight,
  ArrowUp,
  BookOpen,
  ChevronDown,
  ClipboardList,
  ClipboardPlus,
  Clock3,
  Loader2,
  Menu,
  MessageSquareText,
  Moon,
  NotebookPen,
  PanelLeftClose,
  PanelLeftOpen,
  PhoneCall,
  Search,
  Siren,
  X,
} from "lucide-react";
import { SearchResults } from "./components/SearchResults";
import { QuickGuideView } from "./components/QuickGuideView";
import { DutyTimelineDrawer } from "./components/DutyTimelineDrawer";
import { MiniDutyChat } from "./components/MiniDutyChat";
import { ManualCatalogView } from "./components/ManualCatalogView";
import {
  fetchManualCatalog,
  fetchQuickGuides,
  searchComplaints,
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
  | "full_manual";

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

export default function App() {
  const isMiniMode = new URLSearchParams(window.location.search).get("mini") === "1";
  return isMiniMode ? <MiniDutyChat /> : <MainApp />;
}

function MainApp() {
  const [activeView, setActiveView] = useState<ViewId>("response");
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [drawerGuideId, setDrawerGuideId] = useState<ViewId | null>(null);
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
    if (!isSidebarOpen && !drawerGuideId) return;

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsSidebarOpen(false);
        setDrawerGuideId(null);
      }
    };

    const shouldLockScroll = Boolean(drawerGuideId)
      || (isSidebarOpen && window.matchMedia("(max-width: 767px)").matches);

    if (shouldLockScroll) document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isSidebarOpen, drawerGuideId]);

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
    setIsSidebarOpen(false);
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

  return (
    <div
      className="min-h-screen"
      style={{
        background: "var(--background)",
        color: "var(--foreground)",
        fontFamily: "var(--font-family)",
      }}
    >
      <header
        className="sticky top-0 z-30 border-b"
        style={{ background: "rgba(255,255,255,0.96)", borderColor: "var(--border)" }}
      >
        <div className="mx-auto flex max-w-[960px] items-center justify-between px-5 py-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsSidebarOpen((open) => !open)}
              aria-label="업무 메뉴 열기"
              aria-expanded={isSidebarOpen}
              aria-controls="work-sidebar"
              className="inline-flex h-10 w-10 items-center justify-center rounded-xl border bg-white transition-colors hover:bg-[#EAF6FC] md:hidden"
              style={{ borderColor: "var(--border)", color: "var(--foreground)" }}
            >
              <Menu className="h-5 w-5" />
            </button>
            <button
              type="button"
              onClick={handleGoHome}
              aria-label="민원 응대 홈으로 이동"
              title="민원 응대 홈"
              className="rounded-lg p-1 transition-opacity hover:opacity-75 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8] focus-visible:ring-offset-2"
            >
              <img src={yusungLogo} alt="유성구 로고" className="h-10 w-auto object-contain sm:h-11" />
            </button>
          </div>
          <div className="flex items-center">
            <div
              className="inline-flex items-center gap-2 rounded-full border px-3 py-2 text-xs font-semibold"
              style={{ background: "var(--brand-red-light)", borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}
            >
              <Moon className="h-3.5 w-3.5" />
              야간당직 중
            </div>
          </div>
        </div>
      </header>

      {isSidebarOpen && (
          <button
            type="button"
            aria-label="업무 메뉴 닫기"
            className="fixed inset-0 z-40 md:hidden"
            onClick={() => setIsSidebarOpen(false)}
          />
      )}

      <aside
        id="work-sidebar"
        aria-label="업무 메뉴"
        data-state={isSidebarOpen ? "expanded" : "collapsed"}
        className={`fixed bottom-0 left-0 top-[77px] flex flex-col bg-[var(--sidebar)] transition-[width,transform] duration-200 ease-out ${
          drawerGuideId ? "z-30" : "z-50"
        } ${
          isSidebarOpen
            ? "w-[260px] translate-x-0"
            : "invisible w-[260px] -translate-x-full pointer-events-none md:visible md:w-[72px] md:translate-x-0 md:pointer-events-auto"
        }`}
      >
            <div className={`flex h-14 items-center ${isSidebarOpen ? "justify-end px-4" : "justify-center"}`}>
              <button
                type="button"
                onClick={() => setIsSidebarOpen((open) => !open)}
                aria-label={isSidebarOpen ? "업무 메뉴 접기" : "업무 메뉴 펼치기"}
                className="inline-flex h-9 w-9 items-center justify-center rounded-lg transition-colors hover:bg-white"
                style={{ color: "var(--muted-foreground)" }}
              >
                {isSidebarOpen ? (
                  <PanelLeftClose className="h-5 w-5" />
                ) : (
                  <PanelLeftOpen className="h-5 w-5" />
                )}
              </button>
            </div>
            <nav className={`flex-1 overflow-y-auto py-2 ${isSidebarOpen ? "px-4" : "px-2"}`} aria-label="업무 카테고리">
            {NAV_ITEMS.map(({ id, label, icon: Icon }) => {
              const isActive = DRAWER_GUIDE_IDS.has(id)
                ? drawerGuideId === id
                : activeView === id;

              return (
                <button
                  key={id}
                  type="button"
                  onClick={() => {
                    if (DRAWER_GUIDE_IDS.has(id)) {
                      setDrawerGuideId(id);
                    } else {
                      setDrawerGuideId(null);
                      setActiveView(id);
                    }
                    setIsSidebarOpen(false);
                  }}
                  aria-current={isActive ? "page" : undefined}
                  title={isSidebarOpen ? undefined : label}
                  className={`flex w-full items-center py-3.5 text-left transition-colors hover:text-[#036EB8] ${
                    isSidebarOpen ? "gap-3 px-2" : "justify-center px-0"
                  } ${id === "duty_basics" || id === "full_manual" ? "mt-2 border-t pt-5" : ""}`}
                  style={{
                    borderColor: id === "duty_basics" || id === "full_manual" ? "var(--sidebar-border)" : undefined,
                    color: isActive ? "var(--brand-green)" : "var(--foreground)",
                  }}
                >
                  <Icon className="h-5 w-5 flex-shrink-0" />
                  {isSidebarOpen && <span className="whitespace-nowrap text-sm font-bold">{label}</span>}
                </button>
              );
            })}
            </nav>
            {isSidebarOpen && (
              <p className="border-t px-5 py-4 text-[11px] leading-5" style={{ borderColor: "var(--sidebar-border)", color: "var(--muted-foreground)" }}>
                공식 당직 매뉴얼과 과거 민원 처리 사례를 기준으로 안내합니다.
              </p>
            )}
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

      <div className={`transition-[padding] duration-200 ease-out ${isSidebarOpen ? "md:pl-[260px]" : "md:pl-[72px]"}`}>
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
