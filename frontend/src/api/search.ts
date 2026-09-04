export interface DepartmentRouting {
  department: string;
  condition: string;
  confidence: string;
}

export interface ApiSearchResult {
  id: string;
  kind: string;
  category: string;
  documentName: string;
  civilType: string;
  department: string;
  departments: string[];
  paragraphSummary: string;
  guidance: string;
  note: string;
  updatedAt: string;
  relevance: number;
  tags: string[];
  evidenceLevel: string;
  sourceReference: string;
  sourcePages: number[];
  matchedPage: number | null;
  originalUrl: string | null;
  candidateCount: number | null;
  departmentRouting: DepartmentRouting[];
}

export interface ApiSearchResponse {
  query: string;
  tier: string;
  message: string;
  resultCount: number;
  recommendedDepartments: string[];
  relevanceNotice: string;
  results: ApiSearchResult[];
}

interface ApiErrorBody {
  detail?: string;
}

export class SearchApiError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SearchApiError";
  }
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

export async function searchManual(query: string): Promise<ApiSearchResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/search`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        top_k: 4,
      }),
    });
  } catch {
    throw new SearchApiError(
      "검색 API 서버에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인해 주세요.",
    );
  }

  const body = (await response.json().catch(() => ({}))) as Partial<ApiSearchResponse> & ApiErrorBody;
  if (!response.ok) {
    throw new SearchApiError(body.detail ?? "검색 요청에 실패했습니다.");
  }
  return body as ApiSearchResponse;
}
