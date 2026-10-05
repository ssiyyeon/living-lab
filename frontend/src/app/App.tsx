import { useEffect, useState } from "react";
import { ArrowUp, Loader2, Search } from "lucide-react";
import { AdminPage, type AdminTab } from "./components/AdminPage";
import { ContactDirectoryDrawer } from "./components/ContactDirectoryDrawer";
import { LoginPage } from "./components/LoginPage";
import { ManualCatalogView } from "./components/ManualCatalogView";
import { MiniDutyChat } from "./components/MiniDutyChat";
import { Sidebar, type PrimaryView } from "./components/Sidebar";
import { HomePage, type HomeUpdate } from "./pages/HomePage";
import { SituationPage } from "./pages/SituationPage";
import { WorkGuidePage } from "./pages/WorkGuidePage";
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
        if (isMounted) setAuthError(error instanceof Error ? error.message : "서버에 연결하지 못했습니다.");
      } finally {
        if (isMounted) setIsCheckingAuth(false);
      }
    };
    void checkAuth();
    return () => { isMounted = false; };
  }, []);

  if (isCheckingAuth) {
    return <div className="flex min-h-screen items-center justify-center gap-3 bg-[#F3F5F7] text-sm" style={{ color: "var(--muted-foreground)" }}><Loader2 className="h-5 w-5 animate-spin" /> 로그인 상태를 확인하고 있습니다.</div>;
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
    return <LoginPage needsSetup={needsSetup} onAuthenticated={(authenticatedUser) => { setUser(authenticatedUser); setNeedsSetup(false); }} />;
  }

  return isMiniMode
    ? <MiniDutyChat />
    : <MainApp user={user} onLoggedOut={() => setUser(null)} />;
}

