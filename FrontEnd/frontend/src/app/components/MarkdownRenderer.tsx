"use client";

import { useEffect, useState } from "react";
import ReactMarkdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import remarkToc from "remark-toc";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import "katex/dist/katex.min.css";

interface MarkdownRendererProps {
  filePath: string;
}

// Render fenced code blocks with Prism highlighting; leave inline `code` plain.
const components: Components = {
  code({ className, children }) {
    const match = /language-(\w+)/.exec(className || "");
    return match ? (
      <SyntaxHighlighter language={match[1]} style={oneDark} PreTag="div">
        {String(children).replace(/\n$/, "")}
      </SyntaxHighlighter>
    ) : (
      <code className={className}>{children}</code>
    );
  },
};

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ filePath }) => {
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch(filePath)
      .then((res) => res.text())
      .then((text) => setContent(text));
  }, [filePath]);

  return (
    <div className="prose prose-lg max-w-none text-black bg-white rounded-2xl p-6">
      <ReactMarkdown
        // remarkMath parses $...$/$$...$$; remarkToc injects a list under a
        // "## Table of Contents" heading if the document has one.
        remarkPlugins={[remarkGfm, remarkMath, remarkToc]}
        // rehypeRaw first (reparse inline HTML), then rehypeKatex to render math.
        rehypePlugins={[rehypeRaw, rehypeKatex]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
