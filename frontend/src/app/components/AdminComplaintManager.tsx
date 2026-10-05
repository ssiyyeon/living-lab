import { CircleAlert, Loader2, Plus, RotateCcw, Save, Search, Trash2 } from "lucide-react";
import { FormEvent, useEffect, useMemo, useState } from "react";
import {
  createAdminManualEntry,
  deleteOrRestoreAdminManualEntry,
  fetchAdminManualCatalog,
  updateAdminManualEntry,
  type AdminManualInput,
  type DecisionBranch,
  type EscalationRule,
  type ManualCatalogEntry,
} from "../api/search";

const MANUAL_GROUPS = [
  "민원유형별 대응",
  "재난유형별 대응",
  "당직근무자 준수사항",
  "청사 보안·시건",
  "비상 발령·소집",
  "부록",
];

const EMPTY_DRAFT: AdminManualInput = {
  entryType: "case",
  group: "민원유형별 대응",
  topic: "",
  title: "",
  breadcrumb: [],
  sourcePages: [],
  departments: [],
  summary: "",
  content: "",
  intakeQuestions: [],
  immediateActions: [],
  decisionBranches: [],
  responseScripts: [],
  escalationRules: [],
  cautions: [],
};

function entryToDraft(entry: ManualCatalogEntry): AdminManualInput {
  return {
    entryType: entry.entryType,
    group: entry.group,
    topic: entry.topic,
    title: entry.title,
    breadcrumb: [...entry.breadcrumb],
    sourcePages: [...entry.sourcePages],
    departments: [...entry.departments],
    summary: entry.summary,
    content: entry.content,
    intakeQuestions: [...entry.intakeQuestions],
    immediateActions: [...entry.immediateActions],
    decisionBranches: entry.decisionBranches.map((branch) => ({
      condition: branch.condition,
      actions: [...branch.actions],
      response: branch.response,
    })),
    responseScripts: [...entry.responseScripts],
    escalationRules: entry.escalationRules.map((rule) => ({ ...rule })),
    cautions: [...entry.cautions],
  };
}

function normalizedDraft(draft: AdminManualInput): AdminManualInput {
  const strings = (values: string[]) => values.map((value) => value.trim()).filter(Boolean);
  return {
    ...draft,
    title: draft.title.trim(),
    group: draft.group.trim(),
    topic: draft.topic.trim(),
    breadcrumb: strings(draft.breadcrumb),
    departments: strings(draft.departments),
    summary: draft.summary.trim(),
    content: draft.content.trim(),
    intakeQuestions: strings(draft.intakeQuestions),
    immediateActions: strings(draft.immediateActions),
    responseScripts: strings(draft.responseScripts),
    cautions: strings(draft.cautions),
    decisionBranches: draft.decisionBranches
      .map((branch) => ({
        condition: branch.condition.trim(),
        actions: strings(branch.actions),
        response: branch.response.trim(),
      }))
      .filter((branch) => branch.condition || branch.actions.length || branch.response),
    escalationRules: draft.escalationRules
      .map((rule) => ({ condition: rule.condition.trim(), action: rule.action.trim() }))
      .filter((rule) => rule.condition || rule.action),
  };
}

