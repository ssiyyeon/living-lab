import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  MessageSquareText,
  PhoneCall,
} from "lucide-react";
import type { SearchResult } from "../api/search";

interface SearchResultsProps {
  results: SearchResult[];
  emptyMessage?: string;
}

export function SearchResults({ results, emptyMessage }: SearchResultsProps) {
  const result = results[0];
  const [activeBranch, setActiveBranch] = useState(0);

  useEffect(() => {
    setActiveBranch(0);
  }, [result?.id]);

  if (!result) {
    return (
      <div
        className="rounded-2xl border bg-white px-6 py-12 text-center"
        style={{ borderColor: "var(--border)" }}
      >
        <p className="font-semibold">바로 안내할 대응 절차를 찾지 못했어요.</p>
        <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
          {emptyMessage ?? "발생 위치와 현재 상황을 조금 더 구체적으로 입력해 주세요."}
        </p>
      </div>
    );
  }

  const hasActionGuide =
    result.intakeQuestions.length > 0 || result.immediateActions.length > 0;
  const selectedBranch = result.decisionBranches[activeBranch];
  const isOfficial = result.evidenceLevel === "official_manual";
  const evidenceLabel = isOfficial ? "공식 매뉴얼" : "과거 처리사례 기반";
  const departmentContacts = result.departmentContacts ?? [];

  return (
    <article
      className="overflow-hidden rounded-2xl border bg-white"
      style={{ borderColor: "var(--border)" }}
    >
      <div className="border-b px-6 py-6 sm:px-8" style={{ borderColor: "var(--border)" }}>
        <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
          <div className="min-w-0">
            <span
              className="inline-flex rounded-full px-3 py-1 text-xs font-bold"
              style={{
                background: isOfficial ? "var(--brand-green-light)" : "#FFFFFF",
                color: isOfficial ? "var(--brand-green-dark)" : "var(--foreground)",
                border: `1px solid ${isOfficial ? "var(--brand-green)" : "var(--border)"}`,
              }}
            >
              {evidenceLabel}
            </span>
            <h2 className="mt-3 text-2xl font-extrabold">{result.civilType}</h2>
            <p className="mt-3 max-w-2xl text-sm leading-7" style={{ color: "#4B5563" }}>
              {result.paragraphSummary}
            </p>
          </div>

          <div
            className="min-w-[240px] border-l-2 px-4 py-2 sm:max-w-[290px]"
            style={{ borderColor: "var(--brand-green)" }}
          >
            <div className="flex items-center gap-3">
              <Building2 className="h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
              <div>
                <p className="text-xs" style={{ color: "var(--muted-foreground)" }}>이첩·확인 부서</p>
                <p className="mt-0.5 text-sm font-bold">{result.department}</p>
              </div>
            </div>

            {departmentContacts.length > 0 && (
              <div className="mt-3 space-y-3 border-t pt-3" style={{ borderColor: "var(--border)" }}>
                {departmentContacts.map((contact) => (
                  <div key={`${contact.department}-${contact.phone}`}>
                    <p className="text-[11px] font-semibold" style={{ color: "var(--muted-foreground)" }}>
                      {contact.label}
                    </p>
                    <a
                      href={`tel:${contact.phone.replace(/[^\d+]/g, "")}`}
                      className="mt-1 inline-flex items-center gap-2 text-sm font-extrabold"
                      style={{ color: "var(--brand-green-dark)" }}
                      aria-label={`${contact.label} ${contact.phone} 전화`}
                    >
                      <PhoneCall className="h-4 w-4" />
                      {contact.phone}
                    </a>
                    {contact.note && (
                      <p className="mt-1 text-[11px] leading-4" style={{ color: "var(--muted-foreground)" }}>
                        {contact.note}
                      </p>
                    )}
                  </div>
                ))}
                <p className="text-[10px] leading-4" style={{ color: "var(--muted-foreground)" }}>
                  공개 업무번호 · 야간 비상연락은 당직실 비상연락망 확인
                </p>
              </div>
            )}
          </div>
        </div>
      </div>

      {hasActionGuide ? (
        <div className="space-y-6 px-6 py-7 sm:px-8">
          <div className="grid gap-4 md:grid-cols-2">
            <section className="rounded-xl border p-5" style={{ borderColor: "var(--border)" }}>
              <div className="mb-4 flex items-center gap-2">
                <ClipboardList className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
                <h3 className="font-bold">먼저 확인하세요</h3>
              </div>
              <ol className="space-y-3 text-sm leading-6">
                {result.intakeQuestions.map((question, index) => (
                  <li key={question} className="flex gap-3">
                    <span className="font-bold" style={{ color: "var(--brand-green)" }}>{index + 1}</span>
                    <span>{question}</span>
                  </li>
                ))}
              </ol>
            </section>

            <section className="rounded-xl border-l-2 bg-white p-5" style={{ borderColor: "var(--brand-green)" }}>
              <div className="mb-4 flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
                <h3 className="font-bold" style={{ color: "var(--brand-green-dark)" }}>지금 할 일</h3>
              </div>
              <ul className="space-y-3 text-sm leading-6" style={{ color: "var(--brand-green-dark)" }}>
                {result.immediateActions.map((action) => (
                  <li key={action} className="flex gap-2">
                    <span>•</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </section>
          </div>

          {result.decisionBranches.length > 0 && selectedBranch && (
            <section className="border-t pt-6" style={{ borderColor: "var(--border)" }}>
              <h3 className="font-bold">상황에 맞는 항목을 선택하세요</h3>
              <div className="mt-4 grid gap-5 md:grid-cols-[230px_1fr]">
                <div className="space-y-2">
                  {result.decisionBranches.map((branch, index) => {
                    const isActive = activeBranch === index;
                    return (
                      <button
                        type="button"
                        key={branch.condition}
                        onClick={() => setActiveBranch(index)}
                        className="w-full rounded-lg border px-4 py-3 text-left text-sm font-semibold transition-colors"
                        style={{
                          background: isActive ? "var(--brand-green)" : "#FFFFFF",
                          color: isActive ? "#fff" : "#4B5563",
                          borderColor: isActive ? "var(--brand-green)" : "var(--border)",
                        }}
                      >
                        {branch.condition}
                      </button>
                    );
                  })}
                </div>

                <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)" }}>
                  <p className="text-base font-bold">{selectedBranch.condition}</p>
                  <ul className="mt-4 space-y-3 text-sm leading-6">
                    {selectedBranch.actions.map((action) => (
                      <li key={action} className="flex gap-2">
                        <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                        <span>{action}</span>
                      </li>
                    ))}
                  </ul>
                  {selectedBranch.response && (
                    <div className="mt-5 border-l-2 px-4 py-2" style={{ borderColor: "var(--brand-green)" }}>
                      <p className="mb-1 text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>
                        민원인 안내
                      </p>
                      <p className="text-sm leading-6">“{selectedBranch.response}”</p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {result.responseScripts.length > 0 && (
            <section className="rounded-xl border p-5" style={{ borderColor: "var(--brand-green)", background: "#FFFFFF" }}>
              <div className="flex gap-3">
                <MessageSquareText className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                <div>
                  <h3 className="font-bold">이렇게 안내하세요</h3>
                  {result.responseScripts.map((script) => (
                    <p key={script} className="mt-2 text-sm leading-7">“{script}”</p>
                  ))}
                </div>
              </div>
            </section>
          )}

          {(result.escalationRules.length > 0 || result.cautions.length > 0) && (
            <section className="rounded-xl border p-5" style={{ background: "var(--brand-red-light)", borderColor: "var(--brand-red)" }}>
              <div className="flex gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-red)" }} />
                <div>
                  <h3 className="font-bold" style={{ color: "var(--brand-red-dark)" }}>주의할 점</h3>
                  <div className="mt-2 space-y-2 text-sm leading-6" style={{ color: "var(--brand-red-dark)" }}>
                    {result.escalationRules.map((rule) => (
                      <p key={rule.condition}><strong>{rule.condition}:</strong> {rule.action}</p>
                    ))}
                    {result.cautions.map((caution) => <p key={caution}>• {caution}</p>)}
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>
      ) : (
        <div className="px-6 py-7 sm:px-8">
          <h3 className="font-bold">처리 방법</h3>
          <p className="mt-3 text-sm leading-7">{result.guidance}</p>
        </div>
      )}

      <details className="group border-t px-6 py-4 text-sm sm:px-8" style={{ borderColor: "var(--border)" }}>
        <summary className="flex cursor-pointer list-none items-center gap-2 font-semibold" style={{ color: "var(--muted-foreground)" }}>
          <BookOpen className="h-4 w-4" />
          근거 확인
          <ChevronDown className="ml-auto h-4 w-4 transition-transform group-open:rotate-180" />
        </summary>
        <div className="mt-3 space-y-2 pl-6 text-xs leading-6" style={{ color: "var(--muted-foreground)" }}>
          <p>{result.sourceReference || result.documentName}</p>
          {result.note && <p>{result.note}</p>}
        </div>
      </details>
    </article>
  );
}
