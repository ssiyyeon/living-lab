export interface DepartmentRouting {
  department: string;
  condition: string;
  confidence: string;
}

export interface DepartmentContact {
  department: string;
  label: string;
  phone: string;
  note: string;
  sourceUrl: string;
}

export interface DecisionBranch {
  condition: string;
  actions: string[];
  response: string;
}

export interface EscalationRule {
  condition: string;
  action: string;
}

export interface SearchResult {
  id: string;
  kind: string;
  category: string;
  documentName: string;
  civilType: string;
  department: string;
  departments: string[];
  departmentContacts: DepartmentContact[];
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
  caseKind: string | null;
  intakeQuestions: string[];
  immediateActions: string[];
  decisionBranches: DecisionBranch[];
  responseScripts: string[];
  escalationRules: EscalationRule[];
  cautions: string[];
}

export interface SearchResponse {
  query: string;
  tier: string;
  message: string;
  resultCount: number;
  recommendedDepartments: string[];
  relevanceNotice: string;
  results: SearchResult[];
}

export interface QuickGuideSection {
  title: string;
  timeLabel: string;
  steps: string[];
}

export interface QuickGuideContact {
  group: string;
  organization: string;
  label: string;
  phone: string;
}

export interface QuickGuide {
  id: string;
  title: string;
  description: string;
  sourcePages: number[];
  sections: QuickGuideSection[];
  cautions: string[];
  contacts: QuickGuideContact[];
  restrictedNotice: string | null;
}

export interface QuickGuideListResponse {
  source: string;
  guides: QuickGuide[];
}

export interface ContactDirectoryEntry {
  id: string;
  group: string;
  organization: string;
  label: string;
  phone: string;
  note: string;
  source: string;
  sourceUrl: string;
}

export interface ContactDirectoryResponse {
  source: string;
  verifiedAt: string;
  notice: string;
  contacts: ContactDirectoryEntry[];
}

export interface ManualCatalogEntry {
  id: string;
  entryType: "section" | "case";
  group: string;
  topic: string;
  title: string;
  breadcrumb: string[];
  sourcePages: number[];
  departments: string[];
  summary: string;
  content: string;
  intakeQuestions: string[];
  immediateActions: string[];
  decisionBranches: DecisionBranch[];
  responseScripts: string[];
  escalationRules: EscalationRule[];
  cautions: string[];
}

export interface ManualCatalogResponse {
  source: string;
  totalCount: number;
  entries: ManualCatalogEntry[];
}

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export async function searchComplaints(
  query: string,
  topK = 3,
): Promise<SearchResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/search`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        query,
        top_k: topK,
      }),
    });
  } catch {
    throw new Error(
      "검색 서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.",
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    const message =
      body && typeof body.detail === "string"
        ? body.detail
        : "검색 요청에 실패했습니다.";

    throw new Error(message);
  }

  return body as SearchResponse;
}

export async function fetchQuickGuides(): Promise<QuickGuideListResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/guides`);
  } catch {
    throw new Error(
      "업무 가이드를 불러올 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.",
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error("업무 가이드를 불러오지 못했습니다.");
  }

  return body as QuickGuideListResponse;
}

export async function fetchContactDirectory(): Promise<ContactDirectoryResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/contacts`);
  } catch {
    throw new Error(
      "전화번호부를 불러올 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.",
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error("전화번호부를 불러오지 못했습니다.");
  }

  return body as ContactDirectoryResponse;
}

export async function fetchManualCatalog(): Promise<ManualCatalogResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/manual`);
  } catch {
    throw new Error(
      "전체 매뉴얼을 불러올 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.",
    );
  }

  const body = await response.json().catch(() => null);

  if (!response.ok) {
    throw new Error("전체 매뉴얼을 불러오지 못했습니다.");
  }

  return body as ManualCatalogResponse;
}
