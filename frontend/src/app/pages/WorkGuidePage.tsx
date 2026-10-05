import { ClipboardList, ClipboardPlus, Clock3, Loader2, NotebookPen, Pencil } from "lucide-react";
import { useEffect, useState } from "react";
import type { QuickGuide } from "../api/search";
import { DutyTimelineDrawer } from "../components/DutyTimelineDrawer";
import { QuickGuideView } from "../components/QuickGuideView";

const WORK_ITEMS = [
  { id: "duty_timeline", label: "근무 타임라인", description: "시간대별 해야 할 일", icon: Clock3 },
  { id: "duty_log", label: "당직근무일지", description: "작성 순서와 마감 확인", icon: NotebookPen },
  { id: "complaint_registration", label: "당직민원 등록", description: "접수·이첩 기록 기준", icon: ClipboardPlus },
  { id: "duty_basics", label: "당직 기본업무", description: "시건·순찰·인계 확인", icon: ClipboardList },
];

export function WorkGuidePage({
  guides,
  source,
  error,
  onOpenManual,
  requestedGuideId,
  canEdit = false,
  onEditGuide,
}: {
  guides: QuickGuide[];
  source: string;
  error: string;
  onOpenManual: () => void;
  requestedGuideId?: string;
  canEdit?: boolean;
  onEditGuide?: (guideId: string) => void;
}) {
  const firstAvailableId = WORK_ITEMS.find((item) => guides.some((guide) => guide.id === item.id))?.id;
  const [selectedId, setSelectedId] = useState(requestedGuideId ?? firstAvailableId ?? WORK_ITEMS[0].id);

  useEffect(() => {
    if (requestedGuideId && guides.some((guide) => guide.id === requestedGuideId)) {
      setSelectedId(requestedGuideId);
    }
  }, [guides, requestedGuideId]);

  useEffect(() => {
    if (!guides.some((guide) => guide.id === selectedId) && firstAvailableId) setSelectedId(firstAvailableId);
  }, [firstAvailableId, guides, selectedId]);

  const selectedGuide = guides.find((guide) => guide.id === selectedId);

  return (
    <section>
      <header className="flex items-start justify-between gap-4 border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <div>
          <p className="text-sm font-bold" style={{ color: "var(--brand-green)" }}>당직 업무 한곳에서 확인</p>
          <h1 className="mt-2 text-3xl font-extrabold">근무 안내</h1>
          <p className="mt-2 text-base leading-7" style={{ color: "var(--muted-foreground)" }}>타임라인부터 근무일지와 민원 등록까지 필요한 안내를 선택하세요.</p>
        </div>
        {canEdit && selectedGuide && onEditGuide && (
          <button
            type="button"
            onClick={() => onEditGuide(selectedGuide.id)}
            aria-label={`${selectedGuide.title} 수정`}
            title={`${selectedGuide.title} 수정`}
            className="inline-flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full border bg-white"
            style={{ borderColor: "var(--brand-green)", color: "var(--brand-green-dark)" }}
          >
            <Pencil className="h-4 w-4" />
          </button>
        )}
      </header>

      <div className="mt-6 grid gap-2 sm:grid-cols-2 xl:grid-cols-4" role="tablist" aria-label="근무 안내 종류">
        {WORK_ITEMS.map(({ id, label, description, icon: Icon }) => {
          const isActive = selectedId === id;
          const isAvailable = guides.some((guide) => guide.id === id);
          return (
            <button key={id} type="button" role="tab" aria-selected={isActive} onClick={() => setSelectedId(id)} className="flex items-start gap-3 border-t-2 bg-white px-3 py-4 text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]" style={{ borderColor: isActive ? "var(--brand-green)" : "var(--border)", opacity: isAvailable ? 1 : 0.65 }}>
              <Icon className="mt-0.5 h-5 w-5 flex-shrink-0" style={{ color: "var(--brand-green)" }} />
              <span><strong className="block text-sm">{label}</strong><span className="mt-1 block text-xs" style={{ color: "var(--muted-foreground)" }}>{description}</span></span>
            </button>
          );
        })}
      </div>

      <div className="mt-7" role="tabpanel">
        {selectedGuide ? (
          selectedGuide.id === "duty_timeline"
            ? <div className="overflow-hidden rounded-2xl border bg-white pt-4" style={{ borderColor: "var(--border)" }}><DutyTimelineDrawer guide={selectedGuide} source={source} /></div>
            : <QuickGuideView guide={selectedGuide} source={source} />
        ) : error ? (
          <div role="alert" className="border-l-4 px-4 py-5 text-sm" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>{error}</div>
        ) : guides.length === 0 ? (
          <div className="flex min-h-48 items-center justify-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}><Loader2 className="h-5 w-5 animate-spin" /> 근무 안내를 불러오고 있습니다.</div>
        ) : (
          <div className="border-y px-4 py-10 text-center" style={{ borderColor: "var(--border)" }}>
            <p className="font-bold">이 안내는 현재 빠른 업무 안내 API에 포함되지 않았습니다.</p>
            <p className="mt-2 text-sm" style={{ color: "var(--muted-foreground)" }}>전체 매뉴얼에서 원문을 확인할 수 있습니다.</p>
            <button type="button" onClick={onOpenManual} className="mt-4 rounded-xl px-4 py-2.5 text-sm font-bold text-white" style={{ background: "var(--brand-green)" }}>전체 매뉴얼 보기</button>
          </div>
        )}
      </div>
    </section>
  );
}
