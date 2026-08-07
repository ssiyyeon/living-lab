import {
  Building2,
  BookOpen,
  FileQuestion,
  Star,
  Bell,
  FileText,
  LogOut,
  User,
} from "lucide-react";

const categories = [
  { id: "dept", label: "부서 정보", icon: Building2 },
  { id: "manual", label: "당직 매뉴얼", icon: BookOpen },
  { id: "civil", label: "민원 유형", icon: FileQuestion },
  { id: "frequent", label: "자주 찾는 자료", icon: Star },
  { id: "notice", label: "공지사항", icon: Bell },
  { id: "reference", label: "참고 문서", icon: FileText },
];

interface SidebarProps {
  activeCategory: string;
  onCategoryChange: (id: string) => void;
  logoSrc?: string;
}

export function Sidebar({ activeCategory, onCategoryChange, logoSrc }: SidebarProps) {
  return (
    <aside
      className="flex flex-col h-full"
      style={{
        background: "var(--sidebar)",
        color: "var(--sidebar-foreground)",
      }}
    >
      {/* Logo */}
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
        <p style={{ color: "var(--muted-foreground)", fontSize: "12px", marginTop: "7px" }}>당직 근무 지원 시스템</p>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 overflow-y-auto">
        <p style={{ color: "var(--muted-foreground)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", marginBottom: "10px", paddingLeft: "12px" }}>
          자료 탐색
        </p>
        <ul className="space-y-1.5">
          {categories.map((cat) => {
            const Icon = cat.icon;
            const isActive = activeCategory === cat.id;
            return (
              <li key={cat.id}>
                <button
                  onClick={() => onCategoryChange(cat.id)}
                  className="w-full flex items-center gap-3 px-4 py-3.5 transition-all duration-150"
                  style={{
                    borderRadius: "12px",
                    background: isActive ? "var(--brand-green-light)" : "transparent",
                    color: isActive ? "var(--brand-green-dark)" : "var(--muted-foreground)",
                    fontFamily: "var(--font-family)",
                    fontSize: "14px",
                    fontWeight: isActive ? 600 : 400,
                  }}
                >
                  <Icon
                    className="w-5 h-5 flex-shrink-0"
                    style={{ color: isActive ? "var(--brand-green)" : "var(--muted-foreground)", opacity: isActive ? 1 : 0.7 }}
                  />
                  <span className="flex-1 text-left">{cat.label}</span>
                </button>
              </li>
            );
          })}
        </ul>

        {/* Quick Links */}
        <div className="mt-8">
          <p style={{ color: "var(--muted-foreground)", fontSize: "11px", fontWeight: 600, letterSpacing: "0.08em", marginBottom: "10px", paddingLeft: "12px" }}>
            빠른 링크
          </p>
          <div className="space-y-1.5">
            {["비상 연락망", "야간 처리 절차", "민원 접수 양식"].map((link) => (
              <button
                key={link}
                className="w-full text-left px-4 py-3 transition-colors duration-150"
                style={{
                  borderRadius: "12px",
                  color: "var(--muted-foreground)",
                  fontSize: "13px",
                  fontFamily: "var(--font-family)",
                }}
              >
                <span style={{ opacity: 0.35, marginRight: "8px" }}>↗</span>
                {link}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* User info */}
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
          <div className="flex-1 min-w-0">
            <p style={{ color: "var(--brand-green-dark)", fontSize: "14px", fontWeight: 600 }}>당직 근무자</p>
            <p style={{ color: "var(--muted-foreground)", fontSize: "12px", marginTop: "2px" }}>당직 근무 중</p>
          </div>
          <button title="로그아웃">
            <LogOut className="w-4 h-4" style={{ color: "var(--muted-foreground)" }} />
          </button>
        </div>
      </div>
    </aside>
  );
}
