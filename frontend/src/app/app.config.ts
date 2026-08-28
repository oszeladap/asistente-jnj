import { provideHttpClient, withInterceptors } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideAnimationsAsync } from '@angular/platform-browser/animations/async';
import { MessageService } from 'primeng/api';
import { providePrimeNG } from 'primeng/config';
import { definePreset } from '@primeuix/themes';
import Aura from '@primeuix/themes/aura';

import { errorInterceptor } from './interceptors/error.interceptor';

// Rojo oficial de la bandera del Perú como color primario del tema.
const PeruPreset = definePreset(Aura, {
  semantic: {
    primary: {
      50: '#fdf3f4',
      100: '#f6c6ca',
      200: '#ef98a0',
      300: '#e76b77',
      400: '#e03d4d',
      500: '#d91023',
      600: '#b80e1e',
      700: '#980b19',
      800: '#770913',
      900: '#57060e',
      950: '#360409',
    },
  },
});

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideAnimationsAsync(),
    provideHttpClient(withInterceptors([errorInterceptor])),
    providePrimeNG({
      theme: {
        preset: PeruPreset,
        options: {
          darkModeSelector: '.app-dark',
        },
      },
    }),
    MessageService,
  ],
};
