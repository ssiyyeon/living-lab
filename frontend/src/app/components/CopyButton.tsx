import { Check, Copy } from "lucide-react";
import { useEffect, useState } from "react";

interface CopyButtonProps {
  value: string;
  label?: string;
  copiedLabel?: string;
  compact?: boolean;
}

async function copyText(value: string) {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(value);
    return;
  }

  const textarea = document.createElement("textarea");
  textarea.value = value;
  textarea.style.position = "fixed";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

export function CopyButton({
  value,
  label = "복사",
  copiedLabel = "복사됨",
  compact = false,
}: CopyButtonProps) {
  const [state, setState] = useState<"idle" | "copied" | "error">("idle");

  useEffect(() => {
    if (state === "idle") return;
    const timer = window.setTimeout(() => setState("idle"), 1800);
    return () => window.clearTimeout(timer);
  }, [state]);

  const handleCopy = async () => {
    try {
      await copyText(value);
      setState("copied");
    } catch {
      setState("error");
    }
  };

  const text = state === "copied" ? copiedLabel : state === "error" ? "복사 실패" : label;

  return (
    <button
      type="button"
      onClick={() => void handleCopy()}
      aria-label={`${label}: ${value}`}
      className={`inline-flex items-center justify-center gap-1.5 rounded-lg border bg-white font-bold transition-colors hover:bg-[#F3F8FC] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#036EB8] ${
        compact ? "px-2.5 py-1.5 text-xs" : "px-3 py-2 text-sm"
      }`}
      style={{
        borderColor: state === "copied" ? "#16865B" : "var(--border)",
        color: state === "copied" ? "#126B49" : "var(--muted-foreground)",
      }}
    >
      {state === "copied" ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
      <span aria-live="polite">{text}</span>
    </button>
  );
}
