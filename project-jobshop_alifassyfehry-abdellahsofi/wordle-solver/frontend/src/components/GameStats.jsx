import React from 'react';
import { Target, TrendingUp, CheckCircle, XCircle } from 'lucide-react';

const GameStats = ({ 
  attemptsCount, 
  maxAttempts, 
  possibleWordsCount, 
  isWon, 
  isOver 
}) => {
  return (
    <div className="card">
      <h3 className="text-lg font-bold mb-4">Statistiques</h3>
      
      <div className="space-y-3">
        {/* Tentatives */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <Target size={18} className="text-blue-500" />
            <span className="font-medium">Tentatives</span>
          </div>
          <span className="text-lg font-bold">
            {attemptsCount} / {maxAttempts}
          </span>
        </div>

        {/* Mots possibles */}
        <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <div className="flex items-center gap-2">
            <TrendingUp size={18} className="text-purple-500" />
            <span className="font-medium">Mots restants</span>
          </div>
          <span className="text-lg font-bold">
            {possibleWordsCount || '?'}
          </span>
        </div>

        {/* Statut de la partie */}
        {isOver && (
          <div className={`flex items-center justify-center gap-2 p-3 rounded-lg ${
            isWon ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
          }`}>
            {isWon ? (
              <>
                <CheckCircle size={20} />
                <span className="font-bold">Victoire !</span>
              </>
            ) : (
              <>
                <XCircle size={20} />
                <span className="font-bold">Défaite</span>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default GameStats;