export function AdminComplaintManager({
  onChanged,
  initialSelectedId,
}: {
  onChanged?: () => void;
  initialSelectedId?: string;
}) {
  const [entries, setEntries] = useState<ManualCatalogEntry[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [draft, setDraft] = useState<AdminManualInput | null>(null);
  const [query, setQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  const selectedEntry = entries.find((entry) => entry.id === selectedId) ?? null;

  const loadEntries = async (preferredId?: string) => {
    setError("");
    try {
      const response = await fetchAdminManualCatalog();
      setEntries(response.entries);
      const next = response.entries.find((entry) => entry.id === preferredId)
        ?? response.entries.find((entry) => entry.id === selectedId)
        ?? response.entries[0]
        ?? null;
      setSelectedId(next?.id ?? null);
      setDraft(next ? entryToDraft(next) : null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "민원 대응 목록을 불러오지 못했습니다.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    void loadEntries(initialSelectedId);
  }, []);

  const filteredEntries = useMemo(() => {
    const normalized = query.replace(/\s+/g, "").toLowerCase();
    if (!normalized) return entries;
    return entries.filter((entry) =>
      [entry.title, entry.topic, entry.group, entry.summary, ...entry.departments]
        .join(" ")
        .replace(/\s+/g, "")
        .toLowerCase()
        .includes(normalized),
    );
  }, [entries, query]);

  const selectEntry = (entry: ManualCatalogEntry) => {
    setSelectedId(entry.id);
    setDraft(entryToDraft(entry));
    setError("");
    setMessage("");
  };

  const startCreate = () => {
    setSelectedId(null);
    setDraft({ ...EMPTY_DRAFT });
    setError("");
    setMessage("");
  };

  const saveEntry = async (event: FormEvent) => {
    event.preventDefault();
    if (!draft) return;
    const payload = normalizedDraft(draft);
    if (!payload.title || !payload.group) {
      setError("제목과 매뉴얼 분류를 입력해 주세요.");
      return;
    }

    setIsSaving(true);
    setError("");
    setMessage("");
    try {
      const saved = selectedId
        ? await updateAdminManualEntry(selectedId, payload)
        : await createAdminManualEntry(payload);
      await loadEntries(saved.id);
      setMessage(selectedId ? "민원 대응 내용을 저장했습니다." : "새 민원 대응 항목을 추가했습니다.");
      onChanged?.();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "민원 대응 내용을 저장하지 못했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  const removeOrRestore = async () => {
    if (!selectedEntry || (!selectedEntry.isCustom && !selectedEntry.isModified)) return;
    const description = selectedEntry.isCustom
      ? "관리자가 추가한 이 항목을 완전히 삭제할까요?"
      : "관리자 수정 내용을 제거하고 PDF 원본으로 되돌릴까요?";
    if (!window.confirm(description)) return;

    setIsSaving(true);
    setError("");
    setMessage("");
    try {
      const response = await deleteOrRestoreAdminManualEntry(selectedEntry.id);
      await loadEntries();
      setMessage(response.action === "restored" ? "PDF 원본 내용으로 복구했습니다." : "추가한 항목을 삭제했습니다.");
      onChanged?.();
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "삭제 또는 복구하지 못했습니다.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return <div className="flex min-h-64 items-center justify-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}><Loader2 className="h-5 w-5 animate-spin" /> 민원 대응 목록을 불러오고 있습니다.</div>;
  }

  if (error && entries.length === 0 && !draft) {
    return (
      <div className="mt-6 border-l-4 px-5 py-6" style={{ borderColor: "#E08A1E", background: "#FFF8ED" }}>
        <div className="flex items-start gap-3">
          <CircleAlert className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "#975B0C" }} />
          <div>
            <h2 className="font-extrabold">관리자 매뉴얼 API에 연결하지 못했습니다</h2>
            <p className="mt-2 text-sm leading-6" style={{ color: "#8A4C08" }}>{error}</p>
            <p className="mt-2 text-xs" style={{ color: "var(--muted-foreground)" }}>필요 API: GET/POST/PUT/DELETE /api/admin/manual</p>
            <button type="button" onClick={() => { setIsLoading(true); void loadEntries(); }} className="mt-4 rounded-xl border bg-white px-4 py-2.5 text-sm font-bold" style={{ borderColor: "#E08A1E", color: "#8A4C08" }}>다시 연결</button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="mt-6 grid min-w-0 gap-6 lg:grid-cols-[270px_minmax(0,1fr)]">
      <aside className="min-w-0 self-start lg:sticky lg:top-6">
        <div className="flex gap-2">
          <label className="flex min-w-0 flex-1 items-center rounded-xl border bg-white px-3" style={{ borderColor: "var(--border)" }}>
            <Search className="mr-2 h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
            <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="민원 대응 검색" aria-label="민원 대응 항목 검색" className="min-w-0 flex-1 bg-transparent py-3 text-sm outline-none" />
          </label>
          <button type="button" onClick={startCreate} aria-label="새 민원 대응 추가" className="inline-flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl text-white" style={{ background: "var(--brand-green)" }}><Plus className="h-5 w-5" /></button>
        </div>
        <div className="mt-3 max-h-[620px] overflow-y-auto border-y" style={{ borderColor: "var(--border)" }}>
          {filteredEntries.map((entry) => (
            <button key={entry.id} type="button" onClick={() => selectEntry(entry)} className="w-full border-b px-3 py-3 text-left last:border-b-0 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-[#036EB8]" style={{ borderColor: "var(--border)", background: selectedId === entry.id ? "#E7F0FC" : "transparent" }}>
              <span className="block truncate text-sm font-extrabold">{entry.title}</span>
              <span className="mt-1 flex items-center justify-between gap-2 text-xs" style={{ color: "var(--muted-foreground)" }}>
                <span className="truncate">{entry.topic || entry.group}</span>
                {entry.isCustom ? <span className="rounded-full bg-[#EEF5FF] px-2 py-0.5 text-[#155A9C]">추가</span> : entry.isModified ? <span className="rounded-full bg-[#FFF6E8] px-2 py-0.5 text-[#975B0C]">수정</span> : null}
              </span>
            </button>
          ))}
          {filteredEntries.length === 0 && <p className="px-3 py-10 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>일치하는 항목이 없습니다.</p>}
        </div>
        <p className="mt-2 text-xs" style={{ color: "var(--muted-foreground)" }}>총 {entries.length}개 · 원본과 관리자 수정본을 함께 표시합니다.</p>
      </aside>

      <section className="min-w-0">
        {draft ? (
          <form onSubmit={saveEntry} className="space-y-5">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b pb-4" style={{ borderColor: "var(--border)" }}>
              <div>
                <h2 className="text-xl font-extrabold">{selectedEntry ? "민원 대응 수정" : "새 민원 대응 추가"}</h2>
                {selectedEntry?.updatedAt && <p className="mt-1 text-xs" style={{ color: "var(--muted-foreground)" }}>최근 수정 {new Date(selectedEntry.updatedAt).toLocaleString("ko-KR")}</p>}
              </div>
              <div className="flex flex-wrap gap-2">
                {selectedEntry && (selectedEntry.isCustom || selectedEntry.isModified) && (
                  <button type="button" onClick={() => void removeOrRestore()} disabled={isSaving} className="inline-flex items-center gap-2 rounded-xl border px-4 py-2.5 text-sm font-bold disabled:opacity-50" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
                    {selectedEntry.isCustom ? <Trash2 className="h-4 w-4" /> : <RotateCcw className="h-4 w-4" />}{selectedEntry.isCustom ? "추가 항목 삭제" : "원본 복구"}
                  </button>
                )}
                <button type="submit" disabled={isSaving} className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60" style={{ background: "var(--brand-green)" }}>
                  {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} 저장
                </button>
              </div>
            </div>

            {error && <p role="alert" className="border-l-4 px-4 py-3 text-sm" style={{ background: "#FFF5F3", borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>{error}</p>}
            {message && <p role="status" className="border-l-4 px-4 py-3 text-sm" style={{ background: "#ECF8F2", borderColor: "#72B99B", color: "#126B49" }}>{message}</p>}

            <div className="grid gap-4 rounded-2xl border bg-white p-5 sm:grid-cols-2" style={{ borderColor: "var(--border)" }}>
              <label className="text-sm font-bold">제목<input value={draft.title} onChange={(event) => setDraft((current) => current && ({ ...current, title: event.target.value }))} required className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /></label>
              <label className="text-sm font-bold">유형<select value={draft.entryType} onChange={(event) => setDraft((current) => current && ({ ...current, entryType: event.target.value as "section" | "case" }))} className="mt-2 w-full rounded-xl border bg-white px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }}><option value="case">상황별 대응</option><option value="section">일반 매뉴얼</option></select></label>
              <label className="text-sm font-bold">매뉴얼 분류<input list="manual-groups" value={draft.group} onChange={(event) => setDraft((current) => current && ({ ...current, group: event.target.value }))} required className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /><datalist id="manual-groups">{MANUAL_GROUPS.map((group) => <option key={group} value={group} />)}</datalist></label>
              <label className="text-sm font-bold">카테고리·주제<input value={draft.topic} onChange={(event) => setDraft((current) => current && ({ ...current, topic: event.target.value }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} placeholder="예: 소음, 불법주정차" /></label>
              <label className="text-sm font-bold sm:col-span-2">민원 설명<textarea value={draft.summary} onChange={(event) => setDraft((current) => current && ({ ...current, summary: event.target.value }))} rows={3} className="mt-2 w-full resize-y rounded-xl border px-3 py-3 font-normal leading-6" style={{ borderColor: "var(--border)" }} /></label>
              <label className="text-sm font-bold sm:col-span-2">원문·상세 내용<textarea value={draft.content} onChange={(event) => setDraft((current) => current && ({ ...current, content: event.target.value }))} rows={6} className="mt-2 w-full resize-y rounded-xl border px-3 py-3 font-normal leading-6" style={{ borderColor: "var(--border)" }} /></label>
              <label className="text-sm font-bold">근거 PDF 페이지<input value={draft.sourcePages.join(", ")} onChange={(event) => setDraft((current) => current && ({ ...current, sourcePages: event.target.value.split(/[,\s]+/).map(Number).filter((page) => Number.isInteger(page) && page >= 0) }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} placeholder="예: 58, 59" /></label>
              <label className="text-sm font-bold">원문 경로<input value={draft.breadcrumb.join(" > ")} onChange={(event) => setDraft((current) => current && ({ ...current, breadcrumb: event.target.value.split(">").map((value) => value.trim()).filter(Boolean) }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} placeholder="예: 민원유형별 대응 > 소음" /></label>
              <p className="border-l-4 px-3 py-2 text-xs leading-5 sm:col-span-2" style={{ background: "#FFF8ED", borderColor: "#E08A1E", color: "#8A4C08" }}>현재 백엔드 검색은 제목·카테고리·설명·본문·담당 부서·처리 항목을 자동 검색합니다. 별도 검색 키워드와 연락처 필드는 아직 API에 없습니다.</p>
            </div>

            <StringListEditor label="먼저 확인할 사항" values={draft.intakeQuestions} onChange={(values) => setDraft((current) => current && ({ ...current, intakeQuestions: values }))} />
            <StringListEditor label="지금 해야 할 일" values={draft.immediateActions} onChange={(values) => setDraft((current) => current && ({ ...current, immediateActions: values }))} />
            <StringListEditor label="담당 부서" values={draft.departments} onChange={(values) => setDraft((current) => current && ({ ...current, departments: values }))} placeholder="예: 푸른환경과" />
            <DecisionBranchEditor values={draft.decisionBranches} onChange={(values) => setDraft((current) => current && ({ ...current, decisionBranches: values }))} />
            <StringListEditor label="민원인 안내 문구" values={draft.responseScripts} onChange={(values) => setDraft((current) => current && ({ ...current, responseScripts: values }))} />
            <EscalationRuleEditor values={draft.escalationRules} onChange={(values) => setDraft((current) => current && ({ ...current, escalationRules: values }))} />
            <StringListEditor label="주의사항" values={draft.cautions} onChange={(values) => setDraft((current) => current && ({ ...current, cautions: values }))} />

            <div className="flex justify-end pb-24"><button type="submit" disabled={isSaving} className="inline-flex items-center gap-2 rounded-xl px-6 py-3 text-sm font-bold text-white disabled:opacity-60" style={{ background: "var(--brand-green)" }}>{isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Save className="h-4 w-4" />} 전체 사용자에게 저장</button></div>
          </form>
        ) : (
          <div className="border-y py-16 text-center" style={{ borderColor: "var(--border)" }}><p className="font-bold">수정할 항목을 선택하거나 새 항목을 추가하세요.</p></div>
        )}
      </section>
    </div>
  );
}

function StringListEditor({ label, values, onChange, placeholder = "내용을 입력하세요" }: { label: string; values: string[]; onChange: (values: string[]) => void; placeholder?: string }) {
  const shownValues = values.length ? values : [""];
  const update = (index: number, value: string) => onChange(shownValues.map((item, itemIndex) => itemIndex === index ? value : item));
  const remove = (index: number) => onChange(shownValues.filter((_, itemIndex) => itemIndex !== index));
  return (
    <section className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
      <div className="flex items-center justify-between gap-3"><h3 className="font-extrabold">{label}</h3><button type="button" onClick={() => onChange([...shownValues, ""])} className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-bold" style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}><Plus className="h-3.5 w-3.5" /> 항목 추가</button></div>
      <div className="mt-4 space-y-2">{shownValues.map((value, index) => <div key={`${label}-${index}`} className="flex items-start gap-2"><span className="mt-3 w-5 text-center text-xs font-bold" style={{ color: "var(--brand-green)" }}>{index + 1}</span><textarea value={value} onChange={(event) => update(index, event.target.value)} rows={2} placeholder={placeholder} aria-label={`${label} ${index + 1}`} className="min-w-0 flex-1 resize-y rounded-xl border px-3 py-2.5 text-sm leading-6" style={{ borderColor: "var(--border)" }} /><button type="button" onClick={() => remove(index)} aria-label={`${label} ${index + 1} 삭제`} className="mt-1 rounded-lg p-2.5" style={{ color: "var(--brand-red-dark)" }}><Trash2 className="h-4 w-4" /></button></div>)}</div>
    </section>
  );
}

function DecisionBranchEditor({ values, onChange }: { values: DecisionBranch[]; onChange: (values: DecisionBranch[]) => void }) {
  const update = (index: number, value: DecisionBranch) => onChange(values.map((item, itemIndex) => itemIndex === index ? value : item));
  return (
    <section className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
      <div className="flex items-center justify-between gap-3"><h3 className="font-extrabold">상황별 분기</h3><button type="button" onClick={() => onChange([...values, { condition: "", actions: [], response: "" }])} className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-bold" style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}><Plus className="h-3.5 w-3.5" /> 분기 추가</button></div>
      <div className="mt-4 space-y-4">{values.map((branch, index) => <div key={`branch-${index}`} className="relative border-l-2 pl-4" style={{ borderColor: "var(--brand-green)" }}><button type="button" onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))} aria-label={`상황별 분기 ${index + 1} 삭제`} className="absolute right-0 top-0 rounded-lg p-2" style={{ color: "var(--brand-red-dark)" }}><Trash2 className="h-4 w-4" /></button><label className="block pr-10 text-sm font-bold">조건<input value={branch.condition} onChange={(event) => update(index, { ...branch, condition: event.target.value })} className="mt-2 w-full rounded-xl border px-3 py-2.5 font-normal" style={{ borderColor: "var(--border)" }} /></label><label className="mt-3 block text-sm font-bold">처리 내용 <span className="font-normal" style={{ color: "var(--muted-foreground)" }}>한 줄에 한 항목</span><textarea value={branch.actions.join("\n")} onChange={(event) => update(index, { ...branch, actions: event.target.value.split("\n") })} rows={3} className="mt-2 w-full resize-y rounded-xl border px-3 py-2.5 font-normal leading-6" style={{ borderColor: "var(--border)" }} /></label><label className="mt-3 block text-sm font-bold">안내 문구<textarea value={branch.response} onChange={(event) => update(index, { ...branch, response: event.target.value })} rows={2} className="mt-2 w-full resize-y rounded-xl border px-3 py-2.5 font-normal leading-6" style={{ borderColor: "var(--border)" }} /></label></div>)}{values.length === 0 && <p className="py-3 text-sm" style={{ color: "var(--muted-foreground)" }}>등록된 상황별 분기가 없습니다.</p>}</div>
    </section>
  );
}

function EscalationRuleEditor({ values, onChange }: { values: EscalationRule[]; onChange: (values: EscalationRule[]) => void }) {
  const update = (index: number, value: EscalationRule) => onChange(values.map((item, itemIndex) => itemIndex === index ? value : item));
  return (
    <section className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
      <div className="flex items-center justify-between gap-3"><h3 className="font-extrabold">상급 보고·이관 규칙</h3><button type="button" onClick={() => onChange([...values, { condition: "", action: "" }])} className="inline-flex items-center gap-1 rounded-lg border px-3 py-1.5 text-xs font-bold" style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}><Plus className="h-3.5 w-3.5" /> 규칙 추가</button></div>
      <div className="mt-4 space-y-3">{values.map((rule, index) => <div key={`rule-${index}`} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]"><input value={rule.condition} onChange={(event) => update(index, { ...rule, condition: event.target.value })} aria-label={`보고 조건 ${index + 1}`} placeholder="보고 조건" className="rounded-xl border px-3 py-2.5 text-sm" style={{ borderColor: "var(--border)" }} /><input value={rule.action} onChange={(event) => update(index, { ...rule, action: event.target.value })} aria-label={`보고 조치 ${index + 1}`} placeholder="보고·이관 조치" className="rounded-xl border px-3 py-2.5 text-sm" style={{ borderColor: "var(--border)" }} /><button type="button" onClick={() => onChange(values.filter((_, itemIndex) => itemIndex !== index))} aria-label={`보고 규칙 ${index + 1} 삭제`} className="rounded-lg p-2.5" style={{ color: "var(--brand-red-dark)" }}><Trash2 className="h-4 w-4" /></button></div>)}{values.length === 0 && <p className="py-3 text-sm" style={{ color: "var(--muted-foreground)" }}>등록된 보고 규칙이 없습니다.</p>}</div>
    </section>
  );
}
