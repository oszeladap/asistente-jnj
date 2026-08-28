import { Component, inject, signal } from '@angular/core';
import { MessageService } from 'primeng/api';
import { ToastModule } from 'primeng/toast';
import { finalize } from 'rxjs';

import { ChatInputComponent } from './components/chat-input/chat-input.component';
import { ChatWindowComponent } from './components/chat-window/chat-window.component';
import { ChatMessage } from './models/chat-message.model';
import { ChatService } from './services/chat.service';
import { UploadService } from './services/upload.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [ChatWindowComponent, ChatInputComponent, ToastModule],
  templateUrl: './app.html',
  styleUrl: './app.scss',
})
export class App {
  private readonly chatService = inject(ChatService);
  private readonly uploadService = inject(UploadService);
  private readonly messageService = inject(MessageService);

  readonly messages = signal<ChatMessage[]>([]);
  readonly loading = signal(false);
  readonly uploading = signal(false);

  onSend(question: string): void {
    this.messages.update((msgs) => [
      ...msgs,
      { role: 'user', text: question, timestamp: new Date() },
    ]);
    this.loading.set(true);

    this.chatService
      .askQuestion(question)
      .pipe(finalize(() => this.loading.set(false)))
      .subscribe({
        next: (response) => {
          this.messages.update((msgs) => [
            ...msgs,
            {
              role: 'assistant',
              text: response.answer,
              sources: response.sources,
              timestamp: new Date(),
            },
          ]);
        },
        error: (err) => {
          const detail =
            typeof err?.error?.detail === 'string'
              ? err.error.detail
              : 'No se pudo obtener una respuesta. Intenta de nuevo en unos momentos.';
          this.messages.update((msgs) => [
            ...msgs,
            { role: 'assistant', text: detail, isError: true, timestamp: new Date() },
          ]);
        },
      });
  }

  onFilesSelected(files: File[]): void {
    this.uploading.set(true);
    this.uploadService
      .uploadPdfs(files)
      .pipe(finalize(() => this.uploading.set(false)))
      .subscribe({
        next: (response) => {
          const ok = response.files.filter((f) => f.status === 'ok');
          const failed = response.files.filter((f) => f.status === 'error');

          if (ok.length > 0) {
            this.messageService.add({
              severity: 'success',
              summary: 'Documentos indexados',
              detail: `${ok.length} archivo(s), ${response.total_chunks_indexed} fragmentos indexados.`,
              life: 5000,
            });
          }
          failed.forEach((f) => {
            this.messageService.add({
              severity: 'warn',
              summary: `No se pudo procesar ${f.filename}`,
              detail: f.error ?? 'Error desconocido',
              life: 7000,
            });
          });
        },
        error: () => {
          // El error.interceptor ya muestra un toast con el detalle.
        },
      });
  }
}
