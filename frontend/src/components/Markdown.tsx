"use client";

import React, { memo, useMemo } from "react";

/**
 * Lightweight Markdown -> React renderer (zero dependencies).
 *
 * Supports the subset of Markdown that LLM responses actually use:
 *   - **bold**, *italic*, `inline code`
 *   - ## headings (h2-h4)
 *   - - unordered and 1. ordered lists (one level)
 *   - [text](url) links
 *   - [1] inline citation references (superscript pills)
 *   - --- horizontal rules
 *   - > blockquotes
 *   - ```code blocks```
 *   - | tables |
 *
 * 2026 design: Grok-inspired clean typography with proper spacing.
 */

// ─── Safe URL validator ───

function isSafeUrl(url: string): boolean {
  if (url.startsWith("/") || url.startsWith("#")) return true;
  try {
    const parsed = new URL(url);
    return parsed.protocol === "http:" || parsed.protocol === "https:";
  } catch {
    return false;
  }
}

// ─── Inline rendering ───

function renderInline(text: string): React.ReactNode[] {
  const nodes: React.ReactNode[] = [];
  const pattern =
    /(\*\*\*(.+?)\*\*\*)|(\*\*(.+?)\*\*)|(?<!\*)\*([^*]+)\*(?!\*)|(``?([^`]+)``?)|\[(\d+)\]|\[([^\]]+)\]\(([^)]+)\)/g;
  let lastIdx = 0;
  let match: RegExpExecArray | null;
  let key = 0;

  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIdx) {
      nodes.push(text.slice(lastIdx, match.index));
    }

    if (match[2]) {
      // ***bold italic***
      nodes.push(
        <strong key={key++}>
          <em>{match[2]}</em>
        </strong>,
      );
    } else if (match[4]) {
      // **bold**
      nodes.push(<strong key={key++}>{match[4]}</strong>);
    } else if (match[5]) {
      // *italic*
      nodes.push(<em key={key++}>{match[5]}</em>);
    } else if (match[7]) {
      // `inline code`
      nodes.push(
        <code key={key++} className="md-inline-code">
          {match[7]}
        </code>,
      );
    } else if (match[8]) {
      // [1] citation ref
      nodes.push(
        <sup key={key++} className="md-cite-ref">
          {match[8]}
        </sup>,
      );
    } else if (match[9] && match[10]) {
      // [text](url)
      const safeUrl = isSafeUrl(match[10]) ? match[10] : "#";
      nodes.push(
        <a
          key={key++}
          href={safeUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="md-link"
        >
          {match[9]}
        </a>,
      );
    }
    lastIdx = match.index + match[0].length;
  }

  if (lastIdx < text.length) {
    nodes.push(text.slice(lastIdx));
  }

  return nodes.length > 0 ? nodes : [text];
}

// ─── Block types ───

interface Block {
  type:
    | "paragraph"
    | "heading"
    | "ul"
    | "ol"
    | "code"
    | "blockquote"
    | "hr"
    | "table";
  level?: number;
  items?: string[];
  lang?: string;
  text?: string;
  rows?: string[][];
}

// ─── Block parser ───

function parseBlocks(src: string): Block[] {
  const lines = src.split("\n");
  const blocks: Block[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];

    // Fenced code block
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const codeLines: string[] = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        codeLines.push(lines[i]);
        i++;
      }
      blocks.push({ type: "code", text: codeLines.join("\n"), lang });
      i++;
      continue;
    }

    // HR
    if (/^-{3,}$/.test(line.trim())) {
      blocks.push({ type: "hr" });
      i++;
      continue;
    }

    // Heading (h2-h4)
    const hMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (hMatch) {
      const level = Math.max(2, Math.min(4, hMatch[1].length));
      blocks.push({ type: "heading", level, text: hMatch[2] });
      i++;
      continue;
    }

    // Blockquote
    if (line.startsWith("> ") || line === ">") {
      const qLines: string[] = [];
      while (
        i < lines.length &&
        (lines[i].startsWith("> ") || lines[i] === ">")
      ) {
        qLines.push(lines[i].replace(/^>\s?/, ""));
        i++;
      }
      blocks.push({ type: "blockquote", text: qLines.join("\n") });
      continue;
    }

    // Table (pipe-delimited)
    if (line.includes("|") && line.trim().startsWith("|")) {
      const tableLines: string[] = [];
      while (i < lines.length && lines[i].includes("|")) {
        // Skip separator rows
        if (!/^\|[\s-:|]+\|$/.test(lines[i].trim())) {
          tableLines.push(lines[i]);
        }
        i++;
      }
      if (tableLines.length > 0) {
        const rows = tableLines.map((r) =>
          r
            .split("|")
            .filter(Boolean)
            .map((c) => c.trim()),
        );
        blocks.push({ type: "table", rows });
      }
      continue;
    }

    // Unordered list
    if (/^[-*]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^[-*]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^[-*]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ul", items });
      continue;
    }

    // Ordered list
    if (/^\d+[.)]\s+/.test(line)) {
      const items: string[] = [];
      while (i < lines.length && /^\d+[.)]\s+/.test(lines[i])) {
        items.push(lines[i].replace(/^\d+[.)]\s+/, ""));
        i++;
      }
      blocks.push({ type: "ol", items });
      continue;
    }

    // Empty line
    if (!line.trim()) {
      i++;
      continue;
    }

    // Paragraph — collect consecutive non-special lines
    const pLines: string[] = [line];
    i++;
    while (
      i < lines.length &&
      lines[i].trim() &&
      !lines[i].startsWith("```") &&
      !lines[i].startsWith("# ") &&
      !lines[i].startsWith("## ") &&
      !lines[i].startsWith("### ") &&
      !lines[i].startsWith("#### ") &&
      !lines[i].startsWith("> ") &&
      !/^[-*]\s+/.test(lines[i]) &&
      !/^\d+[.)]\s+/.test(lines[i]) &&
      !/^-{3,}$/.test(lines[i].trim()) &&
      !(lines[i].includes("|") && lines[i].trim().startsWith("|"))
    ) {
      pLines.push(lines[i]);
      i++;
    }
    blocks.push({ type: "paragraph", text: pLines.join("\n") });
  }

  return blocks;
}

