'use client';

import { useState } from "react";
import { useRouter } from "next/navigation";

const fileSystem = {
  root: ["models", "projects", "research", "code"],
  models: ["Implied Volatility Surface", "Order Book Ravine", "US Fix Income Yield"],
  projects: ["Citadel Terminal", "Jane Street Puzzles"],
  research: ["Quantum Optimized High Frequency Trading"],
  code: ["GPU Optimized Black Scholes"],
};

type FileSystemKey = keyof typeof fileSystem;

export default function Terminal() {
  const [currentPath, setCurrentPath] = useState<FileSystemKey>("root");
  const [command, setCommand] = useState("");
  const [output, setOutput] = useState<string[]>([]);
  const router = useRouter();

  const handleCommand = () => {
    const [cmd, arg] = command.split(" ");

    if (cmd === "ls") {
      if (arg && arg in fileSystem) {
        setOutput(fileSystem[arg as FileSystemKey]);
      } else if (arg === undefined || arg === currentPath) {
        setOutput(fileSystem[currentPath]);
      } else {
        setOutput(["Error: Directory not found"]);
      }
    } else if (cmd === "cd") {
      if (arg && arg in fileSystem) {
        setCurrentPath(arg as FileSystemKey);
        setOutput([`Changed directory to ${arg}`]);
      } else {
        setOutput(["Error: Directory not found"]);
      }
    } else if (cmd === "open") {
      if (arg && arg in fileSystem) {
        router.push(`/${arg}`);
      } else {
        setOutput(["Error: Directory not found"]);
      }
    } else {
      setOutput(["Error: Unknown command"]);
    }
    setCommand("");
  };

  return (
    <div className="bg-black text-green-400 h-64 p-4 font-mono white-cursor hover:border-2 hover:border-white">
      <div className="overflow-y-auto h-5/6 mb-4">
        {output.map((line, index) => (
          <div key={index}>{line}</div>
        ))}
      </div>
      <div className="flex items-center">
        <span className="pr-2">(base) ///pandera@{currentPath}:~$</span>
        <input
          className="bg-black text-green-400 outline-none flex-grow"
          type="text"
          value={command}
          onChange={(e) => setCommand(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleCommand();
          }}
        />
      </div>
    </div>
  );
}