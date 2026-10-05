import {
  Baby,
  Car,
  Construction,
  FileText,
  HeartHandshake,
  Leaf,
  PawPrint,
  Siren,
  Trash2,
  Trees,
} from "lucide-react";

const SITUATION_GROUPS = [
  { title: "교통", icon: Car, items: ["불법주정차", "마을버스"] },
  { title: "동물", icon: PawPrint, items: ["유기동물", "부상동물", "동물사체"] },
  { title: "환경", icon: Leaf, items: ["소음", "악취", "수질오염"] },
  { title: "청소", icon: Trash2, items: ["쓰레기", "불법투기"] },
  { title: "도로", icon: Construction, items: ["포트홀", "싱크홀", "도로 낙하물"] },
  { title: "복지", icon: HeartHandshake, items: ["노숙인", "이재민"] },
  { title: "아동", icon: Baby, items: ["아동학대"] },
  { title: "민원", icon: FileText, items: ["무인민원발급기"] },
  { title: "산림", icon: Trees, items: ["가로수 전도"] },
  { title: "긴급", icon: Siren, items: ["화재", "침수", "산불", "건축물 붕괴"], urgent: true },
];

export function SituationPage({ onSelect, focusEmergency = false }: { onSelect: (query: string) => void; focusEmergency?: boolean }) {
  const groups = focusEmergency
    ? [...SITUATION_GROUPS].sort((a, b) => Number(Boolean(b.urgent)) - Number(Boolean(a.urgent)))
    : SITUATION_GROUPS;

  return (
    <section>
      <header className="border-b pb-6" style={{ borderColor: "var(--border)" }}>
        <p className="text-sm font-bold" style={{ color: "var(--brand-green)" }}>검색 없이 바로 선택</p>
        <h1 className="mt-2 text-3xl font-extrabold">상황별 대응</h1>
        <p className="mt-2 text-base leading-7" style={{ color: "var(--muted-foreground)" }}>민원 유형을 누르면 검색 API에서 공식 매뉴얼과 관련 사례를 바로 확인합니다.</p>
      </header>

      <div className="mt-7 grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {groups.map(({ title, icon: Icon, items, urgent }) => (
          <section key={title} className="border-t-2 bg-white px-1 py-4" style={{ borderColor: urgent ? "var(--brand-red)" : "var(--brand-green)" }}>
            <div className="flex items-center gap-2 px-2">
              <Icon className="h-5 w-5" style={{ color: urgent ? "var(--brand-red)" : "var(--brand-green)" }} />
              <h2 className="text-lg font-extrabold" style={{ color: urgent ? "var(--brand-red-dark)" : undefined }}>{title}</h2>
              {urgent && <span className="ml-auto rounded-full bg-[#FFF0EE] px-2.5 py-1 text-xs font-extrabold" style={{ color: "var(--brand-red-dark)" }}>긴급</span>}
            </div>
            <div className="mt-3 divide-y" style={{ borderColor: "var(--border)" }}>
              {items.map((item) => (
                <button key={item} type="button" onClick={() => onSelect(`${item} 신고가 들어왔어요`)} className="flex w-full items-center justify-between px-2 py-3 text-left text-sm font-bold transition-colors hover:bg-[#F7FAFC] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8]" style={{ borderColor: "var(--border)" }}>
                  {item}<span aria-hidden="true" style={{ color: urgent ? "var(--brand-red)" : "var(--brand-green)" }}>→</span>
                </button>
              ))}
            </div>
          </section>
        ))}
      </div>
    </section>
  );
}
