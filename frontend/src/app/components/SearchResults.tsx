import { useEffect, useState } from "react";
import {
  AlertCircle,
  BookOpen,
  Building2,
  Check,
  ChevronDown,
  ChevronUp,
  ClipboardCheck,
  Phone,
} from "lucide-react";
import type {
  DepartmentContact,
  DepartmentRouting,
  OperatorGuidance,
  OperatorOption,
} from "@/api/search";

export interface SearchResult {
  id: string;
  tier: string;
  kind: string;
  category: string;
  documentName: string;
  civilType: string;
  department: string;
  departments: string[];
  departmentContacts: DepartmentContact[];
  operatorGuidance: OperatorGuidance;
  paragraphSummary: string;
  keyActions: string[];
  originalText: string;
  guidance: string;
  note: string;
  updatedAt: string;
  relevance: number;
  tags: string[];
  evidenceLevel: string;
  sourceReference: string;
  sourcePages: number[];
  page: number | null;
  originalUrl: string | null;
  candidateCount: number | null;
  departmentRouting: DepartmentRouting[];
}

interface SearchResultsProps {
  results: SearchResult[];
  notice: string;
}

const TIER_LABELS: Record<string, string> = {
  manual_exact: "공식 매뉴얼",
  manual_semantic: "유사 매뉴얼",
  historical_case: "과거 사례 기준",
  no_match: "검색 결과 없음",
};

export function getTierLabel(tier: string) {
  return TIER_LABELS[tier] ?? tier;
}

function ContactList({ contacts }: { contacts: DepartmentContact[] }) {
  if (contacts.length === 0) return null;

  return (
    <div className="mt-3 space-y-2">
      {contacts.map((contact) => (
        <div key={contact.department} className="flex flex-wrap items-center gap-x-3 gap-y-1.5">
          <span style={{ color: "var(--muted-foreground)", fontSize: "12px" }}>
            {contact.department}
          </span>
          <div className="flex flex-wrap gap-1.5">
            {contact.phoneNumbers.map((phoneNumber) => (
              <a
                key={phoneNumber}
                href={`tel:${phoneNumber}`}
                aria-label={`${contact.department} ${phoneNumber} 전화 연결`}
                className="inline-flex items-center gap-1.5"
                style={{
                  borderRadius: "7px",
                  background: "var(--brand-green-light)",
                  color: "var(--brand-green-dark)",
                  fontSize: "12px",
                  fontWeight: 700,
                  padding: "4px 9px",
                }}
              >
                <Phone className="w-3 h-3" />
                {phoneNumber}
              </a>
            ))}
          </div>
        </div>
      ))}
    </div>
  );
}

function ActionSteps({ steps }: { steps: string[] }) {
  if (steps.length === 0) return null;

  return (
    <ol className="space-y-3">
      {steps.map((step, index) => (
        <li key={`${index}-${step}`} className="flex items-start gap-3">
          <span
            className="flex-shrink-0 flex items-center justify-center"
            style={{
              width: "24px",
              height: "24px",
              borderRadius: "999px",
              background: "var(--brand-green)",
              color: "#fff",
              fontSize: "11px",
              fontWeight: 800,
            }}
          >
            {index + 1}
          </span>
          <span style={{ color: "var(--foreground)", fontSize: "14px", lineHeight: 1.7 }}>
            {step}
          </span>
        </li>
      ))}
    </ol>
  );
}

function GuidanceOption({
  option,
  selected,
  onSelect,
}: {
  option: OperatorOption;
  selected: boolean;
  onSelect: () => void;
}) {
  const requiresConfirmation = option.status === "needs_confirmation";

  return (
    <button
      type="button"
      onClick={onSelect}
      aria-pressed={selected}
      className="w-full text-left p-4 transition-all duration-150"
      style={{
        borderRadius: "12px",
        border: `1.5px solid ${selected ? "var(--brand-green)" : "var(--border)"}`,
        background: selected ? "var(--brand-green-light)" : "#fff",
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 750, lineHeight: 1.5 }}>
            {option.label}
          </p>
          <p style={{ color: "var(--muted-foreground)", fontSize: "12px", marginTop: "4px" }}>
            담당부서 {option.department}
          </p>
        </div>
        <span
          className="flex-shrink-0 px-2.5 py-1"
          style={{
            borderRadius: "999px",
            background: requiresConfirmation ? "#FFF3D6" : "var(--brand-green-light)",
            color: requiresConfirmation ? "#8A5A00" : "var(--brand-green-dark)",
            fontSize: "10px",
            fontWeight: 800,
          }}
        >
          {option.statusLabel}
        </span>
      </div>
      {selected && (
        <div className="flex items-center gap-1.5 mt-3" style={{ color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 700 }}>
          <Check className="w-3.5 h-3.5" /> 선택됨
        </div>
      )}
    </button>
  );
}

