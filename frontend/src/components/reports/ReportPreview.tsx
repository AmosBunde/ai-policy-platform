import { FileText } from "lucide-react";
import { Button } from "../ui/Button";
import type { Report } from "./ReportCard";

const ALLOWED_PROTOCOLS = ["https:", "blob:"];

function isValidDownloadUrl(url: string): boolean {
  try {
    const parsed = new URL(url, window.location.origin);
    return ALLOWED_PROTOCOLS.includes(parsed.protocol);
  } catch {
    return false;
  }
}

interface ReportPreviewProps {
  report: Report | null;
  previewUrl?: string;
  onDownloadPdf: () => void;
  onDownloadDocx: () => void;
  onClose: () => void;
}

export function ReportPreview({ report, previewUrl, onDownloadPdf, onDownloadDocx, onClose }: ReportPreviewProps) {
  if (!report) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-slate-500">
        <FileText className="h-12 w-12 mb-3" />
        <p className="text-sm">Select a report to preview.</p>
      </div>
    );
  }

  const safePreviewUrl = previewUrl && isValidDownloadUrl(previewUrl) ? previewUrl : null;

  const handleDownload = (handler: () => void, url?: string) => {
    if (url && !isValidDownloadUrl(url)) return;
    handler();
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-medium">{report.title}</h3>
        <Button variant="ghost" size="sm" onClick={onClose}>
          Close
        </Button>
      </div>

      {safePreviewUrl ? (
        <iframe
          src={safePreviewUrl}
          title={`Preview: ${report.title}`}
          sandbox="allow-same-origin"
          className="w-full h-[500px] rounded-lg border border-slate-200 dark:border-slate-700 bg-white"
        />
      ) : (
        <div className="w-full h-[500px] rounded-lg border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-navy-900 flex flex-col items-center justify-center text-slate-500">
          <FileText className="h-16 w-16 mb-4" />
          <p className="text-sm font-medium">{report.title}</p>
          <p className="text-xs mt-1">
            {report.status === "completed"
              ? "Preview not available — download the report instead."
              : "Report is still being generated."}
          </p>
        </div>
      )}

      <div className="flex items-center gap-3">
        <Button
          size="sm"
          onClick={() => handleDownload(onDownloadPdf)}
          disabled={report.status !== "completed"}
        >
          Download PDF
        </Button>
        <Button
          size="sm"
          variant="secondary"
          onClick={() => handleDownload(onDownloadDocx)}
          disabled={report.status !== "completed"}
        >
          Download DOCX
        </Button>
      </div>
    </div>
  );
}
