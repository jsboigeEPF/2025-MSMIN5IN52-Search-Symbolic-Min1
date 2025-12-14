import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, Subject } from 'rxjs';

interface StartResp {
  message: string;
  game_id: string;
  max_attempts: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private apiUrl = 'http://localhost:8000';
  constructor(private http: HttpClient) {}
  startGame(target?: string, max_attempts?: number): Observable<StartResp> {
    return this.http.post<StartResp>(`${this.apiUrl}/start`, { target, max_attempts });
  }
  guess(game_id: string, guess: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/guess`, { game_id, guess });
  }
  getVocab(limit: number = 200): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/vocab?limit=${limit}`);
  }
  aiSolve(game_id: string, useLLM?: boolean, llmModel?: string): Observable<any> {
    const payload: any = { game_id };
    if (useLLM !== undefined) payload.use_llm = useLLM;
    if (llmModel) payload.llm_model = llmModel;
    return this.http.post<any>(`${this.apiUrl}/ai/solve`, payload);
  }

  aiSolveStream(game_id: string, useLLM?: boolean, llmModel?: string): Subject<any> {
    const subject = new Subject<any>();
    const payload: any = { game_id };
    if (useLLM !== undefined) payload.use_llm = useLLM;
    if (llmModel) payload.llm_model = llmModel;

    // Utiliser fetch avec streaming pour Server-Sent Events
    fetch(`${this.apiUrl}/ai/solve`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload)
    }).then(response => {
      if (!response.body) {
        subject.error('No response body');
        return;
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      const readChunk = () => {
        reader.read().then(({ done, value }) => {
          if (done) {
            subject.complete();
            return;
          }

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          buffer = lines.pop() || '';

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              try {
                const data = JSON.parse(line.slice(6));
                subject.next(data);
              } catch (e) {
                console.error('Error parsing SSE data:', e);
              }
            }
          }

          readChunk();
        }).catch(err => {
          subject.error(err);
        });
      };

      readChunk();
    }).catch(err => {
      subject.error(err);
    });

    return subject;
  }
  
  aiSuggest(game_id: string, llmModel?: string): Observable<any> {
    const payload: any = { game_id };
    if (llmModel) payload.llm_model = llmModel;
    return this.http.post<any>(`${this.apiUrl}/ai/suggest`, payload);
  }
  getGameStatus(game_id: string): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/game/${game_id}`);
  }

  addAttempts(game_id: string, additional_attempts: number): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/add-attempts`, { game_id, additional_attempts });
  }

  revealTarget(game_id: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/reveal-target`, { game_id });
  }
}