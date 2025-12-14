import React, { useState } from 'react';
import { BookOpen, Search, Loader2, AlertCircle, Sparkles } from 'lucide-react';
import wordleApi from '../services/api';

/**
 * Composant pour afficher la définition d'un mot via l'API Gemini
 */
function WordDefinition({ language = 'fr' }) {
  const [word, setWord] = useState('');
  const [definition, setDefinition] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async () => {
    if (!word.trim()) {
      setError('Veuillez entrer un mot');
      return;
    }

    setLoading(true);
    setError(null);
    setDefinition(null);

    try {
      const response = await wordleApi.getWordDefinition(word.trim(), language);
      
      if (response.success && response.definition) {
        setDefinition({
          word: response.word,
          text: response.definition,
          language: response.language
        });
      } else {
        setError(response.error || 'Impossible d\'obtenir la définition');
      }
    } catch (err) {
      console.error('Erreur lors de la récupération de la définition:', err);
      setError('Erreur de connexion. Vérifiez que le backend est démarré et que votre clé API Gemini est configurée.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  return (
    <div className="card">
      <div className="flex items-center gap-2 mb-4">
        <BookOpen className="text-purple-600" size={24} />
        <h2 className="text-xl font-bold text-gray-900">
          Définition de Mot
        </h2>
        <Sparkles className="text-purple-400" size={20} />
      </div>

      <p className="text-sm text-gray-600 mb-4">
        Obtenez une définition simple de n'importe quel mot grâce à l'IA Gemini
      </p>

      {/* Barre de recherche */}
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={word}
          onChange={(e) => setWord(e.target.value.toUpperCase())}
          onKeyPress={handleKeyPress}
          placeholder="Entrez un mot..."
          className="flex-1 px-4 py-2 border-2 border-gray-300 rounded-lg focus:border-purple-500 focus:outline-none uppercase font-medium"
          maxLength={15}
          disabled={loading}
        />
        <button
          onClick={handleSearch}
          disabled={loading || !word.trim()}
          className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:bg-gray-300 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="animate-spin" size={20} />
              <span>Recherche...</span>
            </>
          ) : (
            <>
              <Search size={20} />
              <span>Définir</span>
            </>
          )}
        </button>
      </div>

      {/* Erreur */}
      {error && (
        <div className="bg-red-50 border-2 border-red-200 rounded-lg p-4 mb-4">
          <div className="flex items-start gap-3">
            <AlertCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
            <div>
              <p className="text-red-800 font-medium mb-1">Erreur</p>
              <p className="text-red-700 text-sm">{error}</p>
              {error.includes('clé API') && (
                <div className="mt-2 text-xs text-red-600 bg-red-100 p-2 rounded">
                  <p className="font-semibold mb-1">Configuration requise :</p>
                  <ol className="list-decimal list-inside space-y-1">
                    <li>Créez un fichier <code className="bg-red-200 px-1 rounded">.env</code> dans le dossier <code className="bg-red-200 px-1 rounded">wordle-solver/</code></li>
                    <li>Ajoutez : <code className="bg-red-200 px-1 rounded">GEMINI_API_KEY=votre_clé_api</code></li>
                    <li>Obtenez une clé gratuite sur <a href="https://ai.google.dev/" target="_blank" rel="noopener noreferrer" className="underline">ai.google.dev</a></li>
                    <li>Redémarrez le backend</li>
                  </ol>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Définition */}
      {definition && (
        <div className="bg-gradient-to-br from-purple-50 to-blue-50 border-2 border-purple-200 rounded-lg p-5">
          <div className="flex items-center gap-2 mb-3">
            <div className="px-3 py-1 bg-purple-600 text-white rounded-full font-bold text-lg">
              {definition.word}
            </div>
            <span className="text-xs text-gray-500 bg-white px-2 py-1 rounded">
              {definition.language === 'fr' ? '🇫🇷 Français' : '🇬🇧 English'}
            </span>
          </div>
          
          <div className="bg-white rounded-lg p-4 shadow-sm">
            <p className="text-gray-800 leading-relaxed">
              {definition.text}
            </p>
          </div>

          <div className="flex items-center gap-2 mt-3 text-xs text-gray-500">
            <Sparkles size={14} className="text-purple-400" />
            <span>Généré par Gemini AI</span>
          </div>
        </div>
      )}

      {/* Message initial */}
      {!definition && !error && !loading && (
        <div className="text-center py-8 text-gray-400">
          <BookOpen className="mx-auto mb-2" size={48} />
          <p>Entrez un mot pour voir sa définition</p>
        </div>
      )}
    </div>
  );
}

export default WordDefinition;
