import {
  BookUser,
  Loader2,
  Pencil,
  Phone,
  Plus,
  Search,
  Star,
  Trash2,
  X,
} from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  fetchContactDirectory,
  type ContactDirectoryEntry,
  type ContactDirectoryResponse,
} from "../api/search";
import { CopyButton } from "./CopyButton";

const PINNED_CONTACTS_KEY = "yuseong-duty-pinned-contacts-v1";
const CUSTOM_CONTACTS_KEY = "yuseong-duty-custom-contacts-v1";
const CONTACT_OVERRIDES_KEY = "yuseong-duty-contact-overrides-v1";
const HIDDEN_CONTACTS_KEY = "yuseong-duty-hidden-contacts-v1";

const GROUP_ORDER = [
  "내 연락처",
  "대표·당직",
  "구청 내부",
  "긴급·상급기관",
  "담당 부서",
  "시설·유관기관",
];

interface ContactDirectoryDrawerProps {
  onClose: () => void;
}

interface ContactFormState {
  organization: string;
  label: string;
  phone: string;
  note: string;
}

const EMPTY_FORM: ContactFormState = {
  organization: "",
  label: "",
  phone: "",
  note: "",
};

function loadStoredArray<T>(key: string): T[] {
  try {
    const value = JSON.parse(window.localStorage.getItem(key) ?? "[]");
    return Array.isArray(value) ? value : [];
  } catch {
    return [];
  }
}

