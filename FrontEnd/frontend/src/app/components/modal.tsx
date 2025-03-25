'use client';

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import dynamic from 'next/dynamic';
import Slider from '@mui/material/Slider';
import { styled } from '@mui/material/styles';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

interface Constraint {
  label: string;
  options: string[];
}

interface CardData {
  title: string;
  type: string;
  constraints: Constraint[];
}

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  cardData: CardData;
}

interface PlotData {
  data: Plotly.Data[];
  layout: Partial<Plotly.Layout>;
}

const CustomSlider = styled(Slider)({
  color: '#3B82F6',
  height: 4,
  '& .MuiSlider-thumb': {
    width: 20,
    height: 20,
    backgroundColor: '#fff',
    border: '2px solid currentColor',
  },
  '& .MuiSlider-valueLabel': {
    display: 'none',
  },
});

const getDateRange = (graphType: string) => {
  const currentDate = new Date();
  const startDate = new Date(currentDate);
  const endDate = new Date(currentDate);

  switch (graphType) {
    case 'OrderFlowCanyon':
      startDate.setFullYear(currentDate.getFullYear() - 3);
      endDate.setDate(currentDate.getDate() - 2);
      break;
    case 'IVMap':
      startDate.setDate(currentDate.getDate() + 1);
      endDate.setFullYear(currentDate.getFullYear() + 2);
      break;
    case 'USFixedIncomeYield':
      startDate.setFullYear(currentDate.getFullYear() - 5);
      endDate.setDate(currentDate.getDate() - 1);
      break;
    default:
      startDate.setDate(currentDate.getDate() + 1);
      endDate.setFullYear(currentDate.getFullYear() + 2);
      break;
  }

  return { startDate, endDate };
};

