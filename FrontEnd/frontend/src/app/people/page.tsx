'use client';

export default function MyNotePage() {
  return (
    <div>
      <main className="min-h-screen bg-[url(/paper.jpg)] p-8">
        <div className="bg-white p-4 rounded-2xl shadow-[8px_8px_16px_#bebebe] hover:shadow-inner hover:shadow-gray-300">
          <div className="flex flex-col items-center">
            {/* Shiv Mehta */}
            <div className="text-2xl text-black">Shiv Mehta - Co-Founder & President</div>
            <div className="text-xl text-black">{"Data Science @ UCSD '27"}</div>
            <br />
            <div className="text-sm text-black max-w-prose text-center">
              Machine Learning Researcher at SEELab @ UCSD. Interested in: signal processing, modeling and research,
              causal inference, bayesian statistics, and computational mathematics.
            </div>
            <br />
            <div className="flex flex-row w-full items-center bg-black rounded-lg">
              <a
                href="https://github.com/ShivUCSD1104"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center"
              >
                GitHub
              </a>
              <a
                href="https://www.shivmehta.com/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center"
              >
                Personal Website
              </a>
              <a
                href="https://www.linkedin.com/in/shivmehta722/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-black p-2 pl-4 pr-6 m-4 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center"
              >
                LinkedIn
              </a>
            </div>

            {/* Sukhman Virk */}
            <div className="mt-8 text-2xl text-black">Sukhman Virk - Co-Founder</div>
            <div className="text-xl text-black">{"Mathematics - Computer Science @ UCSD '24"}</div>
            <br />
            <div className="text-sm text-black max-w-prose text-center">
              UC San Diego graduate (June 2024) with a strong academic record (Major GPA 3.95) in Mathematics & Computer Science,
              plus minors in Cognitive Science and Economics. Skilled in full-stack development, cloud architecture, and
              machine learning, with hands-on experience through internships and personal projects. Passionate about quantitative finance,
              security, performance optimization, and building scalable systems.
            </div>
            <br />
            <div className="flex flex-row w-full items-center bg-black rounded-lg">
              <a
                href="https://github.com/AstuteFern"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-black p-2 pl-4 pr-4 m-6 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center"
              >
                GitHub
              </a>
              <a
                href="https://www.linkedin.com/in/sukhman-virk-8b1296198/"
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 text-black p-2 pl-4 pr-6 m-4 bg-white rounded-lg hover:shadow-inner hover:shadow-gray-300 transition-all duration-300 text-center"
              >
                LinkedIn
              </a>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
