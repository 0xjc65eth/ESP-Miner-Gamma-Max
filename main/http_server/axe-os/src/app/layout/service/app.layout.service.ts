import { Injectable, effect, signal } from '@angular/core';
import { BehaviorSubject, Subject } from 'rxjs';
import { ThemeService } from '../../services/theme.service';
import { LocalStorageService } from '../../local-storage.service';

const STATIC_MENU_DESKTOP_INACTIVE = 'STATIC_MENU_DESKTOP_INACTIVE'

export interface AppConfig {
    inputStyle: string;
    colorScheme: string;
    ripple: boolean;
    menuMode: string;
    scale: number;
}

interface LayoutState {
    staticMenuDesktopInactive: boolean;
    overlayMenuActive: boolean;
    profileSidebarVisible: boolean;
    configSidebarVisible: boolean;
    staticMenuMobileActive: boolean;
    menuHoverActive: boolean;
}

@Injectable({
    providedIn: 'root',
})
export class LayoutService {
    private darkTheme = {
        '--surface-a': '#0B1219',  // Darker navy
        '--surface-b': '#070D17',  // Very dark navy (from image)
        '--surface-c': 'rgba(255,255,255,0.03)',
        '--surface-d': '#1A2632',  // Slightly lighter navy
        '--surface-e': '#0B1219',
        '--surface-f': '#0B1219',
        '--surface-ground': '#070D17',
        '--surface-section': '#070D17',
        '--surface-card': '#0B1219',
        '--surface-overlay': '#0B1219',
        '--surface-border': '#1A2632',
        '--surface-hover': 'rgba(255,255,255,0.03)',
        '--text-color': 'rgba(255, 255, 255, 0.87)',
        '--text-color-secondary': 'rgba(255, 255, 255, 0.6)',
        '--maskbg': 'rgba(0,0,0,0.4)'
    };

    private lightTheme = {
        '--surface-a': '#1a2632',  // Lighter navy for main background
        '--surface-b': '#243447',  // Medium navy for secondary background
        '--surface-c': 'rgba(255,255,255,0.03)',
        '--surface-d': '#2f4562',  // Light navy for borders
        '--surface-e': '#1a2632',
        '--surface-f': '#1a2632',
        '--surface-ground': '#243447',
        '--surface-section': '#1a2632',
        '--surface-card': '#1a2632',
        '--surface-overlay': '#1a2632',
        '--surface-border': '#2f4562',
        '--surface-hover': 'rgba(255,255,255,0.03)',
        '--text-color': 'rgba(255, 255, 255, 0.9)',  // Slightly brighter text
        '--text-color-secondary': 'rgba(255, 255, 255, 0.7)',  // Brighter secondary text
        '--maskbg': 'rgba(0,0,0,0.2)'
    };

    _config: AppConfig = {
        ripple: false,
        inputStyle: 'outlined',
        menuMode: 'static',
        colorScheme: 'dark',
        scale: 14,
    };

    config = signal<AppConfig>(this._config);

    state: LayoutState = {
        staticMenuDesktopInactive: false,
        overlayMenuActive: false,
        profileSidebarVisible: false,
        configSidebarVisible: false,
        staticMenuMobileActive: false,
        menuHoverActive: false,
    };

    isWideView = signal<boolean>(this.localStorageService.getBool('DASHBOARD_WIDE_VIEW'));

    private overlayOpen = new Subject<any>();
    overlayOpen$ = this.overlayOpen.asObservable();

    private staticMenuDesktopInactive$ = new BehaviorSubject<boolean>(this.state.staticMenuDesktopInactive);

