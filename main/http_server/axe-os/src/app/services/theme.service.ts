import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { environment } from '../../environments/environment';
import { BehaviorSubject, Observable, of } from 'rxjs';
import { catchError, tap } from 'rxjs/operators';

export interface ThemeSettings {
  colorScheme: string;
  accentColors?: {
    [key: string]: string;
  };
}

@Injectable({
  providedIn: 'root'
})
export class ThemeService {
  private readonly mockSettings: ThemeSettings = {
    colorScheme: 'dark',
    accentColors: {
      '--primary-color': '#00ff95',
      '--primary-color-text': '#04100b',
      '--highlight-bg': '#00ff95',
      '--highlight-text-color': '#04100b',
      '--focus-ring': '0 0 0 0.2rem rgba(0,255,149,0.22)',
      // PrimeNG Slider
      '--slider-bg': '#dee2e6',
      '--slider-range-bg': '#00ff95',
      '--slider-handle-bg': '#00ff95',
      // Progress Bar
      '--progressbar-bg': '#dee2e6',
      '--progressbar-value-bg': '#00ff95',
      // PrimeNG Checkbox
      '--checkbox-border': '#00ff95',
      '--checkbox-bg': '#00ff95',
      '--checkbox-hover-bg': '#00d982',
      // PrimeNG Button
      '--button-bg': '#00ff95',
      '--button-hover-bg': '#00d982',
      '--button-focus-shadow': '0 0 0 2px #04100b, 0 0 0 4px #00ff95',
      // Toggle button
      '--togglebutton-bg': '#00ff95',
      '--togglebutton-border': '1px solid #00ff95',
      '--togglebutton-hover-bg': '#00d982',
      '--togglebutton-hover-border': '1px solid #00d982',
      '--togglebutton-text-color': '#04100b'
    }
  };

  private themeSettingsSubject = new BehaviorSubject<ThemeSettings>(this.mockSettings);
  private themeSettings$ = this.themeSettingsSubject.asObservable();

  constructor(private http: HttpClient) {
    if (environment.production) {
      this.http.get<ThemeSettings>('/api/theme').pipe(
        catchError(() => of(this.mockSettings)),
        tap(settings => this.themeSettingsSubject.next(settings))
      ).subscribe();
    }
  }

  getThemeSettings(): Observable<ThemeSettings> {
    return this.themeSettings$;
  }

  saveThemeSettings(settings: ThemeSettings): Observable<void> {
    if (environment.production) {
      return this.http.post<void>('/api/theme', settings).pipe(
        tap(() => this.themeSettingsSubject.next(settings))
      );
    } else {
      this.themeSettingsSubject.next(settings);
      return of(void 0);
    }
  }
}
