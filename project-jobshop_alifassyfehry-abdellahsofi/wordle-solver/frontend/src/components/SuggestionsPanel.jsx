import React from 'react';
import { Lightbulb, TrendingUp, Filter } from 'lucide-react';

const SuggestionsPanel = ({ 
  suggestedWord, 
  possibleWords, 
  possibleWordsCount, 
  explanation,
  strategy,
  onSelectWord 
}) => {
  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <Lightbulb className="text-yellow-500" size={24} />
        <h3 className="text-lg font-bold">Suggestions IA</h3>
      </div>

      {suggestedWord && (
        <div className="mb-4 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-gray-600">Meilleur choix :</span>
            <span className="text-xs px-2 py-1 bg-blue-100 rounded-full text-blue-800">
              {strategy}
            </span>
          </div>
          <div 
            className="text-3xl font-bold text-blue-600 cursor-pointer hover:text-blue-700 transition-colors"
            onClick={() => onSelectWord && onSelectWord(suggestedWord)}
            title="Cliquer pour utiliser ce mot"
          >
            {suggestedWord}
          </div>
          {explanation && (
            <p className="text-sm text-gray-600 mt-2">{explanation}</p>
          )}
        </div>
      )}

      <div className="mb-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter size={16} className="text-gray-500" />
          <span className="text-sm font-medium text-gray-700">
            Mots possibles : {possibleWordsCount}
          </span>
        </div>
      </div>

      {possibleWords && possibleWords.length > 0 && (
        <div className="space-y-2">
          <div className="flex flex-wrap gap-2 max-h-64 overflow-y-auto p-2 bg-gray-50 rounded">
            {possibleWords.slice(0, 50).map((word, index) => (
              <span
                key={index}
                onClick={() => onSelectWord && onSelectWord(word)}
                className="px-3 py-1 bg-white border border-gray-300 rounded text-sm font-medium hover:bg-blue-50 hover:border-blue-300 cursor-pointer transition-colors"
              >
                {word}
              </span>
            ))}
            {possibleWordsCount > 50 && (
              <span className="px-3 py-1 text-gray-500 text-sm italic">
                +{possibleWordsCount - 50} autres...
              </span>
            )}
          </div>
        </div>
      )}

      {possibleWordsCount === 0 && (
        <div className="text-center py-4 text-gray-500">
          Aucun mot possible trouvé
        </div>
      )}
    </div>
  );
};

export default SuggestionsPanel;