const Modal = ({ isOpen, onClose, cardData }: ModalProps) => {
  const [selections, setSelections] = useState<{ [key: string]: string }>({});
  const [plotData, setPlotData] = useState<PlotData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  // State for the animated dots
  const [dotCount, setDotCount] = useState(0);

  useEffect(() => {
    const { startDate, endDate } = getDateRange(cardData.type);
    setSelections(prev => ({
      ...prev,
      'Start Date': prev['Start Date'] || startDate.toISOString().split('T')[0],
      'End Date': prev['End Date'] || endDate.toISOString().split('T')[0],
    }));
  }, [cardData.type]);

  // Effect to update the dots while loading
  useEffect(() => {
    let interval: NodeJS.Timeout | null = null;
    if (loading) {
      interval = setInterval(() => {
        setDotCount(prev => (prev + 1) % 4); // cycles 0, 1, 2, 3
      }, 500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [loading]);

  const handleSelectionChange = (label: string, value: string) => {
    setSelections(prev => ({ ...prev, [label]: value }));
  };

  const computeGraph = async () => {
    setLoading(true);
    setError('');
    try {
      const parameters: Record<string, string> = {};
      cardData.constraints.forEach((constraint) => {
        if (constraint.label === 'Time Period') {
          const { startDate, endDate } = getDateRange(cardData.type);
          parameters['Start Date'] = selections['Start Date'] || startDate.toISOString().split('T')[0];
          parameters['End Date'] = selections['End Date'] || endDate.toISOString().split('T')[0];
        } else {
          parameters[constraint.label] = selections[constraint.label] || constraint.options[0];
        }
      });

      const res = await axios.post('https://api.pandera.net/api/compute', { 
        parameters,
        graphType: cardData.type
      });

      if (res.data.plotly_json) {
        try {
          const parsed = JSON.parse(res.data.plotly_json);
          setPlotData(parsed);
        } catch (e) {
          console.error('JSON parse error:', e);
          setError('Error in retrieving the data, Finance API might be down');
          setPlotData(null);
        }
      }
      setLoading(false);
    } catch (err) {
      console.error(err);
      setPlotData(null);
      setError('Error in retrieving the data, Finance API might be down');
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  const { startDate: defaultStart, endDate: defaultEnd } = getDateRange(cardData.type);
  const startDateStr = selections['Start Date'] || defaultStart.toISOString().split('T')[0];
  const endDateStr = selections['End Date'] || defaultEnd.toISOString().split('T')[0];

  const minTimestamp = defaultStart.getTime();
  const maxTimestamp = defaultEnd.getTime();
  const startDay = Math.floor((new Date(startDateStr).getTime() - minTimestamp) / 86400000);
  const endDay = Math.floor((new Date(endDateStr).getTime() - minTimestamp) / 86400000);
  const totalDays = Math.floor((maxTimestamp - minTimestamp) / 86400000);

  return (
    <div className="fixed inset-0 bg-gray-500 bg-opacity-50 flex justify-center items-center z-50" onClick={onClose}>
      <div className="bg-white rounded-lg shadow-8px_-8px_16px_rgba(255,255,255,0.7)] max-w-6xl w-full p-6 h-3/4" onClick={(e) => e.stopPropagation()}>
        <div className="flex h-full items-center">
          <div className="flex flex-col items-center w-1/3">
            <h2 className="text-2xl font-bold text-gray-800 mb-4">{cardData.title}</h2>
            <div className="w-full p-4 rounded-lg shadow-lg hover:shadow-inner hover:shadow-gray-300">
              {cardData.constraints.map((constraint: Constraint, index: number) => (
                <div key={index} className="mb-4 w-full text-center">
                  <label className="block text-gray-600 mb-1">{constraint.label}</label>
                  {constraint.label === 'Time Period' ? (
                    <div className="mt-4">
                      <CustomSlider
                        value={[startDay, endDay]}
                        onChange={(_, values, activeThumb) => {
                          const newValues = values as number[];
                          if (activeThumb === 0) {
                            const newStartDate = new Date(minTimestamp + newValues[0] * 86400000);
                            setSelections(prev => ({
                              ...prev,
                              'Start Date': newStartDate.toISOString().split('T')[0],
                            }));
                          } else if (activeThumb === 1) {
                            const newEndDate = new Date(minTimestamp + newValues[1] * 86400000);
                            setSelections(prev => ({
                              ...prev,
                              'End Date': newEndDate.toISOString().split('T')[0],
                            }));
                          }
                        }}
                        min={0}
                        max={totalDays}
                        valueLabelDisplay="off"
                        disableSwap
                      />
                      <div className="flex justify-between text-sm text-gray-600 mt-2">
                        <span>{startDateStr}</span>
                        <span>{endDateStr}</span>
                      </div>
                    </div>
                  ) : (
                    <select
                      className="w-full bg-white text-gray-600 p-2 rounded shadow-md hover:shadow-inner hover:shadow-gray-200"
                      value={selections[constraint.label] || constraint.options[0]}
                      onChange={(e) => handleSelectionChange(constraint.label, e.target.value)}
                    >
                      {constraint.options.map((option: string, idx: number) => (
                        <option key={idx} value={option}>{option}</option>
                      ))}
                    </select>
                  )}
                </div>
              ))}
            </div>
            <button onClick={computeGraph} className="mt-4 px-4 py-2 bg-blue-500 text-white rounded shadow hover:bg-blue-600">
              Compute
            </button>
          </div>
          <div className="w-2/3 p-4 h-full">
            <div className="bg-fuchsia-100 rounded-lg h-full flex justify-center items-center overflow-auto">
              {loading ? (
                <span style={{ color: 'black', fontWeight: 'bold', fontSize: '1.2rem' }}>
                  Loading{'.'.repeat(dotCount)}
                </span>
              ) : error ? (
                <span className="text-red-500">{error}</span>
              ) : plotData ? (
                <Plot
                  data={plotData.data}
                  layout={plotData.layout}
                  config={{ responsive: true }}
                  style={{ width: '100%', height: '100%' }}
                />
              ) : (
                <span className="text-emerald-500">Graph Visualization Here</span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Modal;
