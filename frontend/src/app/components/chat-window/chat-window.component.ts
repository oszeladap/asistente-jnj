import { CommonModule } from '@angular/common';
import {
  AfterViewChecked,
  Component,
  ElementRef,
  Input,
  ViewChild,
} from '@angular/core';
import { ProgressSpinnerModule } from 'primeng/progressspinner';

import { ChatMessage } from '../../models/chat-message.model';

@Component({
  selector: 'app-chat-window',
  standalone: true,
  imports: [CommonModule, ProgressSpinnerModule],
  templateUrl: './chat-window.component.html',
  styleUrl: './chat-window.component.scss',
})
export class ChatWindowComponent implements AfterViewChecked {
  @Input() messages: ChatMessage[] = [];
  @Input() loading = false;

  @ViewChild('scrollContainer') private scrollContainer?: ElementRef<HTMLDivElement>;

  private lastMessageCount = 0;

  ngAfterViewChecked(): void {
    if (this.messages.length !== this.lastMessageCount || this.loading) {
      this.lastMessageCount = this.messages.length;
      this.scrollToBottom();
    }
  }

  private scrollToBottom(): void {
    const el = this.scrollContainer?.nativeElement;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }
}
