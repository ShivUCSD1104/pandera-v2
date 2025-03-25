import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";

interface MarkdownRendererProps {
  filePath: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ filePath }) => {
  const [content, setContent] = useState("");

  useEffect(() => {
    fetch(filePath)
      .then((res) => res.text())
      .then((text) => setContent(text));
  }, [filePath]);

  return (
    <div className="prose prose-lg bg-white rounded-2xl p-6">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]} // Allows HTML inside Markdown
        className="text-black"
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default MarkdownRenderer;
