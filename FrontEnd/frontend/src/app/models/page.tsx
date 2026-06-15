'use client';

import { useState } from 'react';
import Modal from '../components/modal';
import Image from 'next/image';

interface Constraint {
  label: string;
  options: string[];
}

interface CardData {
  title: string;
  image: string;
  type: string;
  description?: string;
  tags?: string[];
  constraints: Constraint[];
}

export default function Models() {
  const [isModalOpen, setModalOpen] = useState(false);
  const [selectedCardData, setSelectedCardData] = useState<CardData | null>(null);
  
  const cards: CardData[] = [
    {
      title: 'Implied Volatility Surface',
      image: '/graph1.png',
      type: 'IVMap',
      description:
        'Black–Scholes implied volatility across strike and expiry, rendered as a 3D surface — read the volatility smile and term structure at a glance.',
      tags: ['Black–Scholes', 'Options', '3D surface'],
      constraints: [
        { label: 'Ticker', options: ['AAPL', 'GOOGL', 'MSFT'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year', 'custom'] 
        },
      ],
    },
    {
      title: 'Order Book Ravine',
      image: '/graph2.png',
      type: 'OrderFlowCanyon',
      description:
        'Live limit-order-book depth (databento MBP-10) sculpted into a 3D liquidity canyon across price levels and time.',
      tags: ['Market microstructure', 'Live data', 'Order book'],
      constraints: [
        { label: 'Ticker', options: ['AAPL', 'GOOGL', 'MSFT'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year', 'custom'] 
        },
      ],
    },
    {
      title: 'US Fixed Income Yield Surface',
      image: '/graph3.png',
      type: 'USFixedIncomeYield',
      description:
        'The US Treasury term structure over time — watch the yield curve steepen, flatten, and invert across maturities.',
      tags: ['Rates', 'Term structure', 'Treasuries'],
      constraints: [
        { label: 'Issuer', options: ['US Treasury'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year', 'custom'] 
        },
      ],
    },
    {
      title: 'Options Greeks Landscape',
      image: '/graph4.png',
      type: 'GreeksLandscape',
      description:
        'First-order option Greeks (Delta, Gamma, Theta, Vega) as a 3D risk surface across strike and expiry — see where exposure concentrates.',
      tags: ['Greeks', 'Risk', 'Options'],
      constraints: [
        { label: 'Ticker', options: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA'] },
        { label: 'Greeks View', options: ['Delta', 'Gamma', 'Theta', 'Vega', 'All'] },
        { label: 'Option Type', options: ['Both', 'Call', 'Put'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year'] 
        },
      ],
    },
  ];

  const openModal = (cardData: CardData) => {
    setSelectedCardData(cardData);
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setSelectedCardData(null);
  };

  return (
    <div>
      <main className="min-h-screen bg-[url(/paper.jpg)] p-8">
        <section className="max-w-6xl mx-auto py-20">
          <div className="grid md:grid-cols-3 gap-8">
            {cards.map((card, index) => (
              <div
                key={index}
                className="rounded-2xl p-6 bg-white shadow-[8px_8px_16px_#bebebe] group hover:shadow-inner hover:shadow-gray-300 cursor-pointer transition-shadow"
                onClick={() => openModal(card)}
              >
                <div className="rounded-lg mb-4"><Image alt={card.title} src={card.image} width={500} height={500}/></div>
                <h3 className="text-xl text-black mb-2 text-center font-semibold">{card.title}</h3>
                {card.description && (
                  <p className="text-sm text-gray-600 text-center mb-3">{card.description}</p>
                )}
                {card.tags && (
                  <div className="flex flex-wrap justify-center gap-2">
                    {card.tags.map((tag) => (
                      <span
                        key={tag}
                        className="text-xs px-2 py-1 rounded-full bg-gray-100 text-gray-700 border border-gray-200"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      </main>
      {selectedCardData && (
        <Modal isOpen={isModalOpen} onClose={closeModal} cardData={selectedCardData} />
      )}
    </div>
  );
}