'use client';
import { useState, useEffect } from 'react';
import Image from 'next/image';

const TypingEffect = () => {
  const text = "(base) ///pandera @UCSD ~ %";
  const [displayedText, setDisplayedText] = useState('');
  const [index, setIndex] = useState(0);
  const [isImageVisible, setIsImageVisible] = useState(true);
  const [, setIsTypingComplete] = useState(false);

  useEffect(() => {
    const typingInterval = setInterval(() => {
      if (index < text.length) {
        setDisplayedText((prev) => prev + text[index]);
        setIndex((prev) => prev + 1);
      } else {
        setIsTypingComplete(true); // Mark typing as complete
        clearInterval(typingInterval);
      }
    }, 150); // Typing speed

    return () => clearInterval(typingInterval);
  }, [index, text]);

  useEffect(() => {
    const blinkingInterval = setInterval(() => {
      setIsImageVisible((prev) => !prev); // Toggle visibility
    }, 1000); // Blink once a second

    return () => clearInterval(blinkingInterval);
  }, []);

  return (
    <div className="flex items-center">
      <h1 className="text-6xl font-black text-black flex">
        {displayedText}
        <Image
          src="/rec.svg"
          alt="Icon"
          width={64}
          height={64}
          className={`h-16 w-16 transition-opacity duration-500 ${
            isImageVisible ? 'opacity-100' : 'opacity-0'
          }`}
          style={{
            marginLeft: '10px', // Adds spacing between text and image
          }}
        />
      </h1>
    </div>
  );
};

export default TypingEffect;
