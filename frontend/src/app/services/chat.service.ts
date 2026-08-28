import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { environment } from '../../environments/environment';
import { ChatResponse } from '../models/chat-message.model';

@Injectable({ providedIn: 'root' })
export class ChatService {
  private readonly http = inject(HttpClient);

  askQuestion(question: string): Observable<ChatResponse> {
    return this.http.post<ChatResponse>(`${environment.apiUrl}/api/chat`, { question });
  }
}
