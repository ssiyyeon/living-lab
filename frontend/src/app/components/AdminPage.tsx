import { useEffect, useMemo, useState } from "react";
import {
  BookOpenText,
  FilePenLine,
  History,
  KeyRound,
  Loader2,
  Pencil,
  Plus,
  RotateCcw,
  Search,
  Trash2,
  UserCog,
  UsersRound,
  X,
} from "lucide-react";
import {
  createAdminContact,
  deleteAdminContact,
  fetchAdminContacts,
  fetchAdminGuides,
  resetAdminGuide,
  updateAdminContact,
  updateAdminGuide,
  type AdminContactInput,
  type AdminGuideInput,
  type ContactDirectoryEntry,
  type QuickGuide,
} from "../api/search";
import { AdminComplaintManager } from "./AdminComplaintManager";

type AdminTab = "complaints" | "guides" | "contacts" | "keywords" | "users" | "history";

const ADMIN_TABS = [
  { id: "complaints" as const, label: "민원 대응 관리", icon: FilePenLine },
  { id: "guides" as const, label: "업무 안내 관리", icon: BookOpenText },
  { id: "contacts" as const, label: "전화번호부", icon: UsersRound },
  { id: "keywords" as const, label: "검색 키워드 관리", icon: KeyRound },
  { id: "users" as const, label: "사용자 계정 관리", icon: UserCog },
  { id: "history" as const, label: "변경 이력", icon: History },
];

const GROUPS = ["대표·당직", "구청 내부", "긴급·상급기관", "담당 부서", "시설·유관기관"];
const EMPTY_CONTACT: AdminContactInput = {
  group: "담당 부서",
  organization: "",
  label: "",
  phone: "",
  note: "",
  sourceUrl: "",
};

function guideToForm(guide: QuickGuide): AdminGuideInput {
  return {
    title: guide.title,
    description: guide.description,
    sections: guide.sections.map((section) => ({
      title: section.title,
      timeLabel: section.timeLabel,
      steps: [...section.steps],
    })),
    cautions: [...guide.cautions],
  };
}

