import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import {
  ArrowUp,
  Building2,
  CheckCircle2,
  Loader2,
  MessageCircleMore,
  PhoneCall,
  RotateCcw,
} from "lucide-react";
import { searchComplaints, type SearchResult } from "../api/search";
import yusungLogo from "@/imports/image.png";

interface ChatTurn {
  id: string;
  query: string;
  result?: SearchResult;
  error?: string;
  selectedBranchIndex?: number;
}

const BRANCH_SECTION_PREFIX = "[구분] ";

function branchSectionTitle(action: string) {
  return action.startsWith(BRANCH_SECTION_PREFIX)
    ? action.slice(BRANCH_SECTION_PREFIX.length)
    : null;
}

export function MiniDutyChat() {
  const [draft, setDraft] = useState("");
  const [turns, setTurns] = useState<ChatTurn[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const previousTitle = document.title;
    document.title = "빠른 응대창 | 유성구";
    return () => {
      document.title = previousTitle;
    };
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, isLoading]);

  const submitQuestion = async () => {
    const query = draft.trim();
    if (!query || isLoading) return;

    const id = `${Date.now()}-${query}`;
    setDraft("");
    setIsLoading(true);

    try {
      const response = await searchComplaints(query, 1);
      const result = response.results[0];
      setTurns((current) => [
        ...current,
        {
          id,
          query,
          result,
          error: result ? undefined : response.message || "대응 절차를 찾지 못했습니다.",
        },
      ]);
    } catch (error) {
      setTurns((current) => [
        ...current,
        {
          id,
          query,
          error: error instanceof Error ? error.message : "검색 요청에 실패했습니다.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    void submitQuestion();
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submitQuestion();
    }
  };

  const selectBranch = (turnId: string, branchIndex: number) => {
    setTurns((current) =>
      current.map((turn) =>
        turn.id === turnId
          ? { ...turn, selectedBranchIndex: branchIndex }
          : turn,
      ),
    );
  };

  return (
    <div className="h-screen min-h-[520px] bg-[#F3F4F6] p-2 text-[#18242C]">
      <section
        className="mx-auto flex h-full w-full max-w-[430px] flex-col overflow-hidden rounded-2xl border bg-white"
        style={{ borderColor: "var(--sidebar-border)" }}
      >
        <header className="flex items-center justify-between border-b px-4 py-3" style={{ borderColor: "var(--sidebar-border)" }}>
          <div className="flex min-w-0 items-center gap-3">
            <img src={yusungLogo} alt="유성구 로고" className="h-7 w-auto object-contain" />
            <div className="h-5 w-px bg-[#D6D9DD]" />
            <h1 className="truncate text-sm font-bold">빠른 응대창</h1>
          </div>
          <button
            type="button"
            onClick={() => setTurns([])}
            disabled={turns.length === 0 || isLoading}
            aria-label="대화 초기화"
            className="inline-flex h-9 w-9 items-center justify-center rounded-lg border bg-white disabled:opacity-30"
            style={{ borderColor: "var(--sidebar-border)", color: "var(--muted-foreground)" }}
          >
            <RotateCcw className="h-4 w-4" />
          </button>
        </header>

        <div
          role="log"
          aria-live="polite"
          aria-busy={isLoading}
          className="flex-1 overflow-y-auto px-4 py-5"
        >
          {turns.length === 0 && !isLoading ? (
            <div className="flex h-full min-h-[280px] flex-col items-center justify-center px-6 text-center">
              <MessageCircleMore className="h-8 w-8" style={{ color: "var(--brand-green)" }} />
              <p className="mt-4 text-base font-bold">민원 내용을 입력해 주세요</p>
              <p className="mt-2 text-xs leading-5" style={{ color: "var(--muted-foreground)" }}>
                당직자가 확인할 내용과 처리 순서, 담당 부서 연락처를 바로 알려드려요.
              </p>
            </div>
          ) : (
            <div className="space-y-6">
              {turns.map((turn) => (
                <div key={turn.id}>
                  <div className="ml-auto max-w-[86%] rounded-2xl rounded-br-sm px-4 py-3 text-sm leading-6 text-white" style={{ background: "var(--brand-green)" }}>
                    {turn.query}
                  </div>

                  {turn.result ? (
                    <MiniAnswer
                      result={turn.result}
                      selectedBranchIndex={turn.selectedBranchIndex}
                      onSelectBranch={(branchIndex) => selectBranch(turn.id, branchIndex)}
                    />
                  ) : (
                    <div className="mt-3 border-l-2 px-3 py-1 text-sm leading-6" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
                      {turn.error}
                    </div>
                  )}
                </div>
              ))}

              {isLoading && (
                <div className="flex items-center gap-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
                  <Loader2 className="h-4 w-4 animate-spin" style={{ color: "var(--brand-green)" }} />
                  대응 절차를 확인하고 있습니다.
                </div>
              )}
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <footer className="border-t bg-white p-3" style={{ borderColor: "var(--sidebar-border)" }}>
          <form onSubmit={handleSubmit} className="rounded-2xl border-2 bg-white p-2" style={{ borderColor: "var(--brand-green)" }}>
            <textarea
              value={draft}
              onChange={(event) => setDraft(event.target.value)}
              onKeyDown={handleKeyDown}
              rows={2}
              placeholder="예: 밤 11시 공사장 소음 신고"
              aria-label="민원 내용"
              className="max-h-24 min-h-[52px] w-full resize-none bg-transparent px-2 py-1 text-sm leading-5 outline-none"
            />
            <div className="flex items-center justify-between pl-2">
              <span className="text-[10px]" style={{ color: "var(--muted-foreground)" }}>
                Enter 전송 · Shift+Enter 줄바꿈
              </span>
              <button
                type="submit"
                disabled={!draft.trim() || isLoading}
                aria-label="민원 전송"
                className="inline-flex h-9 w-9 items-center justify-center rounded-full text-white disabled:opacity-35"
                style={{ background: "var(--brand-green)" }}
              >
                {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowUp className="h-4 w-4" />}
              </button>
            </div>
          </form>
        </footer>
      </section>
    </div>
  );
}

interface MiniAnswerProps {
  result: SearchResult;
  selectedBranchIndex?: number;
  onSelectBranch: (branchIndex: number) => void;
}

function MiniAnswer({ result, selectedBranchIndex, onSelectBranch }: MiniAnswerProps) {
  const actions = result.immediateActions.length > 0
    ? result.immediateActions
    : result.guidance
      ? [result.guidance]
      : [];
  const contacts = result.departmentContacts ?? [];
  const selectedBranch = selectedBranchIndex === undefined
    ? undefined
    : result.decisionBranches[selectedBranchIndex];

  return (
    <section className="mt-3 border-l-2 pl-3" style={{ borderColor: "var(--brand-green)" }}>
      <p className="text-[10px] font-bold" style={{ color: "var(--brand-green)" }}>대응 안내</p>
      <h2 className="mt-1 text-base font-extrabold">{result.civilType}</h2>
      <p className="mt-2 text-xs leading-5" style={{ color: "var(--muted-foreground)" }}>
        {result.paragraphSummary}
      </p>

      {result.intakeQuestions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-bold">먼저 확인</h3>
          <ol className="mt-2 space-y-1.5 text-xs leading-5">
            {result.intakeQuestions.slice(0, 4).map((question, index) => (
              <li key={question} className="flex gap-2">
                <span className="font-bold" style={{ color: "var(--brand-green)" }}>{index + 1}</span>
                <span>{question}</span>
              </li>
            ))}
          </ol>
        </div>
      )}

      {actions.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-bold">지금 할 일</h3>
          <ul className="mt-2 space-y-1.5 text-xs leading-5">
            {actions.map((action) => (
              <li key={action} className="flex gap-2">
                <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                <span>{action}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {result.decisionBranches.length > 0 && (
        <div className="mt-4">
          <h3 className="text-xs font-bold">상황을 선택하세요</h3>
          <div className="mt-2 flex gap-1.5 overflow-x-auto pb-1">
            {result.decisionBranches.map((branch, index) => {
              const isActive = selectedBranchIndex === index;
              return (
                <button
                  key={branch.condition}
                  type="button"
                  aria-pressed={isActive}
                  onClick={() => onSelectBranch(index)}
                  className="shrink-0 rounded-full border px-3 py-1.5 text-[11px] font-semibold"
                  style={{
                    background: isActive ? "var(--brand-green)" : "#FFFFFF",
                    borderColor: isActive ? "var(--brand-green)" : "var(--sidebar-border)",
                    color: isActive ? "#FFFFFF" : "var(--foreground)",
                  }}
                >
                  {branch.condition}
                </button>
              );
            })}
          </div>

          {selectedBranch && (
            <div className="mt-3 border-l-2 py-1 pl-3" style={{ borderColor: "var(--brand-green)" }}>
              <p className="text-xs font-bold">{selectedBranch.condition}</p>
              <ul className="mt-2 space-y-1.5 text-xs leading-5">
                {selectedBranch.actions.map((action) => {
                  const sectionTitle = branchSectionTitle(action);
                  return sectionTitle ? (
                    <li key={action} className="pt-2 first:pt-0 text-sm font-extrabold" style={{ color: "var(--brand-green-dark)" }}>
                      {sectionTitle}
                    </li>
                  ) : (
                    <li key={action} className="flex gap-2">
                      <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                      <span>{action}</span>
                    </li>
                  );
                })}
              </ul>
              {selectedBranch.response && (
                <p className="mt-2 text-xs leading-5" style={{ color: "var(--brand-green-dark)" }}>
                  “{selectedBranch.response}”
                </p>
              )}
            </div>
          )}
        </div>
      )}

      <div className="mt-4 border-t pt-3" style={{ borderColor: "var(--sidebar-border)" }}>
        <div className="flex items-center gap-2 text-xs font-bold">
          <Building2 className="h-4 w-4" style={{ color: "var(--brand-green)" }} />
          {result.department}
        </div>
        {contacts.slice(0, 2).map((contact) => (
          <a
            key={`${contact.label}-${contact.phone}`}
            href={`tel:${contact.phone.replace(/[^\d+]/g, "")}`}
            className="mt-2 flex items-center gap-2 text-xs font-bold"
            style={{ color: "var(--brand-green-dark)" }}
          >
            <PhoneCall className="h-3.5 w-3.5" />
            {contact.department} {contact.phone}
          </a>
        ))}
      </div>

      {result.responseScripts[0] && (
        <div className="mt-4 border-l-2 py-1 pl-3" style={{ borderColor: "var(--brand-green)" }}>
          <p className="text-[10px] font-bold" style={{ color: "var(--brand-green)" }}>민원인 안내 문구</p>
          <p className="mt-1 text-xs leading-5">“{result.responseScripts[0]}”</p>
        </div>
      )}

      {result.cautions.length > 0 && (
        <div className="mt-4 border-l-2 py-1 pl-3" style={{ borderColor: "var(--brand-red)" }}>
          <p className="text-[10px] font-bold" style={{ color: "var(--brand-red-dark)" }}>주의</p>
          {result.cautions.slice(0, 2).map((caution) => (
            <p key={caution} className="mt-1 text-xs leading-5" style={{ color: "var(--brand-red-dark)" }}>• {caution}</p>
          ))}
        </div>
      )}
    </section>
  );
}
