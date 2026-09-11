import { AlertTriangle, BookOpen, CheckCircle2, Clock3 } from "lucide-react";
import { useState } from "react";
import type { QuickGuide } from "../api/search";

interface DutyTimelineDrawerProps {
  guide: QuickGuide;
  source: string;
}

function formatPageLabel(pages: number[]) {
  if (pages.length === 0) return "쪽수 확인 필요";

  const sortedPages = [...new Set(pages)].sort((a, b) => a - b);
  return `${sortedPages.join(", ")}쪽`;
}

export function DutyTimelineDrawer({ guide, source }: DutyTimelineDrawerProps) {
  const [selectedIndex, setSelectedIndex] = useState(0);
  const selectedSection = guide.sections[selectedIndex];

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex-1 overflow-y-auto px-4 pb-5 sm:px-5">
        <fieldset>
          <legend className="sr-only">확인할 근무 시간대 선택</legend>
          <div className="space-y-2.5">
            {guide.sections.map((section, index) => {
              const isSelected = selectedIndex === index;

              return (
                <label
                  key={`${section.title}-${section.timeLabel}`}
                  className="block cursor-pointer rounded-2xl border bg-white px-4 py-4 transition-colors"
                  style={{
                    borderColor: isSelected ? "var(--brand-green)" : "var(--border)",
                    background: isSelected ? "#F7FCFF" : "#FFFFFF",
                  }}
                >
                  <input
                    type="radio"
                    name="duty-timeline-section"
                    value={index}
                    checked={isSelected}
                    onChange={() => setSelectedIndex(index)}
                    className="sr-only"
                  />
                  <span className="flex items-start gap-3">
                    <span className="min-w-0 flex-1">
                      <strong className="block text-[15px] leading-6">
                        {section.timeLabel}
                      </strong>
                      <span
                        className="mt-1 block text-xs leading-5"
                        style={{ color: "var(--muted-foreground)" }}
                      >
                        {section.title}
                      </span>
                    </span>
                    <span
                      aria-hidden="true"
                      className="mt-1 flex h-5 w-5 flex-shrink-0 items-center justify-center rounded-full border"
                      style={{
                        borderColor: isSelected ? "var(--brand-green)" : "var(--border)",
                      }}
                    >
                      {isSelected && (
                        <span
                          className="h-2.5 w-2.5 rounded-full"
                          style={{ background: "var(--brand-green)" }}
                        />
                      )}
                    </span>
                  </span>
                </label>
              );
            })}
          </div>
        </fieldset>

        {selectedSection && (
          <section
            className="mt-5 border-t pt-5"
            style={{ borderColor: "var(--border)" }}
            aria-live="polite"
          >
            <div className="flex items-start gap-3">
              <Clock3
                className="mt-0.5 h-5 w-5 flex-shrink-0"
                style={{ color: "var(--brand-green)" }}
              />
              <div>
                <h3 className="font-extrabold">{selectedSection.title}</h3>
                <p
                  className="mt-0.5 text-xs"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  {selectedSection.timeLabel}
                </p>
              </div>
            </div>

            <ol className="mt-4 space-y-3">
              {selectedSection.steps.map((step, index) => (
                <li key={step} className="flex gap-3 text-[13px] leading-6">
                  <CheckCircle2
                    className="mt-1 h-4 w-4 flex-shrink-0"
                    style={{ color: "var(--brand-green)" }}
                  />
                  <span>
                    <span className="sr-only">{index + 1}번째 할 일: </span>
                    {step}
                  </span>
                </li>
              ))}
            </ol>
          </section>
        )}

        {guide.cautions.length > 0 && (
          <section
            className="mt-5 border-t pt-5"
            style={{ borderColor: "var(--border)" }}
          >
            <div className="flex gap-3">
              <AlertTriangle
                className="mt-0.5 h-4.5 w-4.5 flex-shrink-0"
                style={{ color: "var(--brand-red)" }}
              />
              <div>
                <h3 className="sr-only">주의사항</h3>
                <ul
                  className="space-y-1.5 text-xs leading-5"
                  style={{ color: "var(--muted-foreground)" }}
                >
                  {guide.cautions.map((caution) => (
                    <li key={caution}>• {caution}</li>
                  ))}
                </ul>
              </div>
            </div>
          </section>
        )}

        <footer
          className="mt-5 flex items-start gap-2 border-t pt-4 text-[11px] leading-5"
          style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}
        >
          <BookOpen className="mt-0.5 h-3.5 w-3.5 flex-shrink-0" />
          {source} · {formatPageLabel(guide.sourcePages)}
        </footer>
      </div>
    </div>
  );
}
