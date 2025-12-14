import React from 'react';
import { Delete } from 'lucide-react';

const Keyboard = ({ onKeyPress, letterStates = {} }) => {
  const rows = [
    ['Q', 'W', 'E', 'R', 'T', 'Y', 'U', 'I', 'O', 'P'],
    ['A', 'S', 'D', 'F', 'G', 'H', 'J', 'K', 'L'],
    ['ENTER', 'Z', 'X', 'C', 'V', 'B', 'N', 'M', 'BACKSPACE'],
  ];

  const getKeyClass = (key) => {
    const baseClass = 'keyboard-key';
    const state = letterStates[key];
    
    if (!state) return `${baseClass} keyboard-key-default`;
    
    switch (state) {
      case 'CORRECT':
        return `${baseClass} keyboard-key-correct`;
      case 'PRESENT':
        return `${baseClass} keyboard-key-present`;
      case 'ABSENT':
        return `${baseClass} keyboard-key-absent`;
      default:
        return `${baseClass} keyboard-key-default`;
    }
  };

  const handleKeyClick = (key) => {
    onKeyPress(key);
  };

  const renderKey = (key) => {
    if (key === 'BACKSPACE') {
      return (
        <button
          key={key}
          onClick={() => handleKeyClick(key)}
          className={`${getKeyClass(key)} flex items-center justify-center px-2`}
        >
          <Delete size={20} />
        </button>
      );
    }

    return (
      <button
        key={key}
        onClick={() => handleKeyClick(key)}
        className={getKeyClass(key)}
        style={key === 'ENTER' ? { fontSize: '12px' } : {}}
      >
        {key}
      </button>
    );
  };

  return (
    <div className="flex flex-col gap-2 max-w-lg mx-auto">
      {rows.map((row, rowIndex) => (
        <div key={rowIndex} className="flex gap-1 justify-center">
          {row.map(renderKey)}
        </div>
      ))}
    </div>
  );
};

export default Keyboard;
