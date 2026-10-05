import {
  ArrowRight,
  Bell,
  BriefcaseBusiness,
  ChevronRight,
  Loader2,
  Search,
  Siren,
  X,
} from "lucide-react";
import type { SearchResponse } from "../api/search";
import { SearchResults } from "../components/SearchResults";

export const FREQUENT_COMPLAINTS = [
  { label: "불법 주정차", query: "불법 주차" },
  { label: "동물 사체", query: "동물 사체" },
  { label: "가로등 고장", query: "가로등 고장" },
  { label: "불법 현수막", query: "불법 현수막" },
  { label: "도로 시설물 파손", query: "도로 시설물 파손" },
  { label: "공원 시설물 파손", query: "공원 시설물 파손" },
];

export interface HomeUpdate {
  id: string;
  title: string;
  kind: "추가" | "수정";
  date: string;
  target: "work" | "manual";
  itemId: string;
}

interface HomePageProps {
  query: string;
  onQueryChange: (value: string) => void;
  onSearch: (query?: string) => void;
  onClear: () => void;
  isSearching: boolean;
  hasSearched: boolean;
  response: SearchResponse | null;
  error: string;
  onOpenSituations: () => void;
  onOpenWork: () => void;
  onOpenEmergency: () => void;
  onOpenContacts: () => void;
  onOpenManual: () => void;
  updates: HomeUpdate[];
  isUpdatesLoading: boolean;
  onOpenUpdate: (update: HomeUpdate) => void;
}

