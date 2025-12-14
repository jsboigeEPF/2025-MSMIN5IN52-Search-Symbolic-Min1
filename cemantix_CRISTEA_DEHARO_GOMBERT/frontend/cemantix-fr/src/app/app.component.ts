import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from './api.service';


@Component({
  standalone: true,
  imports: [CommonModule, FormsModule],
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent {
  gameId: string | null = null;
  maxAttempts = 6;
  guessText = '';
  history: any[] = [];
  remaining = 0;
  finished = false;
  won = false;
  targetWord: string | null = null;
  message = '';
  topSimilaires: any[] = [];
  aiSolving = false;
  aiSuggesting = false;
  aiSuggestion: string | null = null;
  addingAttempts = false;
  revealingTarget = false;

  constructor(private api: ApiService) {}

  newGame() {
    this.api.startGame(undefined, this.maxAttempts).subscribe(res => {
      this.gameId = res.game_id;
      this.history = [];
      this.remaining = res.max_attempts;
      this.finished = false;
      this.won = false;
      this.targetWord = null;
      this.message = 'Nouvelle partie démarrée. Bonne chance !';
    }, err => {
      this.message = 'Erreur démarrage partie : ' + (err.error?.detail ?? err.message);
    });
  }

  submitGuess() {
    if (!this.gameId) {
      this.message = "D'abord démarrer une partie";
      return;
    }
    const guess = this.guessText.trim();
    if (!guess) {
      this.message = "Entrez un mot.";
      return;
    }
    this.api.guess(this.gameId, guess).subscribe(res => {
      if (res.error) {
        this.message = res.error;
        return;
      }
      // Mapper l'historique avec les informations
      const historyMapped = res.history.map((h: any, index: number) => ({ 
        guess: h.guess, 
        score: h.score, // Le score est déjà en pourcentage (0-100)
        rank: h.rank || res.rank, // Utiliser le rang de l'historique ou celui du dernier guess
        attempt: index + 1
      }));
      
      // Trier par score décroissant
      this.history = historyMapped.sort((a: any, b: any) => b.score - a.score);
      
      this.remaining = res.remaining;
      this.finished = res.finished;
      this.won = res.won;
      this.targetWord = res.target || null;
      this.topSimilaires = res.top_similaires || [];
      
      if (res.finished) {
        this.message = res.won ? `🎉 Bravo ! Vous avez trouvé le mot !` : `😔 Partie terminée`;
        // Rafraîchir l'état pour s'assurer que tout est à jour (notamment pour afficher les boutons d'ajout de tentatives)
        if (!res.won) {
          this.refreshGameState();
        }
      } else {
        this.message = `Score: ${res.score.toFixed(1)}% — Rang: ${res.rank}`;
      }
      this.guessText = '';
    }, err => {
      this.message = 'Erreur lors de la proposition : ' + (err.error?.detail ?? err.message);
    });
  }

  // Calculate percentage from score (assuming score is between 0 and 1)
  getProximityPercentage(score: number): number {
    if (score < 0) return 0;
    if (score > 100) return 100;
    return score
  }

  // Determine gauge color based on score
  getGaugeColor(score: number): string {
    const percentage = this.getProximityPercentage(score);
    if (percentage >= 80) return '#4CAF50'; // Green
    if (percentage >= 60) return '#8BC34A'; // Yellow-green
    if (percentage >= 40) return '#FF9800'; // Orange
    if (percentage >= 20) return '#FF5722'; // Red
    return '#D32F2F'; // Dark red
  }

  // Check if score is very high (for pulse animation)
  isVeryClose(score: number): boolean {
    return this.getProximityPercentage(score) > 90;
  }

  // Get the best score from history
  getBestScore(): number {
    if (this.history.length === 0) return 0;
    return Math.max(...this.history.map((h: any) => h.score));
  }

  addAttempts(additional: number) {
    if (!this.gameId || this.won) return;
    
    this.addingAttempts = true;
    this.api.addAttempts(this.gameId, additional).subscribe({
      next: (res) => {
        this.addingAttempts = false;
        this.maxAttempts = res.max_attempts;
        this.remaining = res.remaining;
        this.finished = false;
        this.message = `✅ ${additional} tentative(s) ajoutée(s) ! Vous pouvez continuer à jouer.`;
        this.refreshGameState();
      },
      error: (err) => {
        this.addingAttempts = false;
        this.message = 'Erreur : ' + (err.error?.detail ?? err.message);
      }
    });
  }

  revealTarget() {
    if (!this.gameId || this.won) return;
    
    if (!confirm('Êtes-vous sûr de vouloir révéler le mot ? La partie sera définitivement terminée.')) {
      return;
    }
    
    this.revealingTarget = true;
    this.api.revealTarget(this.gameId).subscribe({
      next: (res) => {
        this.revealingTarget = false;
        this.targetWord = res.target;
        this.finished = true;
        this.won = false;
        this.message = `😔 Le mot à trouver était : "${res.target}". Partie terminée.`;
        this.refreshGameState();
      },
      error: (err) => {
        this.revealingTarget = false;
        this.message = 'Erreur : ' + (err.error?.detail ?? err.message);
      }
    });
  }

  aiSolve() {
    if (!this.gameId) {
      this.message = "D'abord démarrer une partie";
      return;
    }
    if (this.finished) {
      this.message = "La partie est déjà terminée";
      return;
    }
    
    this.aiSolving = true;
    this.message = '🤖 L\'IA (LLM) résout la partie...';
    
    // Utiliser le streaming pour voir les propositions en temps réel
    this.api.aiSolveStream(this.gameId).subscribe({
      next: (event) => {
        switch (event.type) {
          case 'start':
            this.message = '🤖 ' + event.message;
            break;
          
          case 'thinking':
            this.message = '🤖 ' + event.message;
            break;
          
          case 'guess':
            // Ajouter le guess à l'historique en temps réel
            const guessData = event.data;
            const newGuess = {
              guess: guessData.guess,
              score: guessData.score,
              rank: guessData.rank,
              attempt: guessData.attempt
            };
            
            // Vérifier si ce guess n'est pas déjà dans l'historique
            const exists = this.history.some((h: any) => 
              h.guess === newGuess.guess && h.attempt === newGuess.attempt
            );
            
            if (!exists) {
              this.history.push(newGuess);
              this.history = this.history.sort((a: any, b: any) => b.score - a.score);
            }
            
            // Mettre à jour les essais restants
            this.remaining = Math.max(0, this.maxAttempts - guessData.attempt);
            
            this.message = `🤖 Proposition ${guessData.attempt}: "${guessData.guess}" - Score: ${guessData.score.toFixed(1)}% - Rang: ${guessData.rank}`;
            break;
          
          case 'success':
            this.aiSolving = false;
            this.message = `🎉 ${event.message}`;
            this.finished = true;
            this.won = true;
            this.targetWord = event.target;
            this.remaining = 0;
            // Rafraîchir pour avoir l'état final complet
            this.refreshGameState();
            break;
          
          case 'finished':
            this.aiSolving = false;
            this.message = `🤖 ${event.message}`;
            this.finished = true;
            this.won = false;
            this.targetWord = event.target;
            this.remaining = 0;
            // Rafraîchir pour avoir l'état final complet
            this.refreshGameState();
            break;
          
          case 'error':
            this.aiSolving = false;
            this.message = `❌ Erreur: ${event.message}`;
            break;
        }
      },
      error: (err) => {
        this.aiSolving = false;
        this.message = 'Erreur lors de la résolution IA : ' + (err.message || err);
      },
      complete: () => {
        this.aiSolving = false;
        this.refreshGameState();
      }
    });
  }

  aiSuggest() {
    if (!this.gameId) {
      this.message = "D'abord démarrer une partie";
      return;
    }
    if (this.finished) {
      this.message = "La partie est déjà terminée";
      return;
    }
    
    this.aiSuggesting = true;
    this.aiSuggestion = null;
    this.message = '🤖 L\'IA (LLM) réfléchit...';
    
    this.api.aiSuggest(this.gameId).subscribe(res => {
      this.aiSuggesting = false;
      
      if (res.suggestion) {
        this.aiSuggestion = res.suggestion;
        this.message = `💡 Le LLM suggère: "${res.suggestion}" - Cliquez sur "Utiliser" pour le proposer`;
      } else {
        this.message = res.error || 'Aucune suggestion disponible';
      }
    }, err => {
      this.aiSuggesting = false;
      this.message = 'Erreur lors de la suggestion IA : ' + (err.error?.detail ?? err.message);
    });
  }

  useAISuggestion() {
    if (this.aiSuggestion && this.gameId && !this.finished) {
      // Mettre le mot dans le champ de saisie
      this.guessText = this.aiSuggestion;
      // Soumettre directement le guess
      const guess = this.aiSuggestion.trim();
      if (guess) {
        this.api.guess(this.gameId, guess).subscribe({
          next: (res) => {
            if (res.error) {
              this.message = res.error;
              return;
            }
            // Mapper l'historique avec les informations
            const historyMapped = res.history.map((h: any, index: number) => ({ 
              guess: h.guess, 
              score: h.score,
              rank: h.rank || res.rank,
              attempt: index + 1
            }));
            
            // Trier par score décroissant
            this.history = historyMapped.sort((a: any, b: any) => b.score - a.score);
            
            this.remaining = res.remaining;
            this.finished = res.finished;
            this.won = res.won;
            this.targetWord = res.target || null;
            this.topSimilaires = res.top_similaires || [];
            
            if (res.finished) {
              this.message = res.won ? `🎉 Bravo ! Vous avez trouvé le mot !` : `😔 Partie terminée`;
            } else {
              this.message = `Score: ${res.score.toFixed(1)}% — Rang: ${res.rank}`;
            }
            this.guessText = '';
            // Effacer la suggestion après soumission
            this.aiSuggestion = null;
          },
          error: (err) => {
            this.message = 'Erreur lors de la proposition : ' + (err.error?.detail ?? err.message);
          }
        });
      }
    }
  }

  refreshGameState() {
    if (!this.gameId) return;
    
    // Récupérer l'état actuel de la partie
    this.api.getGameStatus(this.gameId).subscribe(res => {
      const historyMapped = res.history.map((h: any, index: number) => ({ 
        guess: h.guess, 
        score: h.score,
        rank: h.rank,
        attempt: index + 1
      }));
      
      this.history = historyMapped.sort((a: any, b: any) => b.score - a.score);
      this.remaining = res.max_attempts - res.attempts;
      this.finished = res.finished;
      this.won = res.won;
      this.targetWord = res.target || null;
    }, err => {
      console.error('Erreur lors du rafraîchissement:', err);
    });
  }
}