export function SearchResults({ results, notice }: SearchResultsProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string>>({});

  useEffect(() => {
    setExpandedId(null);
    setSelectedOptions({});
  }, [results]);

  if (results.length === 0) {
    return (
      <div
        className="p-8 border text-center"
        style={{ borderRadius: "16px", background: "var(--card)", borderColor: "var(--border)" }}
      >
        <AlertCircle className="w-7 h-7 mx-auto mb-3" style={{ color: "var(--muted-foreground)" }} />
        <p style={{ color: "var(--foreground)", fontSize: "14px", fontWeight: 700, marginBottom: "6px" }}>
          일치하는 대응 항목을 찾지 못했습니다.
        </p>
        <p style={{ color: "var(--muted-foreground)", fontSize: "13px", lineHeight: 1.7 }}>
          {notice || "민원 위치와 대상을 더 구체적으로 입력하거나 담당부서를 확인해 주세요."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {results.map((result) => {
        const isExpanded = expandedId === result.id;
        const operator = result.operatorGuidance;
        const selectedOption = operator.options.find(
          (option) => option.id === selectedOptions[result.id],
        );
        const actionSteps = selectedOption?.actionSteps ?? operator.actionSteps;
        const visibleDepartment = selectedOption?.department
          ?? (operator.mode === "needs_clarification" ? "" : result.department);
        const visibleContacts = selectedOption
          ? result.departmentContacts.filter((contact) => contact.department === selectedOption.department)
          : result.departmentContacts;
        const isOfficial = result.evidenceLevel === "official_manual";
        const canShowOriginal = isOfficial && Boolean(result.originalText);

        return (
          <article
            key={result.id}
            className="overflow-hidden border"
            style={{
              borderRadius: "18px",
              background: "var(--card)",
              borderColor: "var(--border)",
              boxShadow: "0 2px 12px rgba(0,0,0,0.06)",
            }}
          >
            <div className="px-7 py-6">
              <div className="flex flex-wrap items-start justify-between gap-3 mb-5">
                <h2 style={{ color: "var(--foreground)", fontSize: "21px", fontWeight: 800, lineHeight: 1.45 }}>
                  {result.civilType}
                </h2>
                <span
                  className="flex-shrink-0 px-3 py-1.5"
                  style={{
                    borderRadius: "999px",
                    background: isOfficial ? "var(--brand-green-light)" : "#FFF3D6",
                    color: isOfficial ? "var(--brand-green-dark)" : "#8A5A00",
                    fontSize: "11px",
                    fontWeight: 800,
                  }}
                >
                  {getTierLabel(result.tier)}
                </span>
              </div>

              {operator.mode === "needs_clarification" && (
                <section className="mb-5">
                  <div className="mb-3">
                    <p style={{ color: "var(--brand-green-dark)", fontSize: "12px", fontWeight: 800, marginBottom: "6px" }}>
                      {operator.headline}
                    </p>
                    <p style={{ color: "var(--foreground)", fontSize: "17px", fontWeight: 800, lineHeight: 1.55 }}>
                      {operator.question}
                    </p>
                  </div>
                  <div className="grid grid-cols-1 gap-2.5">
                    {operator.options.map((option) => (
                      <GuidanceOption
                        key={option.id}
                        option={option}
                        selected={selectedOption?.id === option.id}
                        onSelect={() => setSelectedOptions((current) => ({
                          ...current,
                          [result.id]: option.id,
                        }))}
                      />
                    ))}
                  </div>
                </section>
              )}

              {visibleDepartment && (
                <section
                  className="mb-5 p-4"
                  style={{ borderRadius: "12px", background: "var(--background)" }}
                >
                  <div className="flex items-center gap-2">
                    <Building2 className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
                    <span style={{ color: "var(--muted-foreground)", fontSize: "11px", fontWeight: 800 }}>
                      담당 부서
                    </span>
                  </div>
                  <p style={{ color: "var(--foreground)", fontSize: "15px", fontWeight: 800, marginTop: "7px" }}>
                    {visibleDepartment}
                  </p>
                  <ContactList contacts={visibleContacts} />
                </section>
              )}

              {actionSteps.length > 0 && (
                <section
                  className="mb-5 p-5"
                  style={{ borderRadius: "14px", background: "var(--brand-green-light)" }}
                >
                  <div className="flex items-center gap-2 mb-4" style={{ color: "var(--brand-green-dark)" }}>
                    <ClipboardCheck className="w-4 h-4" />
                    <h3 style={{ fontSize: "13px", fontWeight: 850 }}>
                      {selectedOption ? "선택한 상황의 처리 순서" : operator.headline}
                    </h3>
                  </div>
                  <ActionSteps steps={actionSteps} />
                </section>
              )}

              {operator.caution && (
                <div
                  className="flex items-start gap-2.5 p-3.5 mb-4"
                  style={{ borderRadius: "10px", background: "#FFF8E8", color: "#765000" }}
                >
                  <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
                  <p style={{ fontSize: "12px", lineHeight: 1.65 }}>{operator.caution}</p>
                </div>
              )}

              {canShowOriginal && (
                <>
                  {isExpanded && (
                    <div
                      className="p-5 mb-4"
                      style={{ borderRadius: "12px", background: "#F7F8F7", border: "1px solid var(--border)" }}
                    >
                      <div className="flex items-center gap-2 mb-3">
                        <BookOpen className="w-4 h-4" style={{ color: "var(--brand-green)" }} />
                        <p style={{ color: "var(--foreground)", fontSize: "13px", fontWeight: 800 }}>
                          매뉴얼 원문
                        </p>
                      </div>
                      <p className="whitespace-pre-wrap" style={{ color: "var(--card-foreground)", fontSize: "12px", lineHeight: 1.85 }}>
                        {result.originalText}
                      </p>
                      {result.sourceReference && (
                        <p className="mt-4 pt-3 border-t" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)", fontSize: "11px" }}>
                          {result.sourceReference}
                        </p>
                      )}
                    </div>
                  )}
                  <button
                    type="button"
                    aria-expanded={isExpanded}
                    onClick={() => setExpandedId(isExpanded ? null : result.id)}
                    className="inline-flex items-center gap-1.5"
                    style={{ color: "var(--muted-foreground)", fontSize: "12px", fontWeight: 650 }}
                  >
                    {isExpanded
                      ? <><ChevronUp className="w-4 h-4" />매뉴얼 원문 닫기</>
                      : <><ChevronDown className="w-4 h-4" />매뉴얼 원문 보기</>}
                  </button>
                </>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}
