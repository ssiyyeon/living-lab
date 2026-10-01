import { useState } from "react";
import { Loader2, LockKeyhole } from "lucide-react";
import yusungLogo from "@/imports/image.png";
import { login, setupAdmin, type AuthUser } from "../api/search";

interface LoginPageProps {
  needsSetup: boolean;
  onAuthenticated: (user: AuthUser) => void;
}

export function LoginPage({ needsSetup, onAuthenticated }: LoginPageProps) {
  const [displayName, setDisplayName] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError("");

    if (username.trim().length < 3 || password.length < 8) {
      setError("아이디는 3자 이상, 비밀번호는 8자 이상 입력해 주세요.");
      return;
    }
    if (needsSetup && !displayName.trim()) {
      setError("관리자 이름을 입력해 주세요.");
      return;
    }

    setIsSubmitting(true);
    try {
      const user = needsSetup
        ? await setupAdmin(displayName.trim(), username.trim(), password)
        : await login(username.trim(), password);
      onAuthenticated(user);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "로그인하지 못했습니다.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center bg-[#F3F5F7] px-5 py-10">
      <section className="w-full max-w-[420px] rounded-[28px] border bg-white px-8 py-9" style={{ borderColor: "var(--border)" }}>
        <img src={yusungLogo} alt="유성구" className="mx-auto h-14 w-auto object-contain" />
        <div className="mt-7 text-center">
          <h1 className="text-2xl font-extrabold">
            {needsSetup ? "관리자 계정 만들기" : "당직 근무 지원 로그인"}
          </h1>
          <p className="mt-2 text-sm leading-6" style={{ color: "var(--muted-foreground)" }}>
            {needsSetup
              ? "처음 한 번만 사용할 관리자 계정을 설정합니다."
              : "등록된 계정으로 로그인해 주세요."}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-4">
          {needsSetup && (
            <label className="block">
              <span className="mb-2 block text-sm font-bold">관리자 이름</span>
              <input
                value={displayName}
                onChange={(event) => setDisplayName(event.target.value)}
                autoComplete="name"
                className="w-full rounded-xl border px-4 py-3 text-base outline-none focus:border-[#036EB8]"
                style={{ borderColor: "var(--border)" }}
                placeholder="예: 김민준"
              />
            </label>
          )}
          <label className="block">
            <span className="mb-2 block text-sm font-bold">아이디</span>
            <input
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              autoComplete="username"
              className="w-full rounded-xl border px-4 py-3 text-base outline-none focus:border-[#036EB8]"
              style={{ borderColor: "var(--border)" }}
              placeholder="3자 이상"
            />
          </label>
          <label className="block">
            <span className="mb-2 block text-sm font-bold">비밀번호</span>
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete={needsSetup ? "new-password" : "current-password"}
              className="w-full rounded-xl border px-4 py-3 text-base outline-none focus:border-[#036EB8]"
              style={{ borderColor: "var(--border)" }}
              placeholder="8자 이상"
            />
          </label>

          {error && (
            <p role="alert" className="rounded-xl border px-4 py-3 text-sm" style={{ borderColor: "var(--brand-red)", color: "var(--brand-red-dark)" }}>
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting}
            className="flex w-full items-center justify-center gap-2 rounded-xl py-3.5 text-base font-extrabold text-white disabled:opacity-60"
            style={{ background: "var(--brand-green)" }}
          >
            {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin" /> : <LockKeyhole className="h-5 w-5" />}
            {needsSetup ? "관리자 계정 생성" : "로그인"}
          </button>
        </form>
      </section>
    </main>
  );
}