    constructor(
      private themeService: ThemeService,
      private localStorageService: LocalStorageService
    ) {
        // Load saved theme settings from NVS
        this.themeService.getThemeSettings().subscribe(
            settings => {
                if (settings) {
                    this._config = {
                        ...this._config,
                        colorScheme: settings.colorScheme,
                    };
                    // Apply accent colors if they exist
                    if (settings.accentColors) {
                        Object.entries(settings.accentColors).forEach(([key, value]) => {
                            document.documentElement.style.setProperty(key, value);
                        });
                    }
                } else {
                    // Save default Cypher dark theme if no settings exist
                    this.themeService.saveThemeSettings({
                        colorScheme: 'dark',
                        accentColors: {
                            '--primary-color': '#00ff95',
                            '--primary-color-text': '#04100b',
                            '--highlight-bg': '#00ff95',
                            '--highlight-text-color': '#04100b',
                            '--focus-ring': '0 0 0 0.2rem rgba(0,255,149,0.22)',
                            '--slider-bg': '#dee2e6',
                            '--slider-range-bg': '#00ff95',
                            '--slider-handle-bg': '#00ff95',
                            '--progressbar-bg': '#dee2e6',
                            '--progressbar-value-bg': '#00ff95',
                            '--checkbox-border': '#00ff95',
                            '--checkbox-bg': '#00ff95',
                            '--checkbox-hover-bg': '#00d982',
                            '--button-bg': '#00ff95',
                            '--button-hover-bg': '#00d982',
                            '--button-focus-shadow': '0 0 0 2px #04100b, 0 0 0 4px #00ff95',
                            '--togglebutton-bg': '#00ff95',
                            '--togglebutton-border': '1px solid #00ff95',
                            '--togglebutton-hover-bg': '#00d982',
                            '--togglebutton-hover-border': '1px solid #00d982',
                            '--togglebutton-text-color': '#04100b'
                        }
                    }).subscribe();
                }
                // Update signal with config
                this.config.set(this._config);
                // Apply initial theme
                this.changeTheme();
            },
            error => {
                console.error('Error loading theme settings:', error);
                // Use default theme on error
                this.config.set(this._config);
                this.changeTheme();
            }
        );

        effect(() => {
            const config = this.config();
            this.changeTheme();
            this.changeScale(config.scale);
            this.handleStaticMenuDesktopInactivity();
        });
    }

    onMenuToggle() {
        if (this.isOverlay()) {
            this.state.overlayMenuActive = !this.state.overlayMenuActive;
            if (this.state.overlayMenuActive) {
                this.overlayOpen.next(null);
            }
        }

        if (this.isDesktop()) {
            this.state.staticMenuDesktopInactive =
                !this.state.staticMenuDesktopInactive;

            this.localStorageService.setBool(STATIC_MENU_DESKTOP_INACTIVE, this.state.staticMenuDesktopInactive);
            this.staticMenuDesktopInactive$.next(this.state.staticMenuDesktopInactive);
        } else {
            this.state.staticMenuMobileActive =
                !this.state.staticMenuMobileActive;

            if (this.state.staticMenuMobileActive) {
                this.overlayOpen.next(null);
            }
        }
    }

    showProfileSidebar() {
        this.state.profileSidebarVisible = !this.state.profileSidebarVisible;
        if (this.state.profileSidebarVisible) {
            this.overlayOpen.next(null);
        }
    }

    showConfigSidebar() {
        this.state.configSidebarVisible = true;
    }

    isOverlay() {
        return this.config().menuMode === 'overlay';
    }

    isDesktop() {
        return window.innerWidth > 991;
    }

    isMobile() {
        return !this.isDesktop();
    }

    changeTheme() {
        const config = this.config();

        // Apply light/dark theme variables
        const themeVars = config.colorScheme === 'light' ? this.lightTheme : this.darkTheme;
        Object.entries(themeVars).forEach(([key, value]) => {
            document.documentElement.style.setProperty(key, value);
        });

        // Load theme settings from NVS
        this.themeService.getThemeSettings().subscribe(
            settings => {
                if (settings && settings.accentColors) {
                    Object.entries(settings.accentColors).forEach(([key, value]) => {
                        document.documentElement.style.setProperty(key, value);
                    });
                }
            },
            error => console.error('Error loading accent colors:', error)
        );
    }

    changeScale(value: number) {
        document.documentElement.style.fontSize = `${value}px`;
    }

    handleStaticMenuDesktopInactivity() {
        if (!this.isDesktop()) {
            return;
        }

        this.state.staticMenuDesktopInactive = this.localStorageService.getBool(STATIC_MENU_DESKTOP_INACTIVE);
        this.staticMenuDesktopInactive$.next(this.state.staticMenuDesktopInactive);
    }

    toggleWideView() {
        this.isWideView.set(!this.isWideView());
        this.localStorageService.setBool('DASHBOARD_WIDE_VIEW', this.isWideView());
    }

    getStaticMenuDesktopInactive$() {
      return this.staticMenuDesktopInactive$.asObservable();
    }
}
