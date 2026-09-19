export function describeSharePreview(permissions: {
  shareSummary: boolean;
  shareFindings: boolean;
  shareFinancialAmounts: boolean;
  shareSourceExcerpts: boolean;
  shareOriginalDocument: boolean;
}): string[] {
  const lines: string[] = [];
  lines.push(permissions.shareSummary ? "Summary assessment will be visible." : "Summary will stay private.");
  lines.push(permissions.shareFindings ? "Charge findings will be listed." : "Findings will be hidden.");
  lines.push(
    permissions.shareFinancialAmounts
      ? "Loan amount, rate, EMI, and rupee figures will be shown."
      : "Rupee figures will appear as [Private Amount]."
  );
  lines.push(
    permissions.shareSourceExcerpts
      ? "Verbatim clause quotes will be shown."
      : "Source excerpts will be withheld."
  );
  lines.push(
    permissions.shareOriginalDocument
      ? "The original document file can be downloaded."
      : "The original document file will not be shared."
  );
  return lines;
}

export const FINDING_CATEGORY_ORDER = [
  "Explicitly disclosed charge",
  "Easily overlooked charge",
  "Conditional charge",
  "Unclear or missing disclosure",
  "Conflicting financial terms",
] as const;
