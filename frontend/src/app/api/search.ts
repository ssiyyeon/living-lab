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
  addedAt?: string | null;
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
  updatedAt?: string | null;
  changedFields?: string[];
  changedSectionIndexes?: number[];
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
  isCustom?: boolean;
  isModified?: boolean;
  addedAt?: string | null;
  updatedAt?: string | null;
  changedFields?: string[];
}

export interface ManualCatalogResponse {
  source: string;
  totalCount: number;
  entries: ManualCatalogEntry[];
}

export interface AuthUser {
  id: number;
  username: string;
  displayName: string;
  role: "admin" | "staff";
}

export interface AuthStatusResponse {
  needsSetup: boolean;
}

export interface AdminContactInput {
  group: string;
  organization: string;
  label: string;
  phone: string;
  note: string;
  sourceUrl: string;
}

export interface AdminGuideInput {
  title: string;
  description: string;
  sections: QuickGuideSection[];
  cautions: string[];
}

export interface AdminManualInput {
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

export interface ManualAdminDeleteResponse {
  ok: boolean;
  action: "restored" | "deleted";
}

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"
).replace(/\/$/, "");

export function getManualPdfUrl(page?: number): string {
  const pageFragment = page && page > 0 ? `#page=${page}` : "";
  return `${API_BASE_URL}/api/manual/pdf${pageFragment}`;
}

async function apiJson<T>(path: string, options: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      credentials: "include",
      headers: {
        ...(options.body ? { "Content-Type": "application/json" } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error("서버에 연결할 수 없습니다. 백엔드가 실행 중인지 확인해 주세요.");
  }

  const body = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const detail = body && typeof body.detail === "string" ? body.detail : "요청을 처리하지 못했습니다.";
    throw new Error(detail);
  }
  return body as T;
}

export function fetchAuthStatus(): Promise<AuthStatusResponse> {
  return apiJson<AuthStatusResponse>("/api/auth/status");
}

export function fetchCurrentUser(): Promise<AuthUser> {
  return apiJson<AuthUser>("/api/auth/me");
}

export function login(username: string, password: string): Promise<AuthUser> {
  return apiJson<AuthUser>("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ username, password }),
  });
}

export function setupAdmin(
  displayName: string,
  username: string,
  password: string,
): Promise<AuthUser> {
  return apiJson<AuthUser>("/api/auth/setup", {
    method: "POST",
    body: JSON.stringify({ displayName, username, password }),
  });
}

export async function logout(): Promise<void> {
  await apiJson<null>("/api/auth/logout", { method: "POST" });
}

export function fetchAdminContacts(): Promise<ContactDirectoryResponse> {
  return apiJson<ContactDirectoryResponse>("/api/admin/contacts");
}

export function createAdminContact(input: AdminContactInput): Promise<ContactDirectoryEntry> {
  return apiJson<ContactDirectoryEntry>("/api/admin/contacts", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateAdminContact(
  id: string,
  input: AdminContactInput,
): Promise<ContactDirectoryEntry> {
  return apiJson<ContactDirectoryEntry>(`/api/admin/contacts/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export async function deleteAdminContact(id: string): Promise<void> {
  await apiJson<{ ok: boolean }>(`/api/admin/contacts/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function fetchAdminGuides(): Promise<QuickGuideListResponse> {
  return apiJson<QuickGuideListResponse>("/api/admin/guides");
}

export function updateAdminGuide(id: string, input: AdminGuideInput): Promise<QuickGuide> {
  return apiJson<QuickGuide>(`/api/admin/guides/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export async function resetAdminGuide(id: string): Promise<void> {
  await apiJson<{ ok: boolean }>(`/api/admin/guides/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export function fetchAdminManualCatalog(): Promise<ManualCatalogResponse> {
  return apiJson<ManualCatalogResponse>("/api/admin/manual");
}

export function createAdminManualEntry(input: AdminManualInput): Promise<ManualCatalogEntry> {
  return apiJson<ManualCatalogEntry>("/api/admin/manual", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateAdminManualEntry(
  id: string,
  input: AdminManualInput,
): Promise<ManualCatalogEntry> {
  return apiJson<ManualCatalogEntry>(`/api/admin/manual/${encodeURIComponent(id)}`, {
    method: "PUT",
    body: JSON.stringify(input),
  });
}

export function deleteOrRestoreAdminManualEntry(id: string): Promise<ManualAdminDeleteResponse> {
  return apiJson<ManualAdminDeleteResponse>(`/api/admin/manual/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
}

export async function searchComplaints(
  query: string,
  topK = 3,
): Promise<SearchResponse> {
  let response: Response;

  try {
    response = await fetch(`${API_BASE_URL}/api/search`, {
      method: "POST",
      credentials: "include",
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
    response = await fetch(`${API_BASE_URL}/api/guides`, { credentials: "include" });
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
    response = await fetch(`${API_BASE_URL}/api/contacts`, { credentials: "include" });
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
    response = await fetch(`${API_BASE_URL}/api/manual`, { credentials: "include" });
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
