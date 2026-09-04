import { BookOpen, User } from "lucide-react";

interface SidebarProps {
  logoSrc?: string;
}

export function Sidebar({ logoSrc }: SidebarProps) {
  return (
    <aside
      className="flex flex-col h-full"
      style={{
        background: "var(--sidebar)",
        color: "var(--sidebar-foreground)",
      }}
    >
      <div className="px-6 py-6 border-b" style={{ borderColor: "var(--sidebar-border)" }}>
        {logoSrc ? (
          <img
            src={logoSrc}
            alt="유성구 로고"
            style={{ height: "66px" }}
            className="object-contain"
          />
        ) : (
          <p style={{ color: "var(--foreground)", fontWeight: 700, fontSize: "16px" }}>유성구청</p>
        )}
        <p style={{ color: "var(--muted-foreground)", fontSize: "12px", marginTop: "7px" }}>
          당직 근무 지원 시스템
        </p>
      </div>

      <nav className="flex-1 px-4 py-6">
        <p style={{ color: "var(--muted-foreground)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", marginBottom: "10px", paddingLeft: "12px" }}>
          업무
        </p>
        <div
          className="flex items-center gap-3 px-4 py-3.5"
          style={{
            borderRadius: "12px",
            background: "var(--brand-green-light)",
            color: "var(--brand-green-dark)",
            fontSize: "14px",
            fontWeight: 700,
          }}
        >
          <BookOpen className="w-5 h-5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
          <span>민원 대응 검색</span>
        </div>
      </nav>

      <div className="px-4 py-5 border-t" style={{ borderColor: "var(--sidebar-border)" }}>
        <div
          className="flex items-center gap-3 px-4 py-4"
          style={{ borderRadius: "14px", background: "var(--brand-green-light)" }}
        >
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: "var(--muted)" }}
          >
            <User className="w-5 h-5" style={{ color: "var(--muted-foreground)" }} />
          </div>
          <div className="min-w-0">
            <p style={{ color: "var(--brand-green-dark)", fontSize: "14px", fontWeight: 700 }}>
              당직 근무자
            </p>
            <p style={{ color: "var(--muted-foreground)", fontSize: "12px", marginTop: "2px" }}>
              민원 대응 지원
            </p>
          </div>
        </div>
      </div>
    </aside>
  );
}