export function HomePage({
  query,
  onQueryChange,
  onSearch,
  onClear,
  isSearching,
  hasSearched,
  response,
  error,
  onOpenSituations,
  onOpenWork,
  onOpenEmergency,
  onOpenContacts,
  onOpenManual,
  updates,
  isUpdatesLoading,
  onOpenUpdate,
}: HomePageProps) {
  return (
    <div>
      <section className="mx-auto max-w-[940px] pt-3 sm:pt-7">
        <p className="text-sm font-bold" style={{ color: "var(--brand-green)" }}>유성구 당직 민원 대응</p>
        <h1 className="mt-2 text-3xl font-extrabold tracking-tight sm:text-4xl">당직 민원, 바로 찾아보세요</h1>
        <p className="mt-3 text-base leading-7" style={{ color: "var(--muted-foreground)" }}>
          민원인이 말한 내용을 그대로 입력하면 지금 해야 할 일과 담당 부서, 안내 문구를 함께 보여드립니다.
        </p>

        <form
          className="mt-6 rounded-[26px] border-2 bg-white p-2 sm:p-3"
          style={{ borderColor: "var(--brand-green)" }}
          onSubmit={(event) => {
            event.preventDefault();
            onSearch();
          }}
          role="search"
        >
          <div className="flex items-stretch gap-2">
            <label className="flex min-w-0 flex-1 items-center rounded-full px-3 sm:px-5">
              <Search className="mr-3 h-5 w-5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
              <span className="sr-only">민원 내용</span>
              <input
                type="text"
                enterKeyHint="search"
                value={query}
                onChange={(event) => onQueryChange(event.target.value)}
                placeholder="예: 밤 11시에 공사장 소음이 너무 심해요"
                className="min-w-0 flex-1 bg-transparent py-3.5 text-base outline-none sm:text-lg"
              />
              {query && (
                <button type="button" onClick={onClear} aria-label="검색어 지우기" className="rounded-lg p-2" style={{ color: "var(--muted-foreground)" }}>
                  <X className="h-4 w-4" />
                </button>
              )}
            </label>
            <button type="submit" disabled={isSearching || !query.trim()} className="inline-flex min-w-[52px] items-center justify-center gap-2 rounded-[20px] px-4 text-sm font-extrabold text-white disabled:cursor-not-allowed disabled:opacity-40 sm:px-6" style={{ background: "var(--brand-green)" }}>
              {isSearching ? <Loader2 className="h-5 w-5 animate-spin" /> : <ArrowRight className="h-5 w-5" />}
              <span className="hidden sm:inline">대응 찾기</span>
            </button>
          </div>
        </form>

        {!hasSearched && !isSearching && (
          <div className="mt-4">
            <p className="mb-2 text-sm font-bold" style={{ color: "var(--muted-foreground)" }}>
              자주 들어오는 민원
            </p>
            <div className="flex flex-wrap gap-2">
              {FREQUENT_COMPLAINTS.map((complaint) => (
                <button key={complaint.label} type="button" onClick={() => onSearch(complaint.query)} className="rounded-full border bg-white px-4 py-2 text-sm font-semibold transition-colors hover:border-[#5AA2D2] hover:text-[#02558E]" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
                  {complaint.label}
                </button>
              ))}
            </div>
          </div>
        )}

        {!hasSearched && !isSearching && (
          <section className="mt-8 border-y bg-white" style={{ borderColor: "var(--border)" }} aria-labelledby="recent-updates-title">
            <header className="flex items-center justify-between gap-3 px-1 py-4 sm:px-3">
              <div className="flex items-center gap-2.5">
                <Bell className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
                <h2 id="recent-updates-title" className="text-base font-extrabold">최근 업데이트</h2>
              </div>
              {updates.length > 0 && (
                <span className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>최근 {updates.length}건</span>
              )}
            </header>

            {isUpdatesLoading ? (
              <div className="flex items-center gap-2 border-t px-1 py-4 text-sm sm:px-3" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
                <Loader2 className="h-4 w-4 animate-spin" /> 업데이트를 확인하고 있습니다.
              </div>
            ) : updates.length > 0 ? (
              <div className="divide-y border-t" style={{ borderColor: "var(--border)" }}>
                {updates.map((update) => (
                  <button
                    key={update.id}
                    type="button"
                    onClick={() => onOpenUpdate(update)}
                    className="flex w-full items-center gap-3 px-1 py-3.5 text-left transition-colors hover:bg-[#F7FAFC] sm:px-3"
                  >
                    <span
                      className="rounded-full border px-2.5 py-1 text-xs font-extrabold"
                      style={{
                        borderColor: update.kind === "추가" ? "var(--brand-red)" : "var(--brand-green)",
                        color: update.kind === "추가" ? "var(--brand-red-dark)" : "var(--brand-green-dark)",
                      }}
                    >
                      {update.kind}
                    </span>
                    <span className="min-w-0 flex-1 truncate text-sm font-semibold">{update.title}</span>
                    {update.date && (
                      <time className="hidden flex-shrink-0 text-xs sm:block" style={{ color: "var(--muted-foreground)" }}>
                        {update.date.slice(0, 10)}
                      </time>
                    )}
                    <ChevronRight className="h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
                  </button>
                ))}
              </div>
            ) : (
              <p className="border-t px-1 py-4 text-sm sm:px-3" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
                새로 등록된 공지가 없습니다. 관리자가 내용을 추가하거나 수정하면 이곳에 표시됩니다.
              </p>
            )}
          </section>
        )}
      </section>

      {error && (
        <div role="alert" className="mx-auto mt-5 max-w-[940px] border-l-4 px-4 py-3 text-sm" style={{ background: "#FFF5F3", borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
          {error}
        </div>
      )}

      {isSearching && (
        <div className="flex items-center justify-center gap-3 py-20 text-sm" style={{ color: "var(--muted-foreground)" }}>
          <Loader2 className="h-5 w-5 animate-spin" style={{ color: "var(--brand-green)" }} /> 대응 절차를 확인하고 있습니다.
        </div>
      )}

      {hasSearched && !isSearching && (
        <section className="mx-auto mt-7 max-w-[940px]">
          <div className="mb-3 flex items-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
            <span>입력한 민원</span><span>·</span><strong style={{ color: "var(--foreground)" }}>{response?.query}</strong>
          </div>
          <SearchResults
            results={response?.results ?? []}
            emptyMessage={response?.message}
            onRetry={() => onClear()}
            onOpenContacts={onOpenContacts}
            onOpenManual={onOpenManual}
          />
        </section>
      )}

      {!hasSearched && !isSearching && (
        <section className="mx-auto mt-12 max-w-[940px] border-y" style={{ borderColor: "var(--border)" }}>
          <div className="grid md:grid-cols-3">
            <HomeLink title="자주 찾는 상황" description="유형을 직접 골라 대응 확인" icon={Search} onClick={onOpenSituations} />
            <HomeLink title="근무 안내 바로가기" description="타임라인·일지·기본업무" icon={BriefcaseBusiness} onClick={onOpenWork} bordered />
            <HomeLink title="긴급 상황 바로가기" description="화재·침수·산불·붕괴" icon={Siren} onClick={onOpenEmergency} danger />
          </div>
        </section>
      )}
    </div>
  );
}

function HomeLink({
  title,
  description,
  icon: Icon,
  onClick,
  bordered = false,
  danger = false,
}: {
  title: string;
  description: string;
  icon: typeof Search;
  onClick: () => void;
  bordered?: boolean;
  danger?: boolean;
}) {
  return (
    <button type="button" onClick={onClick} className={`flex items-center gap-4 px-4 py-6 text-left transition-colors hover:bg-[#F7FAFC] ${bordered ? "border-y md:border-x md:border-y-0" : ""}`} style={{ borderColor: "var(--border)" }}>
      <Icon className="h-6 w-6 flex-shrink-0" style={{ color: danger ? "var(--brand-red)" : "var(--brand-green)" }} />
      <span className="min-w-0 flex-1">
        <strong className="block text-base">{title}</strong>
        <span className="mt-1 block text-sm" style={{ color: "var(--muted-foreground)" }}>{description}</span>
      </span>
      <ArrowRight className="h-4 w-4 flex-shrink-0" style={{ color: danger ? "var(--brand-red)" : "var(--brand-green)" }} />
    </button>
  );
}
