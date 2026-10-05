import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BookOpen,
  Building2,
  CheckCircle2,
  ChevronDown,
  ClipboardList,
  MessageSquareText,
  Pencil,
  PhoneCall,
  RefreshCcw,
} from "lucide-react";
import type { SearchResult } from "../api/search";
import { CopyButton } from "./CopyButton";

interface SearchResultsProps {
  results: SearchResult[];
  emptyMessage?: string;
  onRetry?: () => void;
  onOpenContacts?: () => void;
  onOpenManual?: () => void;
  canEdit?: boolean;
  onEditResult?: (entryId: string) => void;
}

type EvidenceTone = "official" | "case" | "weak";

const BRANCH_SECTION_PREFIX = "[구분] ";

function branchSectionTitle(action: string) {
  return action.startsWith(BRANCH_SECTION_PREFIX)
    ? action.slice(BRANCH_SECTION_PREFIX.length)
    : null;
}

function evidenceMeta(result: SearchResult): {
  tone: EvidenceTone;
  label: string;
  background: string;
  border: string;
  color: string;
} {
  if (result.evidenceLevel === "official_manual") {
    return {
      tone: "official",
      label: "공식 매뉴얼",
      background: "#ECF8F2",
      border: "#72B99B",
      color: "#126B49",
    };
  }

  const isPastCase = result.kind.toLowerCase().includes("recurring")
    || result.evidenceLevel.toLowerCase().includes("case");

  return isPastCase
    ? {
        tone: "case",
        label: "과거 처리사례",
        background: "#EEF5FF",
        border: "#8BB8EE",
        color: "#155A9C",
      }
    : {
        tone: "weak",
        label: "근거 확인 필요",
        background: "#FFF6E8",
        border: "#E8B15D",
        color: "#975B0C",
      };
}

