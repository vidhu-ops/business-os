"use client";

import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { brandReportText, sanitizeReportMarkdown } from "@/lib/reportBrand";

type ReportMarkdownProps = {
  markdown: string;
  title?: string;
  subtitle?: string;
};

export function ReportMarkdown({ markdown, title, subtitle }: ReportMarkdownProps) {
  const body = sanitizeReportMarkdown(brandReportText(markdown));

  if (!body.trim()) {
    return <p className="muted text-sm">No report content yet.</p>;
  }

  return (
    <article className="iid-report">
      {(title || subtitle) && (
        <header className="iid-report-hero">
          {title ? <h1 className="iid-report-title">{title}</h1> : null}
          {subtitle ? <p className="iid-report-subtitle">{subtitle}</p> : null}
        </header>
      )}
      <div className="iid-report-body">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            h1: ({ children }) => <h2 className="iid-report-h1">{children}</h2>,
            h2: ({ children }) => <h3 className="iid-report-h2">{children}</h3>,
            h3: ({ children }) => <h4 className="iid-report-h3">{children}</h4>,
            p: ({ children }) => <p className="iid-report-p">{children}</p>,
            ul: ({ children }) => <ul className="iid-report-ul">{children}</ul>,
            ol: ({ children }) => <ol className="iid-report-ol">{children}</ol>,
            li: ({ children }) => <li className="iid-report-li">{children}</li>,
            strong: ({ children }) => <strong className="iid-report-strong">{children}</strong>,
            blockquote: ({ children }) => <blockquote className="iid-report-quote">{children}</blockquote>,
            hr: () => <hr className="iid-report-hr" />,
            table: ({ children }) => (
              <div className="iid-report-table-wrap">
                <table className="iid-report-table">{children}</table>
              </div>
            ),
            th: ({ children }) => <th>{children}</th>,
            td: ({ children }) => <td>{children}</td>,
            a: ({ href, children }) => (
              <a href={href} className="iid-report-link" target="_blank" rel="noreferrer">
                {children}
              </a>
            ),
            code: ({ className, children }) => {
              const isBlock = Boolean(className);
              if (isBlock) {
                return <code className="iid-report-code-block">{children}</code>;
              }
              return <code className="iid-report-code">{children}</code>;
            },
          }}
        >
          {body}
        </ReactMarkdown>
      </div>
    </article>
  );
}