// ─── Block renderer ───

function renderBlocks(blocks: Block[]): React.ReactNode[] {
  return blocks.map((block, i) => {
    switch (block.type) {
      case "hr":
        return <hr key={i} className="md-hr" />;

      case "heading": {
        const Tag = `h${block.level}` as "h2" | "h3" | "h4";
        return (
          <Tag key={i} className={`md-h${block.level}`}>
            {renderInline(block.text!)}
          </Tag>
        );
      }

      case "code":
        return (
          <pre key={i} className="md-code-block md-code-block--dark">
            {block.lang && (
              <span className="md-code-lang">{block.lang}</span>
            )}
            <code className="md-code-content">{block.text}</code>
          </pre>
        );

      case "blockquote":
        return (
          <blockquote key={i} className="md-blockquote">
            {renderInline(block.text!)}
          </blockquote>
        );

      case "ul":
        return (
          <ul key={i} className="md-list">
            {block.items!.map((item, j) => (
              <li key={j}>{renderInline(item)}</li>
            ))}
          </ul>
        );

      case "ol":
        return (
          <ol key={i} className="md-list md-ol">
            {block.items!.map((item, j) => (
              <li key={j}>{renderInline(item)}</li>
            ))}
          </ol>
        );

      case "table":
        if (!block.rows || block.rows.length === 0) return null;
        return (
          <div key={i} className="md-table-wrap">
            <table className="md-table">
              <thead>
                <tr>
                  {block.rows[0].map((cell, j) => (
                    <th key={j}>{renderInline(cell)}</th>
                  ))}
                </tr>
              </thead>
              {block.rows.length > 1 && (
                <tbody>
                  {block.rows.slice(1).map((row, ri) => (
                    <tr key={ri}>
                      {row.map((cell, ci) => (
                        <td key={ci}>{renderInline(cell)}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              )}
            </table>
          </div>
        );

      case "paragraph":
      default:
        return (
          <p key={i} className="md-p">
            {renderInline(block.text!)}
          </p>
        );
    }
  });
}

// ─── Component ───

function MarkdownInner({ content }: { content: string }) {
  const rendered = useMemo(() => {
    if (!content) return null;
    const blocks = parseBlocks(content);
    return renderBlocks(blocks);
  }, [content]);

  return <div className="md-body">{rendered}</div>;
}

export const Markdown = memo(MarkdownInner);
