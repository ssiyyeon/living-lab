export interface ApiSearchResult {
  tier: string;
  "부서": string | null;
  "민원유형": string;
  "관련문단": string;
  "참고사항": string;
  "담당자": string | null;
  "문서명": string;
  "페이지": string | number | null;
  "유사도": number | null;
}

export interface ApiSearchResponse {
  "근거수준": string;
  "안내": string | null;
  "결과": ApiSearchResult[];
}

interface ApiErrorBody {
  error?: {
    code?: string;
    message?: string;
    missingFiles?: string[];
    missingModules?: string[];
  };
}

export class SearchApiError extends Error {
  code?: string;
  missingFiles: string[];
  missingModules: string[];

  constructor(message: string, body?: ApiErrorBody) {
    super(message);
    this.name = "SearchApiError";
    this.code = body?.error?.code;
    this.missingFiles = body?.error?.missingFiles ?? [];
    this.missingModules = body?.error?.missingModules ?? [];
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export async function searchManual(query: string): Promise<ApiSearchResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, topK: 4 }),
    });
  } catch {
    throw new SearchApiError(
      "검색 API 서버에 연결할 수 없습니다. 프로젝트 루트에서 Python API 서버를 실행해 주세요.",
    );
  }

  const body = (await response.json().catch(() => ({}))) as ApiSearchResponse & ApiErrorBody;
  if (!response.ok) {
    throw new SearchApiError(body.error?.message ?? "검색 요청에 실패했습니다.", body);
  }
  return body;
}
