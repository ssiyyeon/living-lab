import { useMemo, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  ChevronDown,
  CircleCheck,
  Search,
} from "lucide-react";
import type { ManualCatalogEntry, ManualCatalogResponse } from "../api/search";

const GROUP_ORDER = [
  "당직근무자 준수사항",
  "청사 보안·시건",
  "비상 발령·소집",
  "재난유형별 대응",
  "민원유형별 대응",
  "부록",
];

function formatPages(pages: number[]) {
  if (pages.length === 0) return "쪽수 확인 필요";
  if (pages.length === 1) return `${pages[0]}쪽`;
  return `${Math.min(...pages)}-${Math.max(...pages)}쪽`;
}

function StructuredCaseContent({ entry }: { entry: ManualCatalogEntry }) {
  return (
    <div className="space-y-6">
      {entry.departments.length > 0 && (
        <section>
          <h3 className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>담당 부서</h3>
          <p className="mt-2 text-sm font-semibold">{entry.departments.join(" · ")}</p>
        </section>
      )}

      {(entry.intakeQuestions.length > 0 || entry.immediateActions.length > 0) && (
        <div className="grid gap-6 sm:grid-cols-2">
          {entry.intakeQuestions.length > 0 && (
            <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
              <h3 className="text-sm font-bold">먼저 확인</h3>
              <ol className="mt-3 space-y-2 text-sm leading-6">
                {entry.intakeQuestions.map((question, index) => (
                  <li key={question} className="flex gap-2.5">
                    <span className="font-bold" style={{ color: "var(--brand-green)" }}>{index + 1}.</span>
                    <span>{question}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {entry.immediateActions.length > 0 && (
            <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
              <h3 className="text-sm font-bold">즉시 조치</h3>
              <ul className="mt-3 space-y-2 text-sm leading-6">
                {entry.immediateActions.map((action) => (
                  <li key={action} className="flex gap-2.5">
                    <CircleCheck className="mt-1 h-4 w-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                    <span>{action}</span>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </div>
      )}

      {entry.decisionBranches.length > 0 && (
        <section>
          <h3 className="text-sm font-bold">상황별 처리</h3>
          <div className="mt-3 divide-y border-y" style={{ borderColor: "var(--border)" }}>
            {entry.decisionBranches.map((branch) => (
              <div key={branch.condition} className="py-4" style={{ borderColor: "var(--border)" }}>
                <p className="text-sm font-bold" style={{ color: "var(--brand-green-dark)" }}>{branch.condition}</p>
                <ul className="mt-2 space-y-1.5 text-sm leading-6">
                  {branch.actions.map((action) => <li key={action}>• {action}</li>)}
                </ul>
                {branch.response && (
                  <p className="mt-3 border-l-2 pl-3 text-sm leading-6" style={{ borderColor: "var(--brand-green)", color: "var(--muted-foreground)" }}>
                    안내 문구 · {branch.response}
                  </p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {entry.escalationRules.length > 0 && (
        <section className="border-t pt-4" style={{ borderColor: "var(--border)" }}>
          <h3 className="text-sm font-bold">보고·상향 기준</h3>
          <ul className="mt-3 space-y-3 text-sm leading-6">
            {entry.escalationRules.map((rule) => (
              <li key={`${rule.condition}-${rule.action}`}>
                <strong>{rule.condition}</strong>
                <span className="mt-1 block" style={{ color: "var(--muted-foreground)" }}>{rule.action}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {entry.responseScripts.length > 0 && (
        <section>
          <h3 className="text-sm font-bold">민원인 안내 문구</h3>
          <div className="mt-3 space-y-3">
            {entry.responseScripts.map((script) => (
              <p
                key={script}
                className="border-l-2 pl-4 text-sm leading-6"
                style={{ borderColor: "var(--brand-green)", color: "var(--muted-foreground)" }}
              >
                {script}
              </p>
            ))}
          </div>
        </section>
      )}

      {entry.cautions.length > 0 && (
        <section className="border-l-2 pl-4" style={{ borderColor: "var(--brand-red)" }}>
          <h3 className="flex items-center gap-2 text-sm font-bold" style={{ color: "var(--brand-red-dark)" }}>
            <AlertTriangle className="h-4 w-4" />
            주의사항
          </h3>
          <ul className="mt-2 space-y-1.5 text-sm leading-6">
            {entry.cautions.map((caution) => <li key={caution}>• {caution}</li>)}
          </ul>
        </section>
      )}
    </div>
  );
}

export function ManualCatalogView({ catalog }: { catalog: ManualCatalogResponse }) {
  const [activeGroup, setActiveGroup] = useState("전체");
  const [query, setQuery] = useState("");

  const groupCounts = useMemo(() => {
    const counts = new Map<string, number>();
    catalog.entries.forEach((entry) => counts.set(entry.group, (counts.get(entry.group) ?? 0) + 1));
    return counts;
  }, [catalog.entries]);

  const filteredEntries = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();

    return catalog.entries.filter((entry) => {
      if (activeGroup !== "전체" && entry.group !== activeGroup) return false;
      if (!normalizedQuery) return true;

      return [
        entry.title,
        entry.topic,
        entry.summary,
        entry.content,
        entry.breadcrumb.join(" "),
        entry.departments.join(" "),
      ].some((value) => value.toLowerCase().includes(normalizedQuery));
    });
  }, [activeGroup, catalog.entries, query]);

  const visibleGroups = GROUP_ORDER.filter((group) =>
    filteredEntries.some((entry) => entry.group === group),
  );

  return (
    <article>
      <header className="border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold" style={{ color: "var(--brand-green)" }}>공식 매뉴얼 전체보기</p>
            <h1 className="mt-2 text-2xl font-extrabold">전체 매뉴얼</h1>
            <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
              PDF 85쪽에서 정리한 일반 문서 40개와 상황별 대응 31개를 확인합니다.
            </p>
          </div>
          <span className="text-sm font-bold" style={{ color: "var(--brand-green-dark)" }}>{catalog.totalCount}개 문서</span>
        </div>

        <div className="mt-5 flex items-center gap-3 rounded-full border bg-white px-4" style={{ borderColor: "var(--border)" }}>
          <Search className="h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
          <input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="매뉴얼 제목, 담당 부서 또는 내용 검색"
            aria-label="전체 매뉴얼 검색"
            className="min-w-0 flex-1 bg-transparent py-3 text-sm outline-none"
          />
        </div>

        <div className="mt-4 flex flex-wrap gap-x-5 gap-y-2">
          {["전체", ...GROUP_ORDER].map((group) => {
            const count = group === "전체" ? catalog.totalCount : (groupCounts.get(group) ?? 0);
            if (group !== "전체" && count === 0) return null;

            return (
              <button
                key={group}
                type="button"
                onClick={() => setActiveGroup(group)}
                className="border-b-2 py-1 text-xs font-bold transition-colors"
                style={{
                  borderColor: activeGroup === group ? "var(--brand-green)" : "transparent",
                  color: activeGroup === group ? "var(--brand-green-dark)" : "var(--muted-foreground)",
                }}
              >
                {group} {count}
              </button>
            );
          })}
        </div>
      </header>

      {visibleGroups.length === 0 ? (
        <p className="py-16 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>
          일치하는 매뉴얼 항목이 없습니다.
        </p>
      ) : (
        <div className="mt-8 space-y-10">
          {visibleGroups.map((group) => {
            const entries = filteredEntries.filter((entry) => entry.group === group);

            return (
              <section key={group}>
                <div className="mb-3 flex items-center justify-between">
                  <h2 className="text-base font-extrabold">{group}</h2>
                  <span className="text-xs" style={{ color: "var(--muted-foreground)" }}>{entries.length}개</span>
                </div>

                <div className="divide-y border-y" style={{ borderColor: "var(--border)" }}>
                  {entries.map((entry) => (
                    <details key={entry.id} className="group" style={{ borderColor: "var(--border)" }}>
                      <summary className="flex cursor-pointer list-none items-center gap-4 py-4">
                        <BookOpen className="h-4.5 w-4.5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                        <span className="min-w-0 flex-1">
                          <strong className="block text-sm">{entry.title}</strong>
                          <span className="mt-1 block text-xs" style={{ color: "var(--muted-foreground)" }}>
                            {entry.topic} · {formatPages(entry.sourcePages)}
                          </span>
                        </span>
                        <ChevronDown className="h-4 w-4 flex-shrink-0 transition-transform group-open:rotate-180" style={{ color: "var(--muted-foreground)" }} />
                      </summary>

                      <div className="pb-6 pl-8 sm:pl-9">
                        {entry.breadcrumb.length > 0 && (
                          <p className="text-[11px] leading-5" style={{ color: "var(--muted-foreground)" }}>
                            {entry.breadcrumb.join(" › ")}
                          </p>
                        )}
                        {entry.entryType === "case" && entry.summary && (
                          <p className="mt-3 text-sm leading-6">{entry.summary}</p>
                        )}

                        <div className="mt-5">
                          {entry.entryType === "case" ? (
                            <StructuredCaseContent entry={entry} />
                          ) : (
                            <div className="whitespace-pre-line text-sm leading-7">{entry.content}</div>
                          )}
                        </div>

                        {entry.entryType === "case" && entry.content && (
                          <details className="mt-6 border-t pt-4" style={{ borderColor: "var(--border)" }}>
                            <summary className="cursor-pointer text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>
                              원문 데이터 보기 · 개인정보 제외
                            </summary>
                            <div className="mt-4 whitespace-pre-line text-xs leading-6" style={{ color: "var(--muted-foreground)" }}>
                              {entry.content}
                            </div>
                          </details>
                        )}
                      </div>
                    </details>
                  ))}
                </div>
              </section>
            );
          })}
        </div>
      )}

      <footer className="mt-10 border-t pt-4 text-xs leading-5" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
        {catalog.source} · 표지와 목차를 제외한 전체 실무 페이지를 분류해 표시합니다.
      </footer>
    </article>
  );
}
