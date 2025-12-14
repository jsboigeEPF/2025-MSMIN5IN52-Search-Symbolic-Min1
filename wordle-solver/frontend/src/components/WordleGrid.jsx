import React from 'react';

const WordleGrid = ({ attempts, currentGuess, maxAttempts = 6 }) => {
  const getTileClass = (feedback) => {
    if (!feedback) return 'wordle-tile wordle-tile-empty';
    
    switch (feedback) {
      case 'CORRECT':
        return 'wordle-tile wordle-tile-correct';
      case 'PRESENT':
        return 'wordle-tile wordle-tile-present';
      case 'ABSENT':
        return 'wordle-tile wordle-tile-absent';
      default:
        return 'wordle-tile wordle-tile-empty';
    }
  };

  const renderRow = (rowData, rowIndex) => {
    const tiles = [];
    
    for (let i = 0; i < 5; i++) {
      let letter = '';
      let feedback = null;
      
      if (rowData) {
        // Tentative complétée
        letter = rowData.guess[i] || '';
        feedback = rowData.feedbacks[i];
      } else if (rowIndex === attempts.length && currentGuess) {
        // Ligne en cours de saisie
        letter = currentGuess[i] || '';
      }
      
      tiles.push(
        <div key={i} className={getTileClass(feedback)}>
          {letter}
        </div>
      );
    }
    
    return tiles;
  };

  const rows = [];
  
  // Afficher les tentatives complétées
  for (let i = 0; i < maxAttempts; i++) {
    const rowData = attempts[i] || null;
    
    rows.push(
      <div key={i} className="flex gap-1 justify-center">
        {renderRow(rowData, i)}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-1 mb-6">
      {rows}
    </div>
  );
};

export default WordleGrid;
