import { ChevronLeft, ChevronRight, Loader2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy, RenderTask } from "pdfjs-dist";
import { getManualPdfUrl } from "../api/search";

let manualDocumentPromise: Promise<PDFDocumentProxy> | null = null;

async function loadManualDocument() {
  if (!manualDocumentPromise) {
    manualDocumentPromise = (async () => {
      const response = await fetch(getManualPdfUrl(), { credentials: "include" });
        if (!response.ok) {
          throw new Error(response.status === 401
            ? "로그인 정보가 만료되었습니다. 다시 로그인해 주세요."
            : "공식 매뉴얼 PDF를 불러오지 못했습니다.");
        }
      const data = await response.arrayBuffer();
      const pdfjs = await import("pdfjs-dist");
      pdfjs.GlobalWorkerOptions.workerSrc = new URL(
        "pdfjs-dist/build/pdf.worker.min.mjs",
        import.meta.url,
      ).toString();
      return pdfjs.getDocument({ data }).promise;
    })().catch((error) => {
        manualDocumentPromise = null;
        throw error;
      });
  }
  return manualDocumentPromise;
}

function PdfCanvas({ pageNumber }: { pageNumber: number }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    let renderTask: RenderTask | null = null;
    const canvas = canvasRef.current;
    if (!canvas) return;

    const render = async () => {
      try {
        setIsLoading(true);
        setError("");
        const document = await loadManualDocument();
        const page = await document.getPage(Math.min(Math.max(pageNumber, 1), document.numPages));
        if (cancelled) return;

        const viewport = page.getViewport({ scale: 1.6 });
        const pixelRatio = Math.min(window.devicePixelRatio || 1, 2);
        const context = canvas.getContext("2d", { alpha: false });
        if (!context) throw new Error("PDF 표시 화면을 준비하지 못했습니다.");

        canvas.width = Math.floor(viewport.width * pixelRatio);
        canvas.height = Math.floor(viewport.height * pixelRatio);

        renderTask = page.render({
          canvas,
          canvasContext: context,
          viewport,
          transform: pixelRatio === 1 ? undefined : [pixelRatio, 0, 0, pixelRatio, 0, 0],
        });
        await renderTask.promise;
        if (!cancelled) setIsLoading(false);
      } catch (renderError) {
        if (cancelled || (renderError instanceof Error && renderError.name === "RenderingCancelledException")) return;
        setError(renderError instanceof Error ? renderError.message : "PDF 페이지를 표시하지 못했습니다.");
        setIsLoading(false);
      }
    };

    void render();

    return () => {
      cancelled = true;
      renderTask?.cancel();
    };
  }, [pageNumber]);

  return (
    <div className="relative min-h-80 w-full overflow-hidden bg-[#E7E9EC]">
      {isLoading && (
        <div className="absolute inset-0 z-10 flex items-center justify-center gap-2 text-sm" style={{ color: "var(--muted-foreground)" }}>
          <Loader2 className="h-5 w-5 animate-spin" /> PDF {pageNumber}쪽을 불러오고 있습니다.
        </div>
      )}
      {error ? (
        <div role="alert" className="flex min-h-80 items-center justify-center px-6 text-center text-sm" style={{ color: "var(--brand-red-dark)" }}>
          {error}
        </div>
      ) : (
        <canvas ref={canvasRef} className="mx-auto block h-auto w-full bg-white shadow-sm" aria-label={`공식 매뉴얼 PDF ${pageNumber}쪽`} />
      )}
    </div>
  );
}

export function ManualPdfPages({ pages }: { pages: number[] }) {
  const uniquePages = [...new Set(pages)].filter((page) => page > 0);
  return (
    <div className="space-y-4">
      {uniquePages.map((page) => (
        <section key={page} className="overflow-hidden rounded-xl border bg-white" style={{ borderColor: "var(--border)" }}>
          <div className="border-b px-3 py-2 text-xs font-bold" style={{ borderColor: "var(--border)", color: "var(--muted-foreground)" }}>
            PDF {page}쪽
          </div>
          <PdfCanvas pageNumber={page} />
        </section>
      ))}
    </div>
  );
}

export function ManualPdfPager({ initialPage, totalPages = 85 }: { initialPage: number; totalPages?: number }) {
  const [page, setPage] = useState(initialPage);

  useEffect(() => setPage(initialPage), [initialPage]);

  return (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className="flex items-center justify-center gap-3 border-b bg-white px-4 py-2" style={{ borderColor: "var(--border)" }}>
        <button type="button" onClick={() => setPage((current) => Math.max(1, current - 1))} disabled={page <= 1} aria-label="이전 PDF 페이지" className="rounded-lg border p-2 disabled:opacity-30" style={{ borderColor: "var(--border)" }}>
          <ChevronLeft className="h-4 w-4" />
        </button>
        <strong className="min-w-24 text-center text-sm">{page} / {totalPages}쪽</strong>
        <button type="button" onClick={() => setPage((current) => Math.min(totalPages, current + 1))} disabled={page >= totalPages} aria-label="다음 PDF 페이지" className="rounded-lg border p-2 disabled:opacity-30" style={{ borderColor: "var(--border)" }}>
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>
      <div className="min-h-0 flex-1 overflow-y-auto bg-[#E7E9EC] p-3 sm:p-5">
        <PdfCanvas pageNumber={page} />
      </div>
    </div>
  );
}
