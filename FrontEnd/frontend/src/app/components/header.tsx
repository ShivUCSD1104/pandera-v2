'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

const Header = () => {
  const pathname = usePathname();

  const isActiveLink = (path: string) => {
    return pathname === path ? 'shadow-inner shadow-gray-300 font-bold' : 'hover:shadow-inner';
  };

  return (
    <header className="bg-white p-4">
      <nav className="max-w-6xl mx-auto">
        
          <div className="flex justify-between items-center p-2">
            <div className="flex items-center">
              <Link href="/" className="p-1 bg-none rounded-full mr-2 items-center">
                <svg fill="#000000" width="32px" height="32px" viewBox="0 0 16 16" id="puzzle-16px" xmlns="http://www.w3.org/2000/svg">
                  <path id="Path_56" data-name="Path 56" d="M-8.5,16h-4a.5.5,0,0,1-.5-.5v-1A1.5,1.5,0,0,0-14.5,13,1.5,1.5,0,0,0-16,14.5v1a.5.5,0,0,1-.5.5h-4a.5.5,0,0,1-.5-.5V3.5a.5.5,0,0,1,.5-.5H-17V2.5A2.5,2.5,0,0,1-14.5,0,2.5,2.5,0,0,1-12,2.5V3h3.5a.5.5,0,0,1,.5.5V7h.5A2.5,2.5,0,0,1-5,9.5,2.5,2.5,0,0,1-7.5,12H-8v3.5A.5.5,0,0,1-8.5,16ZM-12,15h3V11.5a.5.5,0,0,1,.5-.5h1A1.5,1.5,0,0,0-6,9.5,1.5,1.5,0,0,0-7.5,8h-1A.5.5,0,0,1-9,7.5V4h-3.5a.5.5,0,0,1-.5-.5v-1A1.5,1.5,0,0,0-14.5,1,1.5,1.5,0,0,0-16,2.5v1a.5.5,0,0,1-.5.5H-20V15h3v-.5A2.5,2.5,0,0,1-14.5,12,2.5,2.5,0,0,1-12,14.5Z" transform="translate(21)"/>
                  
                </svg>
              </Link>
              <Link
                href="/"
                className={`text-xl px-6 py-3 text-gray-600 rounded-lg transition-all duration-300 
                ${isActiveLink('/')}`}
              >
                {'///pandera'}
              </Link>
            </div>
            <ul className="flex items-center space-x-4">
              <li>
                <Link
                  href="/models"
                  className={`px-6 py-3 rounded-lg transition-all duration-300 ${isActiveLink('/models')} 
                  text-gray-600`}
                >
                  Models
                </Link>
              </li>
              <li>
                <Link
                  href="/projects"
                  className={`px-6 py-3 rounded-lg transition-all duration-300 ${isActiveLink('/projects')} 
                  text-gray-600`}
                >
                  Projects
                </Link>
              </li>
              <li>
                <Link
                  href="/research"
                  className={`px-6 py-3 rounded-lg transition-all duration-300 ${isActiveLink('/research')} 
                  text-gray-600`}
                >
                  Research
                </Link>
              </li>
              <li>
                <Link
                  href="/code"
                  className={`px-6 py-3 rounded-lg transition-all duration-300 ${isActiveLink('/code')} 
                  text-gray-600`}
                >
                  Code
                </Link>
              </li>
              <li>
                <Link
                  href="/people"
                  className={`px-6 py-3 rounded-lg transition-all duration-300 ${isActiveLink('/people')} 
                  text-gray-600`}
                >
                  People
                </Link>
              </li>
            </ul>
          </div>
        
      </nav>
    </header>
  );
};

export default Header;
