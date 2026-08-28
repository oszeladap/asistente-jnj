import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { MessageService } from 'primeng/api';
import { catchError, throwError } from 'rxjs';

function extractMessage(err: HttpErrorResponse): string {
  if (err.status === 0) {
    return 'No se pudo conectar con el servidor. Verifica tu conexión e inténtalo de nuevo.';
  }
  const detail = err.error?.detail;
  if (typeof detail === 'string') {
    return detail;
  }
  if (Array.isArray(detail) && detail.length > 0 && detail[0]?.msg) {
    return detail.map((d: { msg: string }) => d.msg).join(', ');
  }
  return `Error del servidor (${err.status}). Inténtalo nuevamente.`;
}

export const errorInterceptor: HttpInterceptorFn = (req, next) => {
  const messageService = inject(MessageService);

  return next(req).pipe(
    catchError((err: HttpErrorResponse) => {
      messageService.add({
        severity: 'error',
        summary: 'Ocurrió un error',
        detail: extractMessage(err),
        life: 6000,
      });
      return throwError(() => err);
    })
  );
};
