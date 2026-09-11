import {
  AlertTriangle,
  BookOpen,
  CheckCircle2,
  Clock3,
  LockKeyhole,
  PhoneCall,
} from "lucide-react";
import type { QuickGuide } from "../api/search";

interface QuickGuideViewProps {
  guide: QuickGuide;
  source: string;
  compact?: boolean;
}

function formatPageLabel(pages: number[]) {
  if (pages.length === 0) return "쪽수 확인 필요";

  const sortedPages = [...new Set(pages)].sort((a, b) => a - b);
  const ranges: string[] = [];
  let rangeStart = sortedPages[0];
  let previousPage = sortedPages[0];

  for (const page of sortedPages.slice(1)) {
    if (page === previousPage + 1) {
      previousPage = page;
      continue;
    }

    ranges.push(rangeStart === previousPage ? `${rangeStart}` : `${rangeStart}-${previousPage}`);
    rangeStart = page;
    previousPage = page;
  }

  ranges.push(rangeStart === previousPage ? `${rangeStart}` : `${rangeStart}-${previousPage}`);
  return `${ranges.join(", ")}쪽`;
}

export function QuickGuideView({ guide, source, compact = false }: QuickGuideViewProps) {
  const pageLabel = formatPageLabel(guide.sourcePages);
  const contactGroups = [...new Set((guide.contacts ?? []).map((contact) => contact.group))];

  if (compact) {
    return (
      <article>
        <p className="text-sm leading-6" style={{ color: "#4B5563" }}>
          {guide.description}
        </p>

        <div className="mt-5 space-y-4">
          {guide.sections.map((section, sectionIndex) => (
            <section
              key={`${section.title}-${section.timeLabel}`}
              className="rounded-2xl border bg-white p-4"
              style={{ borderColor: "var(--border)" }}
            >
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
                    style={{ background: "var(--brand-green)" }}
                  >
                    {sectionIndex + 1}
                  </span>
                  <h2 className="font-bold">{section.title}</h2>
                </div>
                <span
                  className="inline-flex items-center gap-1.5 rounded-full border px-3 py-1.5 text-[11px] font-bold"
                  style={{ background: "#FFFFFF", borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
                >
                  <Clock3 className="h-3.5 w-3.5" />
                  {section.timeLabel}
                </span>
              </div>

              <ul className="mt-4 space-y-2.5 text-[13px] leading-6">
                {section.steps.map((step) => (
                  <li key={step} className="flex gap-2.5">
                    <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                    <span>{step}</span>
                  </li>
                ))}
              </ul>
            </section>
          ))}
        </div>

        {contactGroups.length > 0 && (
          <section className="mt-5 border-t pt-5" style={{ borderColor: "var(--border)" }}>
            <h2 className="flex items-center gap-2 text-sm font-bold">
              <PhoneCall className="h-4 w-4" style={{ color: "var(--brand-green)" }} />
              공개 연락처
            </h2>
            <div className="mt-3 space-y-5">
              {contactGroups.map((group) => (
                <div key={group}>
                  <p className="mb-2 text-[11px] font-bold" style={{ color: "var(--muted-foreground)" }}>
                    {group}
                  </p>
                  <div className="divide-y rounded-2xl border bg-white px-4" style={{ borderColor: "var(--border)" }}>
                    {(guide.contacts ?? [])
                      .filter((contact) => contact.group === group)
                      .map((contact) => (
                        <a
                          key={`${contact.organization}-${contact.label}-${contact.phone}`}
                          href={`tel:${contact.phone}`}
                          className="flex items-center justify-between gap-3 py-3.5"
                          style={{ borderColor: "var(--border)" }}
                        >
                          <span className="min-w-0">
                            <strong className="block text-[13px]">{contact.organization}</strong>
                            <span className="mt-0.5 block text-[11px]" style={{ color: "var(--muted-foreground)" }}>
                              {contact.label}
                            </span>
                          </span>
                          <span className="flex-shrink-0 text-[13px] font-bold" style={{ color: "var(--brand-green)" }}>
                            {contact.phone}
                          </span>
                        </a>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {guide.restrictedNotice && (
          <section className="mt-4 rounded-2xl border border-dashed bg-white p-4" style={{ borderColor: "var(--sidebar-border)" }}>
            <div className="flex gap-3">
              <LockKeyhole className="mt-0.5 h-4.5 w-4.5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
              <div>
                <h2 className="text-sm font-bold">비공개 연락망</h2>
                <p className="mt-1.5 text-xs leading-5" style={{ color: "var(--muted-foreground)" }}>
                  {guide.restrictedNotice}
                </p>
              </div>
            </div>
          </section>
        )}

        {guide.cautions.length > 0 && (
          <section className="mt-4 rounded-2xl border p-4" style={{ background: "var(--brand-red-light)", borderColor: "var(--brand-red)" }}>
            <div className="flex gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-red)" }} />
              <div>
                <h2 className="sr-only">주의사항</h2>
                <ul className="space-y-1.5 text-xs leading-5" style={{ color: "var(--brand-red-dark)" }}>
                  {guide.cautions.map((caution) => <li key={caution}>• {caution}</li>)}
                </ul>
              </div>
            </div>
          </section>
        )}

        <footer
          className="mt-5 flex items-start gap-2 text-[11px] leading-5"
          style={{ color: "var(--muted-foreground)" }}
        >
          <BookOpen className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          {source} · {pageLabel}
        </footer>
      </article>
    );
  }

  return (
    <article
      className="overflow-hidden rounded-2xl border bg-white"
      style={{ borderColor: "var(--border)" }}
    >
      <header className="border-b px-6 py-6 sm:px-8" style={{ borderColor: "var(--border)" }}>
        <span
          className="inline-flex rounded-full border px-3 py-1 text-xs font-bold"
          style={{ background: "#FFFFFF", borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
        >
          공식 매뉴얼
        </span>
        <h1 className="mt-3 text-2xl font-extrabold">{guide.title}</h1>
        <p className="mt-3 text-sm leading-7" style={{ color: "#4B5563" }}>
          {guide.description}
        </p>
      </header>

      <div className="px-6 py-7 sm:px-8">
        <div className="space-y-5">
          {guide.sections.map((section, sectionIndex) => (
            <section key={`${section.title}-${section.timeLabel}`} className="grid gap-4 sm:grid-cols-[150px_1fr]">
              <div>
                <div
                  className="inline-flex items-center gap-2 rounded-lg border px-3 py-2 text-xs font-bold"
                  style={{ background: "#FFFFFF", borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
                >
                  <Clock3 className="h-3.5 w-3.5" />
                  {section.timeLabel}
                </div>
              </div>

              <div className="rounded-xl border p-5" style={{ borderColor: "var(--border)" }}>
                <div className="mb-4 flex items-center gap-3">
                  <span
                    className="flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white"
                    style={{ background: "var(--brand-green)" }}
                  >
                    {sectionIndex + 1}
                  </span>
                  <h2 className="font-bold">{section.title}</h2>
                </div>
                <ul className="space-y-3 text-sm leading-6">
                  {section.steps.map((step) => (
                    <li key={step} className="flex gap-3">
                      <CheckCircle2 className="mt-1 h-4 w-4 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
                      <span>{step}</span>
                    </li>
                  ))}
                </ul>
              </div>
            </section>
          ))}
        </div>

        {contactGroups.length > 0 && (
          <section className="mt-7 border-t pt-6" style={{ borderColor: "var(--border)" }}>
            <h2 className="flex items-center gap-2 font-bold">
              <PhoneCall className="h-5 w-5" style={{ color: "var(--brand-green)" }} />
              공개 연락처
            </h2>
            <div className="mt-4 space-y-6">
              {contactGroups.map((group) => (
                <div key={group}>
                  <p className="mb-2 text-xs font-bold" style={{ color: "var(--muted-foreground)" }}>
                    {group}
                  </p>
                  <div className="grid gap-px overflow-hidden rounded-xl border sm:grid-cols-2" style={{ background: "var(--border)", borderColor: "var(--border)" }}>
                    {(guide.contacts ?? [])
                      .filter((contact) => contact.group === group)
                      .map((contact) => (
                        <a
                          key={`${contact.organization}-${contact.label}-${contact.phone}`}
                          href={`tel:${contact.phone}`}
                          className="flex items-center justify-between gap-3 bg-white px-4 py-4"
                        >
                          <span className="min-w-0">
                            <strong className="block text-sm">{contact.organization}</strong>
                            <span className="mt-1 block text-xs" style={{ color: "var(--muted-foreground)" }}>
                              {contact.label}
                            </span>
                          </span>
                          <span className="flex-shrink-0 text-sm font-bold" style={{ color: "var(--brand-green)" }}>
                            {contact.phone}
                          </span>
                        </a>
                      ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        )}

        {guide.restrictedNotice && (
          <section className="mt-5 rounded-xl border border-dashed bg-white p-5" style={{ borderColor: "var(--sidebar-border)" }}>
            <div className="flex gap-3">
              <LockKeyhole className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--muted-foreground)" }} />
              <div>
                <h2 className="font-bold">비공개 연락망</h2>
                <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
                  {guide.restrictedNotice}
                </p>
              </div>
            </div>
          </section>
        )}

        {guide.cautions.length > 0 && (
          <section className="mt-6 rounded-xl border p-5" style={{ background: "var(--brand-red-light)", borderColor: "var(--brand-red)" }}>
            <div className="flex gap-3">
              <AlertTriangle className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-red)" }} />
              <div>
                <h2 className="sr-only">주의사항</h2>
                <ul className="space-y-2 text-sm leading-6" style={{ color: "var(--brand-red-dark)" }}>
                  {guide.cautions.map((caution) => <li key={caution}>• {caution}</li>)}
                </ul>
              </div>
            </div>
          </section>
        )}
      </div>

      <footer
        className="flex items-center gap-2 border-t px-6 py-4 text-xs sm:px-8"
        style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
      >
        <BookOpen className="h-4 w-4" />
        {source} · {pageLabel}
      </footer>
    </article>
  );
}
