'use client';

import { motion } from 'framer-motion';

interface AnimatedTagsProps {
  tags: string[];
}

const gradients = [
  'bg-gradient-to-r from-red-300 to-yellow-300',
  'bg-gradient-to-r from-green-300 to-blue-300',
  'bg-gradient-to-r from-purple-300 to-pink-300',
  'bg-gradient-to-r from-indigo-300 to-purple-300',
  'bg-gradient-to-r from-yellow-300 to-green-300',
  'bg-gradient-to-r from-sky-300 to-blue-300',
  'bg-gradient-to-r from-blue-300 to-indigo-300',
  'bg-gradient-to-r from-teal-300 to-green-300',
];

export default function AnimatedTags({ tags }: AnimatedTagsProps) {
  const duplicatedTags = [...tags, ...tags];

  return (
    <div className="relative overflow-hidden w-full h-16 bg-none">
      <motion.div
        className="flex space-x-8 absolute whitespace-nowrap"
        initial={{ x: 0 }}
        animate={{ x: `-${0.3 * (tags.length + 1)}%` }}
        transition={{ repeat: Infinity, duration: 20, ease: 'linear' }}
        style={{ display: 'flex', width: `${200 * tags.length}%` }}
      >
        {duplicatedTags.map((tag, index) => {
          const gradientClass = gradients[index % gradients.length];
          return (
            <span
              key={index}
              className={`${gradientClass} inline-block text-transparent bg-clip-text text-lg px-4 py-1 border-2 border-black rounded-lg shadow-lg shadow-gray-600 bg-black bg-opacity-100`}
            >
              {tag}
            </span>
          );
        })}
      </motion.div>
    </div>
  );
}
