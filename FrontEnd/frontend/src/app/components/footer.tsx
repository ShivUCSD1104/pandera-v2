'use client';

const Footer = () => {
  return (
    <footer className="bg-white p-4 mt-auto">
      <div className="max-w-6xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-center p-2">
          <div className="text-black mb-4 md:mb-0">
            © 2025 Pandera. All rights reserved.
          </div>
          
          <div className="flex space-x-6">
            <a href="#" className="text-black hover:text-yellow-400 transition-colors">
              Twitter
            </a>
            <a href="#" className="text-black hover:text-yellow-400 transition-colors">
              LinkedIn
            </a>
            <a href="#" className="text-black hover:text-yellow-400 transition-colors">
              GitHub
            </a>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