function MainApp({ user, onLoggedOut }: { user: AuthUser; onLoggedOut: () => void }) {
  const [activeView, setActiveView] = useState<PrimaryView>("home");
  const [focusEmergency, setFocusEmergency] = useState(false);
  const [isContactDirectoryOpen, setIsContactDirectoryOpen] = useState(false);
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
  const [requestedGuideId, setRequestedGuideId] = useState<string>();
  const [requestedManualEntryId, setRequestedManualEntryId] = useState<string>();
  const [requestedAdminEdit, setRequestedAdminEdit] = useState<{ tab: AdminTab; itemId: string } | null>(null);

  const loadQuickGuides = () => {
    setGuideError("");
    return fetchQuickGuides()
      .then((response) => {
        setQuickGuides(response.guides);
        setQuickGuideSource(response.source);
      })
      .catch((error) => {
        setGuideError(error instanceof Error ? error.message : "업무 가이드를 불러오지 못했습니다.");
      });
  };

  const loadManualCatalog = () => {
    setManualCatalogError("");
    return fetchManualCatalog()
      .then((response) => {
        setManualCatalog(response);
      })
      .catch((error) => {
        setManualCatalogError(
          error instanceof Error ? error.message : "전체 매뉴얼을 불러오지 못했습니다.",
        );
      });
  };

  useEffect(() => {
    void Promise.all([loadQuickGuides(), loadManualCatalog()]);
  }, []);

  const recentUpdates: HomeUpdate[] = [
    ...quickGuides
      .filter((guide) => Boolean(guide.updatedAt))
      .map((guide) => ({
        id: `guide-${guide.id}`,
        title: `${guide.title} 안내가 수정되었습니다.`,
        kind: "수정" as const,
        date: guide.updatedAt ?? "",
        target: "work" as const,
        itemId: guide.id,
      })),
    ...(manualCatalog?.entries ?? [])
      .filter((entry) => Boolean(entry.isCustom || entry.isModified))
      .map((entry) => ({
        id: `manual-${entry.id}`,
        title: `${entry.title} 항목이 ${entry.isCustom ? "추가" : "수정"}되었습니다.`,
        kind: entry.isCustom ? "추가" as const : "수정" as const,
        date: entry.updatedAt ?? entry.addedAt ?? "",
        target: "manual" as const,
        itemId: entry.id,
      })),
  ]
    .sort((left, right) => right.date.localeCompare(left.date))
    .slice(0, 10);

  useEffect(() => {
    if (!isContactDirectoryOpen) return;
    const previousOverflow = document.body.style.overflow;
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsContactDirectoryOpen(false);
        setActiveView("home");
      }
    };
    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleEscape);
    };
  }, [isContactDirectoryOpen]);

  const handleSearch = async (nextQuery?: string) => {
    const searchQuery = (nextQuery ?? query).trim();
    if (!searchQuery || isSearching) return;
    setQuery(searchQuery);
    setActiveView("home");
    setIsSearching(true);
    setHasSearched(false);
    setSearchError("");
    try {
      const response = await searchComplaints(searchQuery, 3);
      setSearchResponse(response);
      setHasSearched(true);
    } catch (error) {
      setSearchResponse(null);
      setSearchError(error instanceof Error ? error.message : "검색 서버에 연결하지 못했습니다.");
    } finally {
      setIsSearching(false);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  const handleClear = () => {
    setQuery("");
    setHasSearched(false);
    setSearchResponse(null);
    setSearchError("");
  };

  const navigate = (view: PrimaryView, preserveUpdateTarget = false) => {
    if (!preserveUpdateTarget) {
      setRequestedGuideId(undefined);
      setRequestedManualEntryId(undefined);
    }
    setRequestedAdminEdit(null);
    if (view === "contacts") {
      setActiveView("contacts");
      setIsContactDirectoryOpen(true);
      return;
    }
    setIsContactDirectoryOpen(false);
    setFocusEmergency(false);
    setActiveView(view);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openUpdate = (update: HomeUpdate) => {
    if (update.target === "work") {
      setRequestedGuideId(update.itemId);
    } else {
      setRequestedManualEntryId(update.itemId);
    }
    navigate(update.target, true);
  };

  const openEmergency = () => {
    setFocusEmergency(true);
    setActiveView("situations");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openAdminEditor = (tab: "complaints" | "guides", itemId: string) => {
    setRequestedAdminEdit({ tab, itemId });
    setActiveView("admin");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const openQuickSearch = () => {
    const miniChatUrl = new URL(window.location.href);
    miniChatUrl.search = "?mini=1";
    window.open(miniChatUrl.toString(), "yuseong-duty-quick-search", "popup=yes,width=430,height=720,resizable=yes,scrollbars=no")?.focus();
  };

  const handleLogout = async () => {
    try {
      await logout();
    } finally {
      onLoggedOut();
    }
  };

  return (
    <div className="min-h-screen" style={{ background: "var(--background)", color: "var(--foreground)", fontFamily: "var(--font-family)" }}>
      <Sidebar logoSrc={yusungLogo} user={user} activeView={activeView} onNavigate={navigate} onOpenQuickSearch={openQuickSearch} onLogout={() => void handleLogout()} />

      {isContactDirectoryOpen && (
        <>
          <button type="button" aria-label="전화번호부 닫기" className="fixed inset-0 z-40" onClick={() => { setIsContactDirectoryOpen(false); setActiveView("home"); }} style={{ background: "rgba(17, 24, 39, 0.32)", backdropFilter: "blur(2px)" }} />
          <ContactDirectoryDrawer onClose={() => { setIsContactDirectoryOpen(false); setActiveView("home"); }} />
        </>
      )}

      <div className="pb-20 pt-16 md:pb-0 md:pl-[180px] md:pt-0">
        <main className={`mx-auto w-full px-4 py-8 sm:px-6 md:py-10 ${activeView === "home" ? "max-w-[1200px]" : "max-w-[1120px] pb-28"}`}>
          {activeView === "home" ? (
            <HomePage
              query={query}
              onQueryChange={setQuery}
              onSearch={(value) => void handleSearch(value)}
              onClear={handleClear}
              isSearching={isSearching}
              hasSearched={hasSearched}
              response={searchResponse}
              error={searchError}
              onOpenSituations={() => navigate("situations")}
              onOpenWork={() => navigate("work")}
              onOpenEmergency={openEmergency}
              onOpenContacts={() => navigate("contacts")}
              onOpenManual={() => navigate("manual")}
              updates={recentUpdates}
              isUpdatesLoading={!manualCatalog && !manualCatalogError}
              onOpenUpdate={openUpdate}
              canEdit={user.role === "admin"}
              onEditManualEntry={(entryId) => openAdminEditor("complaints", entryId)}
            />
          ) : activeView === "situations" ? (
            <SituationPage focusEmergency={focusEmergency} onSelect={(value) => void handleSearch(value)} />
          ) : activeView === "work" ? (
            <WorkGuidePage
              guides={quickGuides}
              source={quickGuideSource}
              error={guideError}
              onOpenManual={() => navigate("manual")}
              requestedGuideId={requestedGuideId}
              canEdit={user.role === "admin"}
              onEditGuide={(guideId) => openAdminEditor("guides", guideId)}
            />
          ) : activeView === "manual" ? (
            manualCatalog
              ? <ManualCatalogView
                  key={requestedManualEntryId ?? "manual"}
                  catalog={manualCatalog}
                  requestedEntryId={requestedManualEntryId}
                  canEdit={user.role === "admin"}
                  onEditEntry={(entryId) => openAdminEditor("complaints", entryId)}
                />
              : <LoadingState error={manualCatalogError} label="전체 매뉴얼을 불러오고 있습니다." />
          ) : activeView === "admin" && user.role === "admin" ? (
            <AdminPage
              key={`${requestedAdminEdit?.tab ?? "default"}-${requestedAdminEdit?.itemId ?? "default"}`}
              onGuidesChanged={() => { void loadQuickGuides(); }}
              onManualChanged={() => { void loadManualCatalog(); }}
              initialTab={requestedAdminEdit?.tab}
              initialGuideId={requestedAdminEdit?.tab === "guides" ? requestedAdminEdit.itemId : undefined}
              initialManualEntryId={requestedAdminEdit?.tab === "complaints" ? requestedAdminEdit.itemId : undefined}
            />
          ) : (
            <HomePage
              query={query}
              onQueryChange={setQuery}
              onSearch={(value) => void handleSearch(value)}
              onClear={handleClear}
              isSearching={isSearching}
              hasSearched={hasSearched}
              response={searchResponse}
              error={searchError}
              onOpenSituations={() => navigate("situations")}
              onOpenWork={() => navigate("work")}
              onOpenEmergency={openEmergency}
              onOpenContacts={() => navigate("contacts")}
              onOpenManual={() => navigate("manual")}
              updates={recentUpdates}
              isUpdatesLoading={!manualCatalog && !manualCatalogError}
              onOpenUpdate={openUpdate}
              canEdit={user.role === "admin"}
              onEditManualEntry={(entryId) => openAdminEditor("complaints", entryId)}
            />
          )}
        </main>

        {activeView !== "home" && activeView !== "contacts" && (
          <form onSubmit={(event) => { event.preventDefault(); void handleSearch(); }} className="pointer-events-none fixed inset-x-0 bottom-16 z-30 px-4 md:bottom-4 md:left-[180px]" role="search">
            <div className="pointer-events-auto mx-auto flex w-full max-w-[560px] items-center gap-2 rounded-2xl border-2 bg-white p-2" style={{ borderColor: "var(--brand-green)" }}>
              <Search className="ml-2 h-4.5 w-4.5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
              <input type="search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="민원 내용을 바로 검색하세요" aria-label="빠른 민원 검색" className="min-w-0 flex-1 bg-transparent px-1 py-2.5 text-sm outline-none" />
              <button type="submit" disabled={isSearching || !query.trim()} aria-label="민원 검색" className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl text-white disabled:opacity-40" style={{ background: "var(--brand-green)" }}>
                {isSearching ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-5 w-5" />}
              </button>
            </div>
          </form>
        )}

        <footer className="mx-auto max-w-[1120px] px-5 pb-8 text-xs" style={{ color: "var(--muted-foreground)" }}>
          안내 결과는 공식 매뉴얼과 과거 당직민원 이첩 사례를 구분해 표시합니다.
        </footer>
      </div>
    </div>
  );
}

function LoadingState({ error, label }: { error: string; label: string }) {
  return (
    <div role={error ? "alert" : "status"} className="flex min-h-[240px] items-center justify-center border-y px-6 text-center text-sm" style={{ borderColor: "var(--border)", color: error ? "var(--brand-red-dark)" : "var(--muted-foreground)" }}>
      {error || <span className="inline-flex items-center gap-3"><Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} />{label}</span>}
    </div>
  );
}
