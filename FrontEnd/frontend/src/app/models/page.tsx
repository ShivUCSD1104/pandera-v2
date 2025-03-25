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
      constraints: [
        { label: 'Ticker', options: ['AAPL', 'GOOGL', 'MSFT'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year', 'custom'] 
        },
      ],
    },
    {
      title: 'US Fix Income Yield Plot',
      image: '/graph3.png',
      type: 'USFixedIncomeYield',
      constraints: [
        { label: 'Issuer', options: ['US Treasury'] },
        { 
          label: 'Time Period', 
          options: ['1 month', '3 months', '6 months', '1 year', 'custom'] 
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
                className="rounded-2xl p-6 bg-white shadow-[8px_8px_16px_#bebebe] group hover:shadow-inner hover:shadow-gray-300"
                onClick={() => openModal(card)}
              >
                <div className="rounded-lg mb-4"><Image alt={card.title} src={card.image} width={500} height={500}/></div>
                <h3 className="text-xl text-black mb-2 text-center">{card.title}</h3>
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