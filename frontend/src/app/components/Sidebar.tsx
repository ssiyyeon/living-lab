import {
  BookOpen,
  BookUser,
  BriefcaseBusiness,
  House,
  LogOut,
  MessagesSquare,
  Moon,
  Settings,
  Siren,
} from "lucide-react";
import type { AuthUser } from "../api/search";

export type PrimaryView = "home" | "situations" | "work" | "contacts" | "manual" | "admin";

interface SidebarProps {
  logoSrc: string;
  user: AuthUser;
  activeView: PrimaryView;
  onNavigate: (view: PrimaryView) => void;
  onOpenQuickSearch: () => void;
  onLogout: () => void;
}

const BASE_ITEMS = [
  { id: "home" as const, label: "홈 / 민원 대응", shortLabel: "홈", icon: House },
  { id: "situations" as const, label: "상황별 대응", shortLabel: "상황별", icon: Siren },
  { id: "work" as const, label: "근무 안내", shortLabel: "근무", icon: BriefcaseBusiness },
  { id: "contacts" as const, label: "연락처", shortLabel: "연락처", icon: BookUser },
  { id: "manual" as const, label: "전체 매뉴얼", shortLabel: "매뉴얼", icon: BookOpen },
];

export function Sidebar({
  logoSrc,
  user,
  activeView,
  onNavigate,
  onOpenQuickSearch,
  onLogout,
}: SidebarProps) {
  const items = [
    ...BASE_ITEMS,
    ...(user.role === "admin"
      ? [{ id: "admin" as const, label: "관리자", shortLabel: "관리자", icon: Settings }]
      : []),
  ];

  return (
    <>
      <aside className="fixed inset-y-0 left-0 z-40 hidden w-[180px] bg-[var(--sidebar)] p-2 md:flex" aria-label="업무 메뉴">
        <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-[24px] border bg-white" style={{ borderColor: "var(--border)" }}>
          <button
            type="button"
            onClick={() => onNavigate("home")}
            aria-label="민원 대응 홈으로 이동"
            className="border-b px-4 py-6 text-center transition-colors hover:bg-[#F7FCFF] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#036EB8]"
            style={{ borderColor: "var(--border)" }}
          >
            <img src={logoSrc} alt="유성구 로고" className="mx-auto h-11 w-auto object-contain" />
            <span className="mt-3 block text-xs font-semibold" style={{ color: "var(--muted-foreground)" }}>당직 근무 지원</span>
          </button>

          <div className="min-h-0 flex-1 overflow-y-auto px-3 py-4">
            <p className="mb-2 px-3 text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>업무 메뉴</p>
            <nav className="space-y-1" aria-label="주요 화면">
              {items.map(({ id, label, icon: Icon }) => {
                const isActive = activeView === id;
                return (
                  <button
                    key={id}
                    type="button"
                    onClick={() => onNavigate(id)}
                    aria-current={isActive ? "page" : undefined}
                    className="flex w-full items-center gap-2.5 rounded-xl px-3 py-3 text-left text-sm font-bold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]"
                    style={{ background: isActive ? "#E7F0FC" : "transparent", color: isActive ? "#0B4DA2" : "var(--muted-foreground)" }}
                  >
                    <Icon className="h-[18px] w-[18px] flex-shrink-0" />
                    <span>{label}</span>
                  </button>
                );
              })}
            </nav>

            <div className="mt-4 border-t pt-4" style={{ borderColor: "var(--border)" }}>
              <p className="mb-2 px-3 text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>지원 도구</p>
              <button
                type="button"
                onClick={onOpenQuickSearch}
                className="flex w-full items-center gap-2.5 rounded-xl px-3 py-3 text-left text-sm font-bold transition-colors hover:bg-[#F2F7FC] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]"
                style={{ color: "var(--muted-foreground)" }}
              >
                <MessagesSquare className="h-[18px] w-[18px] flex-shrink-0" />
                <span>빠른 응대창</span>
              </button>
            </div>
          </div>

          <div className="border-t p-3" style={{ borderColor: "var(--border)" }}>
            <div className="rounded-2xl px-3 py-3" style={{ background: "#F2F6FC" }}>
              <div className="flex items-center gap-2 text-sm font-extrabold">
                <Moon className="h-4 w-4" style={{ color: "var(--brand-red)" }} />
                <span className="min-w-0 flex-1 truncate">{user.displayName}</span>
                <button type="button" onClick={onLogout} aria-label="로그아웃" title="로그아웃" className="rounded-lg p-1 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]" style={{ color: "var(--muted-foreground)" }}>
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
              <p className="mt-1 pl-6 text-xs" style={{ color: "var(--muted-foreground)" }}>{user.role === "admin" ? "관리자 · 야간당직" : "야간당직"}</p>
            </div>
          </div>
        </div>
      </aside>

      <header className="fixed inset-x-0 top-0 z-40 flex h-16 items-center justify-between border-b bg-white px-4 md:hidden" style={{ borderColor: "var(--border)" }}>
        <button type="button" onClick={() => onNavigate("home")} aria-label="홈으로 이동">
          <img src={logoSrc} alt="유성구 로고" className="h-8 w-auto" />
        </button>
        <button type="button" onClick={onOpenQuickSearch} className="inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-xs font-bold" style={{ borderColor: "var(--border)", color: "var(--brand-green-dark)" }}>
          <MessagesSquare className="h-4 w-4" /> 빠른 응대창
        </button>
      </header>

      <nav className="fixed inset-x-0 bottom-0 z-40 flex border-t bg-white px-1 md:hidden" style={{ borderColor: "var(--border)" }} aria-label="모바일 업무 메뉴">
        {items.map(({ id, shortLabel, icon: Icon }) => {
          const isActive = activeView === id;
          return (
            <button key={id} type="button" onClick={() => onNavigate(id)} aria-current={isActive ? "page" : undefined} className="flex min-w-0 flex-1 flex-col items-center gap-1 px-0.5 py-2.5 text-[11px] font-bold" style={{ color: isActive ? "var(--brand-green-dark)" : "var(--muted-foreground)" }}>
              <Icon className="h-5 w-5" /> {shortLabel}
            </button>
          );
        })}
      </nav>
    </>
  );
}
