'use client';

export default function MyNotePage() {
  return (
    <div>
      <main className="min-h-screen bg-[url(/paper.jpg)] p-8">
      <div className="bg-white p-4 rounded-2xl shadow-[8px_8px_16px_#bebebe] hover:shadow-inner hover:shadow-gray-300">
        <div className="flex flex-col items-center">
          <div className="text-2xl text-black">Shiv Mehta - Co-Founder & President</div>
          <div className="text-xl text-black">{"Data Science @ UCSD '27"}</div>
          <br />
          <div className='text-sm text-black'>Lorem ipsum dolor sit amet consectetur adipisicing elit. Corporis excepturi error consequuntur nam, necessitatibus deserunt similique ipsa rem dolorem doloribus!</div>
          <br />
          <div className="flex flex-row w-full items-center bg-black rounded-lg">
            <a href="#" className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center">
              Google Scholar
            </a>
            <a href="#" className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center">
              Personal Website
            </a>
            <a href="#" className="flex-1 text-black p-2 pl-4 pr-6 m-4 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center">
              LinkedIn
            </a>
          </div>
          <div className="text-2xl text-black">Sukhman Virk - Co-Founder</div>
          <div className="text-xl text-black">{"Mathematics - Computer Science @ UCSD '24"}</div>
          <br />
          <div className='text-sm text-black'>Lorem ipsum dolor sit amet consectetur adipisicing elit. Corporis excepturi error consequuntur nam, necessitatibus deserunt similique ipsa rem dolorem doloribus!</div>
          <br />
          <div className="flex flex-row w-full items-center bg-black rounded-lg">
            <a href="#" className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center">
              GitHub
            </a>
            <a href="#" className="flex-1 text-black p-2 pl-4 pr-6 m-4 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center">
              LinkedIn
            </a>
          </div>
        </div>
      </div>
      </main>
  </div>

  ) ;
}