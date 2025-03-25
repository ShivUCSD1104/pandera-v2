'use client';

import MarkdownRenderer from '../components/MarkdownRenderer'; 

export default function MyNotePage() {
  return (
    <div>
      <main className="min-h-screen bg-[url(/paper.jpg)] p-8">
      <div className="bg-white p-4 rounded-2xl shadow-[8px_8px_16px_#bebebe] hover:shadow-inner hover:shadow-gray-300">
        <MarkdownRenderer filePath="/notes/research/research.md" />
      </div>
      </main>
  </div>

  ) ;
}