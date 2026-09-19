const API_BASE = "/api/v1";

function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

export async function apiRequest<T = any>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Include CSRF token on modifying requests
  if (["POST", "PUT", "PATCH", "DELETE"].includes(options.method?.toUpperCase() || "")) {
    const csrfToken = getCookie("ff_csrf");
    if (csrfToken) {
      headers.set("X-CSRF-Token", csrfToken);
    }
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers,
    credentials: "include", // Ensure session cookies are sent
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) errorDetail = errJson.detail;
    } catch {
      // Non-JSON error
    }
    throw new Error(errorDetail);
  }

  // If response is empty (e.g. 204 or logout)
  const contentType = response.headers.get("content-type");
  if (contentType && contentType.includes("application/json")) {
    return response.json();
  }
  return {} as T;
}

export const api = {
  // Auth
  register: (data: { email: string; password: string; displayName: string }) =>
    apiRequest("/auth/register", { method: "POST", body: JSON.stringify(data) }),
  login: (data: { email: string; password: string }) =>
    apiRequest("/auth/login", { method: "POST", body: JSON.stringify(data) }),
  logout: () => apiRequest("/auth/logout", { method: "POST" }),
  getMe: () => apiRequest("/auth/me"),
  getCsrf: () => apiRequest("/auth/csrf"),

  // Documents
  uploadDocument: (formData: FormData) =>
    apiRequest("/documents", { method: "POST", body: formData }),
  getDocuments: () => apiRequest("/documents"),
  getDocument: (id: string) => apiRequest(`/documents/${id}`),
  deleteDocument: (id: string) => apiRequest(`/documents/${id}`, { method: "DELETE" }),

  // Analyses
  getAnalysis: (id: string) => apiRequest(`/analyses/${id}`),
  triggerAnalysis: (docId: string) =>
    apiRequest(`/documents/${docId}/analyses`, { method: "POST" }),

  // URL Checks
  submitUrl: (url: string) =>
    apiRequest("/url-checks", { method: "POST", body: JSON.stringify({ url }) }),
  getUrlChecks: () => apiRequest("/url-checks"),
  getUrlCheck: (id: string) => apiRequest(`/url-checks/${id}`),
  deleteUrlCheck: (id: string) => apiRequest(`/url-checks/${id}`, { method: "DELETE" }),

  // Jobs
  getJobStatus: (id: string) => apiRequest(`/jobs/${id}`),
  cancelJob: (id: string) => apiRequest(`/jobs/${id}/cancel`, { method: "POST" }),

  // Calculations
  calculateLoan: (data: any) =>
    apiRequest("/calculations/loan", { method: "POST", body: JSON.stringify(data) }),

  // Reports
  getReports: () => apiRequest("/reports"),
  getReport: (type: string, id: string) => apiRequest(`/reports/${type}/${id}`),
  askReportQuestion: (type: string, id: string, question: string) =>
    apiRequest(`/reports/${type}/${id}/questions`, {
      method: "POST",
      body: JSON.stringify({ question }),
    }),

  // Family Sharing
  createInvitation: (data: any) =>
    apiRequest("/family/invitations", { method: "POST", body: JSON.stringify(data) }),
  shareInvitationViaWhatsApp: (data: {
    invitationId: string;
    invitationLink: string;
    recipientPhone: string;
  }) => apiRequest("/family/whatsapp", { method: "POST", body: JSON.stringify(data) }),
  acceptInvitation: (token: string) =>
    apiRequest("/family/invitations/accept", {
      method: "POST",
      body: JSON.stringify({ token }),
    }),
  getShares: () => apiRequest("/family/shares"),
  revokeShare: (shareId: string) =>
    apiRequest(`/family/shares/${shareId}`, { method: "DELETE" }),

  // Privacy
  getPrivacySettings: () => apiRequest("/privacy/settings"),
  updatePrivacySettings: (documentRetentionDays: number) =>
    apiRequest("/privacy/settings", {
      method: "PATCH",
      body: JSON.stringify({ documentRetentionDays }),
    }),
  deleteAccount: () => apiRequest("/privacy/account-deletion", { method: "POST" }),
  getFamilyAudit: () => apiRequest("/family/audit"),
  downloadDemoFixture: async (fixtureKey: string) => {
    const response = await fetch(`/api/v1/demo/documents/${fixtureKey}`, {
      credentials: "include",
    });
    if (!response.ok) {
      throw new Error("Could not load synthetic fixture.");
    }
    const blob = await response.blob();
    const disposition = response.headers.get("content-disposition") || "";
    const match = disposition.match(/filename="?([^"]+)"?/);
    const filename = match?.[1] || `${fixtureKey}_demo_loan.pdf`;
    return new File([blob], filename, { type: blob.type || "application/pdf" });
  },
};
