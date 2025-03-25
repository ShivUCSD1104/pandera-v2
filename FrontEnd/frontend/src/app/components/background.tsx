'use client';

import { useEffect, useState } from 'react';
import Image from 'next/image';

const images = [
  '/gears.svg',
  '/cube.svg',
  '/squares.svg',
  '/barcode.svg',
];

const RandomBackdrop = () => {
  const [positions, setPositions] = useState<{ top: string; left: string; src: string }[]>([]);

  useEffect(() => {
    const newPositions = images.map((src) => ({
      src,
      top: `${Math.random() * 100}vh`,
      left: `${Math.random() * 100}vw`,
    }));
    setPositions(newPositions);
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden" style={{ zIndex: 0}}>
      {positions.map((pos, index) => (
        <Image
        key={index}
        src={pos.src}
        alt={`Random SVG ${index}`}
        className="absolute"
        style={{ top: pos.top, left: pos.left }}
        width={50}
        height={50}
      />
      ))}
    </div>
  );
};

export default RandomBackdrop;