export function SearchResults({
  results,
  emptyMessage,
  onRetry,
  onOpenContacts,
  onOpenManual,
  canEdit = false,
  onEditResult,
}: SearchResultsProps) {
  const result = results[0];
  const [activeBranch, setActiveBranch] = useState(0);

  useEffect(() => {
    setActiveBranch(0);
  }, [result?.id]);

  if (!result) {
    return (
      <section className="border-y bg-white px-5 py-12 text-center" style={{ borderColor: "var(--border)" }}>
        <h2 className="text-xl font-extrabold">일치하는 공식 대응 절차를 찾지 못했습니다.</h2>
        <p className="mx-auto mt-3 max-w-xl text-base leading-7" style={{ color: "var(--muted-foreground)" }}>
          {emptyMessage ?? "발생 위치, 시간, 대상, 현재 상황을 조금 더 구체적으로 입력해 주세요."}
        </p>
        <div className="mt-6 flex flex-wrap justify-center gap-2">
          {onRetry && (
            <button type="button" onClick={onRetry} className="inline-flex items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-bold text-white" style={{ background: "var(--brand-green)" }}>
              <RefreshCcw className="h-4 w-4" /> 다시 검색
            </button>
          )}
          {onOpenContacts && (
            <button type="button" onClick={onOpenContacts} className="rounded-xl border bg-white px-4 py-2.5 text-sm font-bold" style={{ borderColor: "var(--border)" }}>
              전화번호부 열기
            </button>
          )}
          {onOpenManual && (
            <button type="button" onClick={onOpenManual} className="rounded-xl border bg-white px-4 py-2.5 text-sm font-bold" style={{ borderColor: "var(--border)" }}>
              전체 매뉴얼 보기
            </button>
          )}
        </div>
      </section>
    );
  }

  const evidence = evidenceMeta(result);
  const selectedBranch = result.decisionBranches[activeBranch];
  const departmentContacts = result.departmentContacts ?? [];
  const relatedResults = results.slice(1);
  const immediateActions = result.immediateActions.length > 0
    ? result.immediateActions
    : result.guidance
      ? [result.guidance]
      : [];

  return (
    <div className="space-y-4">
      <article className="overflow-hidden border-y bg-white sm:rounded-2xl sm:border" style={{ borderColor: "var(--border)" }}>
        <header className="relative px-5 py-6 sm:px-7">
          <div className="flex flex-wrap items-center gap-2 pr-12">
            <span className="rounded-full border px-3 py-1 text-xs font-extrabold" style={{ background: evidence.background, borderColor: evidence.border, color: evidence.color }}>
              {evidence.label}
            </span>
            {result.category && <span className="text-sm font-semibold" style={{ color: "var(--muted-foreground)" }}>{result.category}</span>}
          </div>
          <h2 className="mt-3 text-2xl font-extrabold tracking-tight sm:text-3xl">{result.civilType}</h2>
          {result.paragraphSummary && (
            <p className="mt-3 max-w-3xl text-base leading-7" style={{ color: "#4B5563" }}>{result.paragraphSummary}</p>
          )}
          {canEdit && onEditResult && result.kind.startsWith("manual_") && (
            <button
              type="button"
              onClick={() => onEditResult(result.id)}
              aria-label={`${result.civilType} 수정`}
              title={`${result.civilType} 수정`}
              className="absolute right-5 top-5 inline-flex h-10 w-10 items-center justify-center rounded-full border bg-white sm:right-7"
              style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
            >
              <Pencil className="h-4 w-4" />
            </button>
          )}
        </header>

        {evidence.tone === "case" && (
          <div className="mx-5 mb-5 border-l-4 px-4 py-3 text-sm leading-6 sm:mx-7" style={{ background: "#F3F7FD", borderColor: "#2B78C5", color: "#174D82" }}>
            참고 사례입니다. 현재 공식 매뉴얼의 확정된 대응 절차가 아니므로 필요 시 담당 부서에 확인하세요.
          </div>
        )}
        {evidence.tone === "weak" && (
          <div className="mx-5 mb-5 border-l-4 px-4 py-3 text-sm leading-6 sm:mx-7" style={{ background: "#FFF8ED", borderColor: "#E08A1E", color: "#8A4C08" }}>
            공식 근거가 충분하지 않습니다. 임의로 확정 안내하지 말고 담당 부서 또는 긴급 연락망을 확인하세요.
          </div>
        )}

        <div className="grid border-y lg:grid-cols-[minmax(0,1fr)_330px]" style={{ borderColor: "var(--border)" }}>
          <section className="px-5 py-6 sm:px-7" style={{ background: "#F5FAFE" }}>
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6" style={{ color: "var(--brand-green)" }} />
              <h3 className="text-xl font-extrabold" style={{ color: "var(--brand-green-dark)" }}>지금 해야 할 일</h3>
            </div>
            {immediateActions.length > 0 ? (
              <ol className="mt-4 space-y-3 text-base leading-7">
                {immediateActions.map((action, index) => (
                  <li key={`${action}-${index}`} className="flex gap-3">
                    <span className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-xs font-extrabold text-white" style={{ background: "var(--brand-green)" }}>{index + 1}</span>
                    <span>{action}</span>
                  </li>
                ))}
              </ol>
            ) : (
              <p className="mt-3 text-sm" style={{ color: "var(--muted-foreground)" }}>담당 부서 확인 후 조치하세요.</p>
            )}
          </section>

          <aside className="border-t bg-white px-5 py-6 lg:border-l lg:border-t-0" style={{ borderColor: "var(--border)" }}>
            <div className="flex items-start gap-3">
              <Building2 className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
              <div>
                <p className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>담당 부서</p>
                <p className="mt-1 text-base font-extrabold">{result.department}</p>
              </div>
            </div>
            {departmentContacts.length > 0 ? (
              <div className="mt-4 space-y-4 border-t pt-4" style={{ borderColor: "var(--border)" }}>
                {departmentContacts.map((contact) => (
                  <div key={`${contact.department}-${contact.label}-${contact.phone}`}>
                    <p className="text-sm font-extrabold">{contact.department}</p>
                    {contact.label && contact.label !== contact.department && (
                      <p className="mt-1 text-xs font-semibold" style={{ color: "var(--muted-foreground)" }}>{contact.label}</p>
                    )}
                    <div className="mt-2 flex flex-wrap items-center gap-2">
                      <strong className="text-base" style={{ color: "var(--brand-green-dark)" }}>{contact.phone}</strong>
                      <CopyButton value={contact.phone} label="번호 복사" compact />
                      <a href={`tel:${contact.phone.replace(/[^\d+]/g, "")}`} className="inline-flex items-center gap-1.5 rounded-lg border bg-white px-2.5 py-1.5 text-xs font-bold" style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}>
                        <PhoneCall className="h-3.5 w-3.5" /> 전화
                      </a>
                    </div>
                    {contact.note && <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--muted-foreground)" }}>{contact.note}</p>}
                  </div>
                ))}
              </div>
            ) : (
              <button type="button" onClick={onOpenContacts} className="mt-4 text-sm font-bold underline underline-offset-4" style={{ color: "var(--brand-green-dark)" }}>
                전화번호부에서 담당 부서 확인
              </button>
            )}
          </aside>
        </div>

        <div className="space-y-7 px-5 py-7 sm:px-7">
          {result.intakeQuestions.length > 0 && (
            <section>
              <div className="flex items-center gap-2">
                <ClipboardList className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
                <h3 className="text-lg font-extrabold">먼저 확인할 내용</h3>
              </div>
              <ol className="mt-4 grid gap-3 text-sm leading-6 sm:grid-cols-2">
                {result.intakeQuestions.map((question, index) => (
                  <li key={question} className="flex gap-3 border-t pt-3" style={{ borderColor: "var(--border)" }}>
                    <span className="font-extrabold" style={{ color: "var(--brand-green)" }}>{index + 1}</span>
                    <span>{question}</span>
                  </li>
                ))}
              </ol>
            </section>
          )}

          {result.decisionBranches.length > 0 && selectedBranch && (
            <section className="border-t pt-6" style={{ borderColor: "var(--border)" }}>
              <h3 className="text-lg font-extrabold">상황별 분기</h3>
              <div className="mt-4 grid gap-5 md:grid-cols-[230px_minmax(0,1fr)]">
                <div className="space-y-2">
                  {result.decisionBranches.map((branch, index) => (
                    <button
                      type="button"
                      key={branch.condition}
                      onClick={() => setActiveBranch(index)}
                      aria-pressed={activeBranch === index}
                      className="w-full rounded-xl border px-4 py-3 text-left text-sm font-bold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]"
                      style={{
                        background: activeBranch === index ? "var(--brand-green)" : "#FFFFFF",
                        borderColor: activeBranch === index ? "var(--brand-green)" : "var(--border)",
                        color: activeBranch === index ? "#FFFFFF" : "var(--foreground)",
                      }}
                    >
                      {branch.condition}
                    </button>
                  ))}
                </div>
                <div className="border-l-2 pl-5" style={{ borderColor: "var(--brand-green)" }}>
                  <h4 className="font-extrabold">{selectedBranch.condition}</h4>
                  <ul className="mt-3 space-y-2 text-sm leading-6">
                    {selectedBranch.actions.map((action) => {
                      const sectionTitle = branchSectionTitle(action);
                      return sectionTitle ? (
                        <li key={action} className="pt-3 first:pt-0">
                          <strong className="inline-flex rounded-full px-3 py-1 text-sm" style={{ background: "#EAF4FB", color: "var(--brand-green-dark)" }}>
                            {sectionTitle}
                          </strong>
                        </li>
                      ) : <li key={action}>• {action}</li>;
                    })}
                  </ul>
                  {selectedBranch.response && (
                    <div className="mt-5 bg-[#F7FAFC] p-4">
                      <p className="text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>민원인 안내 문구</p>
                      <p className="mt-2 text-sm leading-6">“{selectedBranch.response}”</p>
                      <div className="mt-3"><CopyButton value={selectedBranch.response} label="문구 복사" compact /></div>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {result.responseScripts.length > 0 && (
            <section className="border-t pt-6" style={{ borderColor: "var(--border)" }}>
              <div className="flex items-center gap-2">
                <MessageSquareText className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
                <h3 className="text-lg font-extrabold">민원인 안내 문구</h3>
              </div>
              <div className="mt-4 space-y-3">
                {result.responseScripts.map((script) => (
                  <div key={script} className="flex flex-col gap-3 border-l-2 bg-[#F7FAFC] px-4 py-3 sm:flex-row sm:items-start" style={{ borderColor: "var(--brand-green)" }}>
                    <p className="min-w-0 flex-1 text-sm leading-7">“{script}”</p>
                    <CopyButton value={script} label="문구 복사" compact />
                  </div>
                ))}
              </div>
            </section>
          )}

          {(result.escalationRules.length > 0 || result.cautions.length > 0) && (
            <section className="border-l-4 px-4 py-3" style={{ background: "#FFF5F3", borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
              <div className="flex gap-3">
                <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" />
                <div>
                  <h3 className="font-extrabold">주의사항</h3>
                  <div className="mt-2 space-y-2 text-sm leading-6">
                    {result.escalationRules.map((rule) => <p key={rule.condition}><strong>{rule.condition}:</strong> {rule.action}</p>)}
                    {result.cautions.map((caution) => <p key={caution}>• {caution}</p>)}
                  </div>
                </div>
              </div>
            </section>
          )}
        </div>

        <details className="group border-t px-5 py-4 text-sm sm:px-7" style={{ borderColor: "var(--border)" }}>
          <summary className="flex cursor-pointer list-none items-center gap-2 font-bold" style={{ color: "var(--muted-foreground)" }}>
            <BookOpen className="h-4 w-4" /> 근거 문서·원문·PDF 페이지
            <ChevronDown className="ml-auto h-4 w-4 transition-transform group-open:rotate-180" />
          </summary>
          <div className="mt-3 space-y-2 pl-6 text-xs leading-6" style={{ color: "var(--muted-foreground)" }}>
            <p>{result.sourceReference || result.documentName}</p>
            {result.sourcePages.length > 0 && <p>PDF {result.sourcePages.join(", ")}쪽</p>}
            {result.note && <p>{result.note}</p>}
            {result.originalUrl && <a href={result.originalUrl} target="_blank" rel="noreferrer" className="font-bold underline underline-offset-4">원문 열기</a>}
          </div>
        </details>
      </article>

      {relatedResults.length > 0 && (
        <details className="group rounded-xl border bg-white px-5 py-4 text-sm" style={{ borderColor: "#8BB8EE" }}>
          <summary className="flex cursor-pointer list-none items-center gap-2 font-bold" style={{ color: "#155A9C" }}>
            <BookOpen className="h-4 w-4" /> 함께 확인할 과거 처리사례
            <ChevronDown className="ml-auto h-4 w-4 transition-transform group-open:rotate-180" />
          </summary>
          <div className="mt-4 space-y-4 border-t pt-4" style={{ borderColor: "#CFE1F5" }}>
            {relatedResults.map((related) => (
              <div key={related.id}>
                <p className="font-bold">{related.civilType}</p>
                <p className="mt-2 text-xs leading-6" style={{ color: "var(--muted-foreground)" }}>{related.paragraphSummary}</p>
                <p className="mt-2 text-xs font-semibold">이첩 사례: {related.department}{related.candidateCount ? ` · ${related.candidateCount.toLocaleString()}건` : ""}</p>
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