function ContactRow({
  contact,
  isPinned,
  onTogglePin,
  onEdit,
}: {
  contact: ContactDirectoryEntry;
  isPinned: boolean;
  onTogglePin: (id: string) => void;
  onEdit: (contact: ContactDirectoryEntry) => void;
}) {
  return (
    <div className="flex items-center gap-3 bg-white px-4 py-3.5">
      <div className="min-w-0 flex-1">
        <span className="block truncate text-sm font-bold">{contact.organization}</span>
        <span
          className="mt-0.5 block truncate text-[11px]"
          style={{ color: "var(--muted-foreground)" }}
        >
          {contact.label}
          {contact.note ? ` · ${contact.note}` : ""}
        </span>
        <span
          className="mt-1 block text-[13px] font-bold"
          style={{ color: "var(--brand-green)" }}
        >
          {contact.phone}
        </span>
      </div>
      <CopyButton value={contact.phone} label="번호 복사" compact />
      <button
        type="button"
        onClick={() => onEdit(contact)}
        aria-label={`${contact.organization} 연락처 수정`}
        title="연락처 수정"
        className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full transition-colors hover:bg-[#F7FCFF]"
        style={{ color: "var(--muted-foreground)" }}
      >
        <Pencil className="h-4 w-4" />
      </button>
      <button
        type="button"
        onClick={() => onTogglePin(contact.id)}
        aria-label={`${contact.organization} ${isPinned ? "고정 해제" : "상단에 고정"}`}
        title={isPinned ? "고정 해제" : "상단에 고정"}
        className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full transition-colors hover:bg-[#F7FCFF]"
        style={{ color: isPinned ? "var(--brand-red)" : "var(--muted-foreground)" }}
      >
        <Star className="h-4.5 w-4.5" fill={isPinned ? "currentColor" : "none"} />
      </button>
      <a
        href={`tel:${contact.phone}`}
        aria-label={`${contact.organization} 전화 걸기`}
        title="전화 걸기"
        className="inline-flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full border"
        style={{ borderColor: "var(--brand-green)", color: "var(--brand-green)" }}
      >
        <Phone className="h-4 w-4" />
      </a>
    </div>
  );
}

export function ContactDirectoryDrawer({ onClose }: ContactDirectoryDrawerProps) {
  const [directory, setDirectory] = useState<ContactDirectoryResponse | null>(null);
  const [loadError, setLoadError] = useState("");
  const [query, setQuery] = useState("");
  const [isAdding, setIsAdding] = useState(false);
  const [editingContactId, setEditingContactId] = useState<string | null>(null);
  const [form, setForm] = useState<ContactFormState>(EMPTY_FORM);
  const [formError, setFormError] = useState("");
  const [pinnedIds, setPinnedIds] = useState<string[]>(() =>
    loadStoredArray<string>(PINNED_CONTACTS_KEY),
  );
  const [customContacts, setCustomContacts] = useState<ContactDirectoryEntry[]>(() =>
    loadStoredArray<ContactDirectoryEntry>(CUSTOM_CONTACTS_KEY),
  );
  const [contactOverrides, setContactOverrides] = useState<ContactDirectoryEntry[]>(() =>
    loadStoredArray<ContactDirectoryEntry>(CONTACT_OVERRIDES_KEY),
  );
  const [hiddenContactIds, setHiddenContactIds] = useState<string[]>(() =>
    loadStoredArray<string>(HIDDEN_CONTACTS_KEY),
  );

  useEffect(() => {
    let isMounted = true;

    fetchContactDirectory()
      .then((response) => {
        if (isMounted) setDirectory(response);
      })
      .catch((error) => {
        if (!isMounted) return;
        setLoadError(
          error instanceof Error ? error.message : "전화번호부를 불러오지 못했습니다.",
        );
      });

    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    window.localStorage.setItem(PINNED_CONTACTS_KEY, JSON.stringify(pinnedIds));
  }, [pinnedIds]);

  useEffect(() => {
    window.localStorage.setItem(CUSTOM_CONTACTS_KEY, JSON.stringify(customContacts));
  }, [customContacts]);

  useEffect(() => {
    window.localStorage.setItem(CONTACT_OVERRIDES_KEY, JSON.stringify(contactOverrides));
  }, [contactOverrides]);

  useEffect(() => {
    window.localStorage.setItem(HIDDEN_CONTACTS_KEY, JSON.stringify(hiddenContactIds));
  }, [hiddenContactIds]);

  const allContacts = useMemo(() => {
    const overridesById = new Map(
      contactOverrides.map((contact) => [contact.id, contact]),
    );
    const officialContacts = (directory?.contacts ?? [])
      .filter((contact) => !hiddenContactIds.includes(contact.id))
      .map((contact) => overridesById.get(contact.id) ?? contact);

    return [...customContacts, ...officialContacts];
  }, [contactOverrides, customContacts, directory, hiddenContactIds]);

  const filteredContacts = useMemo(() => {
    const normalizedQuery = query.replace(/\s+/g, "").toLowerCase();
    if (!normalizedQuery) return allContacts;

    return allContacts.filter((contact) =>
      [
        contact.organization,
        contact.label,
        contact.phone,
        contact.note,
        contact.group,
      ]
        .join(" ")
        .replace(/\s+/g, "")
        .toLowerCase()
        .includes(normalizedQuery),
    );
  }, [allContacts, query]);

  const pinnedContacts = filteredContacts.filter((contact) => pinnedIds.includes(contact.id));
  const groupedContacts = GROUP_ORDER.map((group) => ({
    group,
    contacts: filteredContacts.filter(
      (contact) => contact.group === group && !pinnedIds.includes(contact.id),
    ),
  })).filter(({ contacts }) => contacts.length > 0);

  const togglePin = (id: string) => {
    setPinnedIds((current) =>
      current.includes(id)
        ? current.filter((pinnedId) => pinnedId !== id)
        : [id, ...current],
    );
  };

  const resetForm = () => {
    setForm(EMPTY_FORM);
    setFormError("");
    setEditingContactId(null);
    setIsAdding(false);
  };

  const startEditContact = (contact: ContactDirectoryEntry) => {
    setEditingContactId(contact.id);
    setForm({
      organization: contact.organization,
      label: contact.label,
      phone: contact.phone,
      note: contact.note,
    });
    setFormError("");
    setIsAdding(true);
  };

  const handleSaveContact = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const organization = form.organization.trim();
    const phone = form.phone.trim();

    if (!organization || !phone) {
      setFormError("이름과 전화번호를 입력해 주세요.");
      return;
    }

    if (!/^[0-9+()\-\s]{2,30}$/.test(phone)) {
      setFormError("전화번호 형식을 확인해 주세요.");
      return;
    }

    if (editingContactId) {
      const existing = allContacts.find((contact) => contact.id === editingContactId);
      if (!existing) {
        setFormError("수정할 연락처를 찾지 못했습니다.");
        return;
      }

      const updatedContact: ContactDirectoryEntry = {
        ...existing,
        organization,
        label: form.label.trim() || "업무 연락처",
        phone,
        note: form.note.trim(),
      };

      if (editingContactId.startsWith("custom_")) {
        setCustomContacts((current) =>
          current.map((contact) =>
            contact.id === editingContactId ? updatedContact : contact,
          ),
        );
      } else {
        setContactOverrides((current) => [
          updatedContact,
          ...current.filter((contact) => contact.id !== editingContactId),
        ]);
      }
    } else {
      const contact: ContactDirectoryEntry = {
        id: `custom_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
        group: "내 연락처",
        organization,
        label: form.label.trim() || "직접 추가",
        phone,
        note: form.note.trim(),
        source: "사용자 추가",
        sourceUrl: "",
      };

      setCustomContacts((current) => [contact, ...current]);
    }

    resetForm();
  };

  const handleDeleteContact = () => {
    if (!editingContactId) return;

    const contact = allContacts.find((item) => item.id === editingContactId);
    if (!contact) {
      setFormError("삭제할 연락처를 찾지 못했습니다.");
      return;
    }

    if (!window.confirm(`${contact.organization} 연락처를 이 전화번호부에서 삭제할까요?`)) {
      return;
    }

    if (editingContactId.startsWith("custom_")) {
      setCustomContacts((current) =>
        current.filter((item) => item.id !== editingContactId),
      );
    } else {
      setHiddenContactIds((current) =>
        current.includes(editingContactId)
          ? current
          : [editingContactId, ...current],
      );
      setContactOverrides((current) =>
        current.filter((item) => item.id !== editingContactId),
      );
    }

    setPinnedIds((current) =>
      current.filter((id) => id !== editingContactId),
    );
    resetForm();
  };

  return (
    <aside
      id="contact-directory-drawer"
      role="dialog"
      aria-modal="true"
      aria-labelledby="contact-directory-title"
      className="fixed inset-x-0 bottom-0 z-50 flex max-h-[90vh] flex-col overflow-hidden rounded-t-3xl border bg-white sm:inset-x-auto sm:bottom-3 sm:right-3 sm:top-3 sm:max-h-none sm:w-[min(460px,calc(100vw-24px))] sm:rounded-3xl"
      style={{ borderColor: "var(--border)" }}
    >
      <header className="flex items-start justify-between gap-4 border-b px-5 py-5" style={{ borderColor: "var(--border)" }}>
        <div>
          <div className="flex items-center gap-2">
            <BookUser className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
            <h2 id="contact-directory-title" className="text-xl font-extrabold">전화번호부</h2>
          </div>
          <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--muted-foreground)" }}>
            매뉴얼과 공개 부서 연락처를 모았습니다.
          </p>
        </div>
        <button
          type="button"
          onClick={onClose}
          aria-label="전화번호부 닫기"
          className="inline-flex h-10 w-10 items-center justify-center rounded-xl border"
          style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
        >
          <X className="h-5 w-5" />
        </button>
      </header>

      <div className="border-b px-4 py-4 sm:px-5" style={{ borderColor: "var(--border)" }}>
        <div className="flex gap-2">
          <label className="flex min-w-0 flex-1 items-center rounded-xl border bg-white px-3" style={{ borderColor: "var(--border)" }}>
            <Search className="mr-2 h-4 w-4 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="부서·업무·번호 검색"
              aria-label="전화번호부 검색"
              className="min-w-0 flex-1 bg-transparent py-2.5 text-sm outline-none"
            />
          </label>
          <button
            type="button"
            onClick={() => {
              if (isAdding) {
                resetForm();
              } else {
                setEditingContactId(null);
                setForm(EMPTY_FORM);
                setFormError("");
                setIsAdding(true);
              }
            }}
            aria-expanded={isAdding}
            aria-controls="contact-form"
            className="inline-flex flex-shrink-0 items-center gap-1.5 rounded-xl border px-3 text-xs font-bold"
            style={{ borderColor: "var(--brand-green)", color: "var(--brand-green)" }}
          >
            <Plus className="h-4 w-4" />
            추가
          </button>
        </div>

        {isAdding && (
          <form id="contact-form" onSubmit={handleSaveContact} className="mt-4 border-t pt-4" style={{ borderColor: "var(--border)" }}>
            <h3 className="mb-3 text-sm font-extrabold">
              {editingContactId ? "연락처 수정" : "새 연락처 추가"}
            </h3>
            <div className="grid grid-cols-2 gap-2">
              <input
                value={form.organization}
                onChange={(event) => setForm((current) => ({ ...current, organization: event.target.value }))}
                placeholder="이름 또는 기관 *"
                aria-label="연락처 이름 또는 기관"
                className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-[#036EB8]"
                style={{ borderColor: "var(--border)" }}
              />
              <input
                value={form.phone}
                onChange={(event) => setForm((current) => ({ ...current, phone: event.target.value }))}
                placeholder="전화번호 *"
                inputMode="tel"
                aria-label="추가할 전화번호"
                className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-[#036EB8]"
                style={{ borderColor: "var(--border)" }}
              />
              <input
                value={form.label}
                onChange={(event) => setForm((current) => ({ ...current, label: event.target.value }))}
                placeholder="담당 업무"
                aria-label="담당 업무"
                className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-[#036EB8]"
                style={{ borderColor: "var(--border)" }}
              />
              <input
                value={form.note}
                onChange={(event) => setForm((current) => ({ ...current, note: event.target.value }))}
                placeholder="메모"
                aria-label="연락처 메모"
                className="rounded-lg border px-3 py-2.5 text-sm outline-none focus:border-[#036EB8]"
                style={{ borderColor: "var(--border)" }}
              />
            </div>
            {formError && <p className="mt-2 text-xs" style={{ color: "var(--brand-red-dark)" }}>{formError}</p>}
            <div className="mt-3 flex items-center justify-between gap-2">
              <div>
                {editingContactId && (
                  <button
                    type="button"
                    onClick={handleDeleteContact}
                    className="inline-flex items-center gap-1.5 rounded-lg px-3 py-2 text-xs font-bold transition-colors hover:bg-[#FFF4F3]"
                    style={{ color: "var(--brand-red-dark)" }}
                  >
                    <Trash2 className="h-4 w-4" />
                    삭제
                  </button>
                )}
              </div>
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  onClick={resetForm}
                  className="rounded-lg px-3 py-2 text-xs font-bold"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  취소
                </button>
                <button
                  type="submit"
                  className="rounded-lg px-4 py-2 text-xs font-bold text-white"
                  style={{ background: "var(--brand-green)" }}
                >
                  {editingContactId ? "수정 저장" : "연락처 저장"}
                </button>
              </div>
            </div>
          </form>
        )}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-5">
        {!directory && !loadError && (
          <div className="flex min-h-52 items-center justify-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
            <Loader2 className="h-4.5 w-4.5 animate-spin" style={{ color: "var(--brand-green)" }} />
            전화번호를 불러오고 있습니다.
          </div>
        )}

        {loadError && (
          <div role="alert" className="rounded-xl border px-4 py-4 text-sm" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
            {loadError}
          </div>
        )}

        {pinnedContacts.length > 0 && (
          <section className="mb-6">
            <h3 className="mb-2 flex items-center gap-1.5 text-xs font-extrabold" style={{ color: "var(--brand-red-dark)" }}>
              <Star className="h-3.5 w-3.5" fill="currentColor" />
              상단 고정
            </h3>
            <div className="divide-y overflow-hidden rounded-2xl border" style={{ borderColor: "var(--border)" }}>
              {pinnedContacts.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  isPinned
                  onTogglePin={togglePin}
                  onEdit={startEditContact}
                />
              ))}
            </div>
          </section>
        )}

        {groupedContacts.map(({ group, contacts }) => (
          <section key={group} className="mb-6 last:mb-0">
            <h3 className="mb-2 text-xs font-extrabold" style={{ color: "var(--muted-foreground)" }}>
              {group} <span className="font-normal">{contacts.length}</span>
            </h3>
            <div className="divide-y overflow-hidden rounded-2xl border" style={{ borderColor: "var(--border)" }}>
              {contacts.map((contact) => (
                <ContactRow
                  key={contact.id}
                  contact={contact}
                  isPinned={false}
                  onTogglePin={togglePin}
                  onEdit={startEditContact}
                />
              ))}
            </div>
          </section>
        ))}

        {directory && filteredContacts.length === 0 && (
          <p className="py-16 text-center text-sm" style={{ color: "var(--muted-foreground)" }}>
            일치하는 연락처가 없습니다.
          </p>
        )}
      </div>

      <footer className="border-t px-5 py-3 text-sm leading-5" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
        {directory?.notice ?? "공개 업무용 연락처만 표시합니다."}
        {directory?.verifiedAt ? ` · 확인 ${directory.verifiedAt}` : ""}
        <span className="mt-1 block">추가·수정·삭제한 내용은 현재 브라우저에 저장됩니다.</span>
      </footer>
    </aside>
  );
}
