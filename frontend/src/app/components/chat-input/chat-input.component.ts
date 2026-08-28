import { CommonModule } from '@angular/common';
import { Component, EventEmitter, Input, Output } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { ButtonModule } from 'primeng/button';
import { FileUploadHandlerEvent, FileUploadModule } from 'primeng/fileupload';
import { TextareaModule } from 'primeng/textarea';
import { TooltipModule } from 'primeng/tooltip';

@Component({
  selector: 'app-chat-input',
  standalone: true,
  imports: [CommonModule, FormsModule, ButtonModule, TextareaModule, FileUploadModule, TooltipModule],
  templateUrl: './chat-input.component.html',
  styleUrl: './chat-input.component.scss',
})
export class ChatInputComponent {
  @Input() disabled = false;
  @Input() uploading = false;

  @Output() send = new EventEmitter<string>();
  @Output() filesSelected = new EventEmitter<File[]>();

  question = '';

  get canSend(): boolean {
    return !this.disabled && this.question.trim().length > 0;
  }

  onSend(): void {
    if (!this.canSend) {
      return;
    }
    this.send.emit(this.question.trim());
    this.question = '';
  }

  onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.onSend();
    }
  }

  onUploadHandler(event: FileUploadHandlerEvent): void {
    const files = (event.files ?? []) as File[];
    if (files.length > 0) {
      this.filesSelected.emit(files);
    }
  }
}