export function AdminPage({ onGuidesChanged, onManualChanged }: { onGuidesChanged?: () => void; onManualChanged?: () => void }) {
  const [activeTab, setActiveTab] = useState<AdminTab>("complaints");
  const [error, setError] = useState("");

  const [guides, setGuides] = useState<QuickGuide[]>([]);
  const [selectedGuideId, setSelectedGuideId] = useState("");
  const [guideForm, setGuideForm] = useState<AdminGuideInput | null>(null);
  const [isGuideLoading, setIsGuideLoading] = useState(true);
  const [isGuideSaving, setIsGuideSaving] = useState(false);

  const [contacts, setContacts] = useState<ContactDirectoryEntry[]>([]);
  const [query, setQuery] = useState("");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [contactForm, setContactForm] = useState<AdminContactInput>(EMPTY_CONTACT);
  const [isContactFormOpen, setIsContactFormOpen] = useState(false);
  const [isContactLoading, setIsContactLoading] = useState(true);
  const [isContactSaving, setIsContactSaving] = useState(false);

  const loadGuides = async (preferredId?: string) => {
    setError("");
    try {
      const response = await fetchAdminGuides();
      setGuides(response.guides);
      const nextId = preferredId || selectedGuideId || response.guides[0]?.id || "";
      const selected = response.guides.find((guide) => guide.id === nextId) ?? response.guides[0];
      setSelectedGuideId(selected?.id ?? "");
      setGuideForm(selected ? guideToForm(selected) : null);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "업무 안내를 불러오지 못했습니다.");
    } finally {
      setIsGuideLoading(false);
    }
  };

  const loadContacts = async () => {
    setError("");
    try {
      const response = await fetchAdminContacts();
      setContacts(response.contacts);
    } catch (loadError) {
      setError(loadError instanceof Error ? loadError.message : "연락처를 불러오지 못했습니다.");
    } finally {
      setIsContactLoading(false);
    }
  };

  useEffect(() => {
    void Promise.all([loadGuides(), loadContacts()]);
  }, []);

  const filteredContacts = useMemo(() => {
    const normalized = query.replace(/\s+/g, "").toLowerCase();
    if (!normalized) return contacts;
    return contacts.filter((contact) =>
      [contact.group, contact.organization, contact.label, contact.phone, contact.note]
        .join(" ")
        .replace(/\s+/g, "")
        .toLowerCase()
        .includes(normalized),
    );
  }, [contacts, query]);

  const selectGuide = (guideId: string) => {
    const guide = guides.find((item) => item.id === guideId);
    setSelectedGuideId(guideId);
    setGuideForm(guide ? guideToForm(guide) : null);
    setError("");
  };

  const updateSection = (
    sectionIndex: number,
    field: "title" | "timeLabel" | "steps",
    value: string | string[],
  ) => {
    setGuideForm((current) => current && ({
      ...current,
      sections: current.sections.map((section, index) =>
        index === sectionIndex ? { ...section, [field]: value } : section,
      ),
    }));
  };

  const saveGuide = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!guideForm || !selectedGuideId) return;
    if (!guideForm.title.trim() || !guideForm.description.trim()) {
      setError("제목과 설명을 입력해 주세요.");
      return;
    }
    setIsGuideSaving(true);
    setError("");
    try {
      const updated = await updateAdminGuide(selectedGuideId, guideForm);
      setGuides((current) => current.map((guide) => guide.id === updated.id ? updated : guide));
      setGuideForm(guideToForm(updated));
      onGuidesChanged?.();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "업무 안내를 저장하지 못했습니다.");
    } finally {
      setIsGuideSaving(false);
    }
  };

  const restoreGuide = async () => {
    if (!selectedGuideId || !window.confirm("이 업무 안내를 원본 매뉴얼 내용으로 되돌릴까요?")) return;
    setIsGuideSaving(true);
    setError("");
    try {
      await resetAdminGuide(selectedGuideId);
      await loadGuides(selectedGuideId);
      onGuidesChanged?.();
    } catch (restoreError) {
      setError(restoreError instanceof Error ? restoreError.message : "원본으로 되돌리지 못했습니다.");
    } finally {
      setIsGuideSaving(false);
    }
  };

  const closeContactForm = () => {
    setIsContactFormOpen(false);
    setEditingId(null);
    setContactForm(EMPTY_CONTACT);
    setError("");
  };

  const openContactEdit = (contact: ContactDirectoryEntry) => {
    setEditingId(contact.id);
    setContactForm({
      group: contact.group,
      organization: contact.organization,
      label: contact.label,
      phone: contact.phone,
      note: contact.note,
      sourceUrl: contact.sourceUrl,
    });
    setIsContactFormOpen(true);
    setError("");
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const saveContact = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!contactForm.organization.trim() || !contactForm.label.trim() || !contactForm.phone.trim()) {
      setError("기관·담당 업무·전화번호를 모두 입력해 주세요.");
      return;
    }
    setIsContactSaving(true);
    setError("");
    try {
      if (editingId) await updateAdminContact(editingId, contactForm);
      else await createAdminContact(contactForm);
      closeContactForm();
      setIsContactLoading(true);
      await loadContacts();
    } catch (saveError) {
      setError(saveError instanceof Error ? saveError.message : "연락처를 저장하지 못했습니다.");
    } finally {
      setIsContactSaving(false);
    }
  };

  const hideContact = async (contact: ContactDirectoryEntry) => {
    if (!window.confirm(`${contact.organization} 연락처를 전체 사용자 화면에서 숨길까요?`)) return;
    setError("");
    try {
      await deleteAdminContact(contact.id);
      setContacts((current) => current.filter((item) => item.id !== contact.id));
    } catch (deleteError) {
      setError(deleteError instanceof Error ? deleteError.message : "연락처를 숨기지 못했습니다.");
    }
  };

  return (
    <section>
      <header className="border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <span className="inline-flex items-center gap-2 text-sm font-bold" style={{ color: "var(--brand-green)" }}>
          <UsersRound className="h-5 w-5" /> 관리자
        </span>
        <h1 className="mt-3 text-3xl font-extrabold">운영 정보 관리</h1>
        <p className="mt-2 text-base leading-7" style={{ color: "var(--muted-foreground)" }}>
          현재 연결된 업무 안내·전화번호부 API를 관리하고, 다음 단계의 운영 기능을 준비합니다.
        </p>
      </header>

      <div className="mt-6 flex gap-1 overflow-x-auto border-b" style={{ borderColor: "var(--border)" }} role="tablist" aria-label="관리자 기능">
        {ADMIN_TABS.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={activeTab === id}
            onClick={() => { setActiveTab(id); setError(""); }}
            className="flex shrink-0 items-center gap-2 border-b-2 px-3 py-3 text-sm font-extrabold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]"
            style={{ borderColor: activeTab === id ? "var(--brand-green)" : "transparent", color: activeTab === id ? "var(--brand-green)" : "var(--muted-foreground)" }}
          >
            <Icon className="h-4.5 w-4.5" /> {label}
          </button>
        ))}
      </div>

      {error && <p role="alert" className="mt-5 rounded-xl border px-4 py-3 text-sm" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>{error}</p>}

      {activeTab === "guides" ? (
        isGuideLoading ? (
          <Loading label="업무 안내를 불러오고 있습니다." />
        ) : guideForm ? (
          <form onSubmit={saveGuide} className="mt-6">
            <div className="grid gap-5 lg:grid-cols-[220px_minmax(0,1fr)]">
              <nav className="self-start overflow-hidden rounded-2xl border bg-white p-2" style={{ borderColor: "var(--border)" }} aria-label="수정할 업무 안내">
                {guides.map((guide) => (
                  <button key={guide.id} type="button" onClick={() => selectGuide(guide.id)} className="w-full rounded-xl px-3 py-3 text-left text-sm font-bold" style={{ background: selectedGuideId === guide.id ? "#E7F0FC" : "transparent", color: selectedGuideId === guide.id ? "#0B4DA2" : "var(--muted-foreground)" }}>
                    {guide.title}
                  </button>
                ))}
              </nav>

              <div className="min-w-0 space-y-5">
                <div className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
                  <h2 className="text-lg font-extrabold">기본 내용</h2>
                  <label className="mt-4 block text-sm font-bold">제목
                    <input value={guideForm.title} onChange={(event) => setGuideForm((current) => current && ({ ...current, title: event.target.value }))} className="mt-2 w-full rounded-xl border px-4 py-3 font-normal" style={{ borderColor: "var(--border)" }} />
                  </label>
                  <label className="mt-4 block text-sm font-bold">화면 설명
                    <textarea value={guideForm.description} onChange={(event) => setGuideForm((current) => current && ({ ...current, description: event.target.value }))} rows={3} className="mt-2 w-full resize-y rounded-xl border px-4 py-3 font-normal leading-6" style={{ borderColor: "var(--border)" }} />
                  </label>
                </div>

                {guideForm.sections.map((section, sectionIndex) => (
                  <div key={`${selectedGuideId}-${sectionIndex}`} className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
                    <div className="flex items-center justify-between gap-3">
                      <h2 className="text-lg font-extrabold">안내 단계 {sectionIndex + 1}</h2>
                      <button type="button" onClick={() => setGuideForm((current) => current && ({ ...current, sections: current.sections.filter((_, index) => index !== sectionIndex) }))} className="rounded-full p-2" style={{ color: "var(--brand-red-dark)" }} aria-label={`안내 단계 ${sectionIndex + 1} 삭제`}><Trash2 className="h-4 w-4" /></button>
                    </div>
                    <div className="mt-4 grid gap-4 sm:grid-cols-2">
                      <label className="block text-sm font-bold">단계 제목
                        <input value={section.title} onChange={(event) => updateSection(sectionIndex, "title", event.target.value)} className="mt-2 w-full rounded-xl border px-4 py-3 font-normal" style={{ borderColor: "var(--border)" }} />
                      </label>
                      <label className="block text-sm font-bold">시간·상황 표시
                        <input value={section.timeLabel} onChange={(event) => updateSection(sectionIndex, "timeLabel", event.target.value)} className="mt-2 w-full rounded-xl border px-4 py-3 font-normal" style={{ borderColor: "var(--border)" }} placeholder="예: 근무 시작 시" />
                      </label>
                    </div>
                    <label className="mt-4 block text-sm font-bold">처리 내용 <span className="font-normal" style={{ color: "var(--muted-foreground)" }}>한 줄에 한 항목씩 입력</span>
                      <textarea value={section.steps.join("\n")} onChange={(event) => updateSection(sectionIndex, "steps", event.target.value.split("\n"))} rows={Math.max(4, section.steps.length + 1)} className="mt-2 w-full resize-y rounded-xl border px-4 py-3 font-normal leading-7" style={{ borderColor: "var(--border)" }} />
                    </label>
                  </div>
                ))}

                <button type="button" onClick={() => setGuideForm((current) => current && ({ ...current, sections: [...current.sections, { title: "새 안내 단계", timeLabel: "", steps: [""] }] }))} className="inline-flex items-center gap-2 rounded-xl border bg-white px-4 py-3 text-sm font-bold" style={{ borderColor: "var(--brand-green)", color: "var(--brand-green)" }}><Plus className="h-4 w-4" /> 안내 단계 추가</button>

                <div className="rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
                  <label className="block text-sm font-bold">주의사항 <span className="font-normal" style={{ color: "var(--muted-foreground)" }}>한 줄에 한 항목씩 입력</span>
                    <textarea value={guideForm.cautions.join("\n")} onChange={(event) => setGuideForm((current) => current && ({ ...current, cautions: event.target.value.split("\n") }))} rows={4} className="mt-2 w-full resize-y rounded-xl border px-4 py-3 font-normal leading-7" style={{ borderColor: "var(--border)" }} />
                  </label>
                </div>

                <div className="flex flex-wrap justify-end gap-2 pb-24">
                  <button type="button" onClick={() => void restoreGuide()} disabled={isGuideSaving} className="inline-flex items-center gap-2 rounded-xl border px-4 py-3 text-sm font-bold" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}><RotateCcw className="h-4 w-4" /> 원본으로 되돌리기</button>
                  <button type="submit" disabled={isGuideSaving} className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold text-white disabled:opacity-60" style={{ background: "var(--brand-green)" }}>{isGuideSaving && <Loader2 className="h-4 w-4 animate-spin" />} 전체 사용자에게 저장</button>
                </div>
              </div>
            </div>
          </form>
        ) : null
      ) : activeTab === "contacts" ? (
        <div>
          <div className="mt-6 flex flex-wrap gap-3">
            <label className="flex min-w-[260px] flex-1 items-center rounded-xl border bg-white px-4" style={{ borderColor: "var(--border)" }}>
              <Search className="mr-3 h-5 w-5" style={{ color: "var(--muted-foreground)" }} />
              <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="부서·업무·전화번호 검색" className="min-w-0 flex-1 bg-transparent py-3.5 text-base outline-none" />
            </label>
            <button type="button" onClick={() => { if (isContactFormOpen) closeContactForm(); else setIsContactFormOpen(true); }} className="inline-flex items-center gap-2 rounded-xl px-5 py-3 text-sm font-bold text-white" style={{ background: "var(--brand-green)" }}>
              {isContactFormOpen ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}{isContactFormOpen ? "닫기" : "연락처 추가"}
            </button>
          </div>

          {isContactFormOpen && (
            <form onSubmit={saveContact} className="mt-5 rounded-2xl border bg-white p-5" style={{ borderColor: "var(--border)" }}>
              <h2 className="text-lg font-extrabold">{editingId ? "공용 연락처 수정" : "새 공용 연락처"}</h2>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                <label className="block text-sm font-bold">분류<select value={contactForm.group} onChange={(event) => setContactForm((current) => ({ ...current, group: event.target.value }))} className="mt-2 w-full rounded-xl border bg-white px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }}>{GROUPS.map((group) => <option key={group}>{group}</option>)}</select></label>
                <label className="block text-sm font-bold">기관·부서<input value={contactForm.organization} onChange={(event) => setContactForm((current) => ({ ...current, organization: event.target.value }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /></label>
                <label className="block text-sm font-bold">담당 업무<input value={contactForm.label} onChange={(event) => setContactForm((current) => ({ ...current, label: event.target.value }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /></label>
                <label className="block text-sm font-bold">전화번호<input value={contactForm.phone} onChange={(event) => setContactForm((current) => ({ ...current, phone: event.target.value }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /></label>
                <label className="block text-sm font-bold sm:col-span-2">메모<input value={contactForm.note} onChange={(event) => setContactForm((current) => ({ ...current, note: event.target.value }))} className="mt-2 w-full rounded-xl border px-3 py-3 font-normal" style={{ borderColor: "var(--border)" }} /></label>
              </div>
              <div className="mt-5 flex justify-end gap-2"><button type="button" onClick={closeContactForm} className="rounded-xl px-4 py-2.5 text-sm font-bold" style={{ color: "var(--muted-foreground)" }}>취소</button><button type="submit" disabled={isContactSaving} className="inline-flex items-center gap-2 rounded-xl px-5 py-2.5 text-sm font-bold text-white disabled:opacity-60" style={{ background: "var(--brand-green)" }}>{isContactSaving && <Loader2 className="h-4 w-4 animate-spin" />}{editingId ? "수정 저장" : "전체에 추가"}</button></div>
            </form>
          )}

          {isContactLoading ? <Loading label="연락처를 불러오고 있습니다." /> : (
            <div className="mt-6 overflow-hidden rounded-2xl border bg-white" style={{ borderColor: "var(--border)" }}>
              {filteredContacts.map((contact, index) => (
                <div key={contact.id} className={`flex items-center gap-4 px-5 py-4 ${index ? "border-t" : ""}`} style={{ borderColor: "var(--border)" }}>
                  <div className="min-w-0 flex-1"><div className="flex flex-wrap items-center gap-2"><strong className="text-base">{contact.organization}</strong><span className="rounded-full bg-[#F2F6FC] px-2.5 py-1 text-xs" style={{ color: "var(--muted-foreground)" }}>{contact.group}</span></div><p className="mt-1 text-sm" style={{ color: "var(--muted-foreground)" }}>{contact.label}{contact.note ? ` · ${contact.note}` : ""}</p><p className="mt-1 text-sm font-bold" style={{ color: "var(--brand-green)" }}>{contact.phone}</p></div>
                  <button type="button" onClick={() => openContactEdit(contact)} aria-label={`${contact.organization} 수정`} className="rounded-full p-2.5 hover:bg-[#F2F6FC]" style={{ color: "var(--muted-foreground)" }}><Pencil className="h-4 w-4" /></button>
                  <button type="button" onClick={() => void hideContact(contact)} aria-label={`${contact.organization} 숨기기`} className="rounded-full p-2.5 hover:bg-[#FFF4F3]" style={{ color: "var(--brand-red-dark)" }}><Trash2 className="h-4 w-4" /></button>
                </div>
              ))}
              {filteredContacts.length === 0 && <p className="py-16 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>일치하는 연락처가 없습니다.</p>}
            </div>
          )}
        </div>
      ) : activeTab === "complaints" ? (
        <AdminComplaintManager onChanged={onManualChanged} />
      ) : activeTab === "keywords" ? (
        <KeywordManagementShell />
      ) : activeTab === "users" ? (
        <ApiPendingState
          title="사용자 계정 관리"
          description="일반 직원 계정 목록·초대·권한 변경 API가 필요합니다. 현재 로그인과 최초 관리자 생성 API는 그대로 유지됩니다."
          endpoint="GET/POST/PATCH /api/admin/users"
        />
      ) : (
        <ApiPendingState
          title="변경 이력"
          description="실제 변경 이력 데이터가 없어 빈 상태로 표시합니다. 백엔드에서 대상 항목·수정자·수정 시간·변경 내용·버전을 제공해야 합니다."
          endpoint="GET /api/admin/change-history"
        />
      )}
    </section>
  );
}

function KeywordManagementShell() {
  return (
    <section className="mt-6">
      <div className="border-l-4 px-4 py-3 text-sm leading-6" style={{ background: "#FFF8ED", borderColor: "#E08A1E", color: "#8A4C08" }}>
        검색 키워드 전용 API가 없어 실제 데이터를 표시하거나 저장하지 않습니다.
      </div>
      <div className="mt-6 border-y py-10 text-center" style={{ borderColor: "var(--border)" }}>
        <KeyRound className="mx-auto h-8 w-8" style={{ color: "var(--muted-foreground)" }} />
        <h2 className="mt-3 text-lg font-extrabold">등록된 키워드를 불러올 수 없습니다</h2>
        <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>민원 대응 항목별 키워드 조회·추가·삭제 API가 연결되면 태그 편집 UI를 활성화합니다.</p>
        <button type="button" disabled className="mt-5 rounded-xl border px-4 py-2.5 text-sm font-bold opacity-50" style={{ borderColor: "var(--border)" }}>+ 키워드 추가</button>
      </div>
      <p className="mt-4 text-xs" style={{ color: "var(--muted-foreground)" }}>TODO: GET/PUT /api/admin/search-keywords 연결</p>
    </section>
  );
}

function ApiPendingState({ title, description, endpoint }: { title: string; description: string; endpoint: string }) {
  return (
    <section className="mt-6 border-y py-14 text-center" style={{ borderColor: "var(--border)" }}>
      <History className="mx-auto h-8 w-8" style={{ color: "var(--muted-foreground)" }} />
      <h2 className="mt-3 text-xl font-extrabold">{title}</h2>
      <p className="mx-auto mt-3 max-w-xl text-sm leading-7" style={{ color: "var(--muted-foreground)" }}>{description}</p>
      <code className="mt-4 inline-block rounded-lg bg-[#F2F4F7] px-3 py-2 text-xs">필요 API · {endpoint}</code>
    </section>
  );
}

function Loading({ label }: { label: string }) {
  return <div className="flex min-h-60 items-center justify-center gap-2" style={{ color: "var(--muted-foreground)" }}><Loader2 className="h-5 w-5 animate-spin" /> {label}</div>;
}
