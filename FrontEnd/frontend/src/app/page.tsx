import Link from 'next/link'
import TypingEffect from './components/typingeffect';
import Terminal from './components/shell'
import AnimatedTags from './components/tags';

export default function Home() {
  return (
    <div>
      <main className="min-h-screen bg-[url(/paper.jpg)] p-8">
      
        {/* Hero Section */}
        <section className="max-w-6xl mx-auto py-8">
          <div className="flex flex-col items-center text-center space-y-8">
            <TypingEffect />
            <p className="text-xl text-gray-600 max-w-1xl">
              Data Science. High Performance Compute. Econometrics. Puzzles & Strategy.
            </p>
            <div className="flex flex-row space-x-4">
            <button className="px-8 py-4 rounded-lg bg-gradient-to-r from-amber-200 to-lime-200 text-gray-600 text-lg font-semibold transition-all duration-300 shadow-[2px_2px_4px_#bebebe] hover:shadow-inner hover:bg-none hover:border-2 hover:border-black">
              <Link href="/models"><img
                  src="/chain.svg"
                  alt="Icon"
                  className={`h-8 w-8`}
                /></Link>
            </button>
            <button className="px-8 py-4 rounded-lg bg-gradient-to-r from-lime-200 to-teal-200 text-gray-600 text-lg font-semibold transition-all duration-300 shadow-[2px_2px_4px_#bebebe] hover:shadow-inner hover:bg-none hover:border-2 hover:border-black">
              <Link href="/projects"><img
                  src="/cube2.svg"
                  alt="Icon"
                  className={`h-8 w-8`}
                /></Link>
            </button>
            <button className="px-8 py-4 rounded-lg bg-gradient-to-r from-teal-200 from-30% to-blue-200 text-gray-600 text-lg font-semibold transition-all duration-300 shadow-[2px_2px_4px_#bebebe] hover:shadow-inner hover:bg-none hover:border-2 hover:border-black">
              <Link href="/research"><img
                  src="/cube.svg"
                  alt="Icon"
                  className={`h-8 w-8`}
                /></Link>
            </button>
            <button className="px-8 py-4 rounded-lg bg-gradient-to-r from-blue-200 from-30% to-fuchsia-200 text-gray-600 text-lg font-semibold transition-all duration-300 shadow-[2px_2px_4px_#bebebe] hover:shadow-inner hover:bg-none hover:border-2 hover:border-black">
              <Link href="/code"><img
                  src="/terminal.svg"
                  alt="Icon"
                  className={`h-8 w-8`}
                /></Link>
            </button>
            </div>
            
          </div>
        </section>

        {/* Tags stream */}
        <div className="mt-4 pb-6">
          <AnimatedTags tags={["Implied Volatility Surfaces", "Order Flow Ravines", "Terminal by Citadel", "Jane Street Puzzles", "Bridgewater x Metacalc", "US Fixed Income Yield Plots", "Distributed Systems", "Stochastic Processes", "Time Series Modelling", "Edge Computing"]} />
        </div>

        {/* About Us Section */}
        <section className="py-2">
          <div className="grid md:grid-cols-2 gap-12 items-center bg-five-color-gradient text-gray-600 p-12 mx-0 h-96">
            <div className="space-y-6">
            <div className="flex flex-col items-center">
            <h2 className="text-4xl font-bold text-black py-4">
            &gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt; ABOUT &lt;&lt;&lt;&lt;&lt;&lt;&lt;&lt;
              </h2>
              <div className="p-4 bg-white shadow-[8px_8px_16px_rgba(0,0,0,0.2)] flex flex-col items-center hover:shadow-inner hover:shadow-gray-400 rounded-lg space-y-4">
                <h4 className="text-center">WE LOVE TO LEARN, RESEARCH, EXPIREMENT, BUILD, & SOLVE.
                </h4>
                <div className="flex flex-row space-x-4 align-center justify-center">
                <h2 className="text-center align-center">Sound Like You? <br /> Scan & Join The Panderium</h2>
                <img src="/qr.gif" className="h-20 w-20"/> 
                </div>
                <h4 className="text-center">Subscribe to our free newsletter: <strong>The Street View</strong> to get a summary of our insights + update on anything new we may be working on! 
                </h4> 
              <div className="flex flex-row items-center">
                <form className="flex flex-row space-x-2">
                  <input
                    type="email"
                    placeholder="Enter your email"
                    className="px-4 py-2 rounded-lg shadow-[inset_4px_4px_8px_#bebebe,inset_-4px_-4px_8px_#ffffff] bg-gray-100 text-gray-700 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all duration-300"
                    required
                  />
                  <button
                    className="px-6 py-2 rounded-lg bg-gradient-to-r from-fuchsia-200 to-rose-200 text-gray-600 font-semibold shadow-[2px_2px_4px_#bebebe] hover:shadow-inner hover:bg-none hover:border-2 hover:border-black transition-all duration-300"
                  >
                    Subscribe
                  </button>
                </form>
              </div>
              </div>
            </div>
              
            </div>
            <div className="flex flex-col items-center">
            <h1 className='pt-2 text-2xl text-black text-center'> Explore Our Work Through The <br /> <strong>____Pandera CLI v1.1____</strong></h1>
            <h4 className='pb-4 text-l text-black'> Supported Commands: <strong>&#91; cd | ls | open &#93;</strong> </h4>
            <Terminal />
            </div>
            
          </div>
        </section>
      </main>
    </div>
  );
}
