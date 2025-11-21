/**
 * JW Time Website - Main JavaScript
 * Handles theme switching, language selection, and navigation
 */

(function() {
    'use strict';

    // ==========================================
    // Theme Management
    // ==========================================

    const Theme = {
        STORAGE_KEY: 'jwtime-theme',
        DARK: 'dark',
        LIGHT: 'light',
        AUTO: 'auto',

        /**
         * Initialize theme based on user preference or system settings
         */
        init() {
            const savedTheme = this.getSavedTheme();

            if (savedTheme === this.AUTO || !savedTheme) {
                this.applySystemTheme();
                this.watchSystemTheme();
            } else {
                this.applyTheme(savedTheme);
            }

            this.setupToggleButton();
        },

        /**
         * Get saved theme from localStorage
         */
        getSavedTheme() {
            return localStorage.getItem(this.STORAGE_KEY);
        },

        /**
         * Save theme preference
         */
        saveTheme(theme) {
            localStorage.setItem(this.STORAGE_KEY, theme);
        },

        /**
         * Apply theme to document
         */
        applyTheme(theme) {
            document.body.classList.remove('dark-theme', 'light-theme');

            if (theme === this.DARK) {
                document.body.classList.add('dark-theme');
            } else if (theme === this.LIGHT) {
                document.body.classList.add('light-theme');
            }
        },

        /**
         * Apply system theme based on prefers-color-scheme
         */
        applySystemTheme() {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            this.applyTheme(prefersDark ? this.DARK : this.LIGHT);
        },

        /**
         * Watch for system theme changes
         */
        watchSystemTheme() {
            const darkModeQuery = window.matchMedia('(prefers-color-scheme: dark)');

            darkModeQuery.addEventListener('change', (e) => {
                const savedTheme = this.getSavedTheme();
                if (savedTheme === this.AUTO || !savedTheme) {
                    this.applyTheme(e.matches ? this.DARK : this.LIGHT);
                }
            });
        },

        /**
         * Toggle between light and dark themes
         */
        toggle() {
            const currentTheme = this.getCurrentTheme();
            const newTheme = currentTheme === this.DARK ? this.LIGHT : this.DARK;

            this.applyTheme(newTheme);
            this.saveTheme(newTheme);
            this.updateToggleButton(newTheme);
        },

        /**
         * Get current active theme
         */
        getCurrentTheme() {
            if (document.body.classList.contains('dark-theme')) {
                return this.DARK;
            } else if (document.body.classList.contains('light-theme')) {
                return this.LIGHT;
            } else {
                return window.matchMedia('(prefers-color-scheme: dark)').matches ? this.DARK : this.LIGHT;
            }
        },

        /**
         * Setup theme toggle button
         */
        setupToggleButton() {
            const toggleBtn = document.getElementById('theme-toggle');
            if (!toggleBtn) return;

            const currentTheme = this.getCurrentTheme();
            this.updateToggleButton(currentTheme);

            toggleBtn.addEventListener('click', () => {
                this.toggle();
            });
        },

        /**
         * Update toggle button icon
         */
        updateToggleButton(theme) {
            const toggleBtn = document.getElementById('theme-toggle');
            if (!toggleBtn) return;

            // Icons for light/dark mode
            const sunIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z"/>
            </svg>`;

            const moonIcon = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                <path fill-rule="evenodd" d="M9.528 1.718a.75.75 0 01.162.819A8.97 8.97 0 009 6a9 9 0 009 9 8.97 8.97 0 003.463-.69.75.75 0 01.981.98 10.503 10.503 0 01-9.694 6.46c-5.799 0-10.5-4.701-10.5-10.5 0-4.368 2.667-8.112 6.46-9.694a.75.75 0 01.818.162z" clip-rule="evenodd"/>
            </svg>`;

            toggleBtn.innerHTML = theme === this.DARK ? sunIcon : moonIcon;
            toggleBtn.setAttribute('title', theme === this.DARK ? 'Switch to light mode' : 'Switch to dark mode');
        }
    };

    // ==========================================
    // Language Management
    // ==========================================

    const Language = {
        STORAGE_KEY: 'jwtime-lang',
        SUPPORTED: ['it', 'en', 'es', 'de', 'fr', 'pt_BR'],

        /**
         * Save language preference
         */
        save(lang) {
            if (this.SUPPORTED.includes(lang)) {
                localStorage.setItem(this.STORAGE_KEY, lang);
            }
        },

        /**
         * Get saved language
         */
        get() {
            return localStorage.getItem(this.STORAGE_KEY);
        },

        /**
         * Switch to a different language
         */
        switch(newLang) {
            if (!this.SUPPORTED.includes(newLang)) return;

            this.save(newLang);

            // Get current path
            const currentPath = window.location.pathname;
            const basePath = currentPath.includes('/jwtime/') ? '/jwtime/' : '/';

            // Extract current page (e.g., 'manual.html', 'news.html')
            const pathParts = currentPath.split('/');
            const currentPage = pathParts[pathParts.length - 1] || 'index.html';

            // Navigate to the same page in the new language
            window.location.href = `${basePath}${newLang}/${currentPage}`;
        },

        /**
         * Initialize language selector
         */
        init() {
            const langLinks = document.querySelectorAll('[data-lang]');

            langLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const targetLang = link.getAttribute('data-lang');
                    this.switch(targetLang);
                });
            });

            // Save current language when on a language-specific page
            this.detectAndSaveCurrentLanguage();
        },

        /**
         * Detect current language from URL and save it
         */
        detectAndSaveCurrentLanguage() {
            const currentPath = window.location.pathname;

            // Try to extract language from path (e.g., /it/, /en/, etc.)
            const langMatch = currentPath.match(/\/(it|en|es|de|fr|pt_BR)\//);
            if (langMatch) {
                this.save(langMatch[1]);
            }
        }
    };

    // ==========================================
    // Navigation Utilities
    // ==========================================

    const Navigation = {
        /**
         * Mark active navigation link
         */
        setActiveLink() {
            const currentPath = window.location.pathname;
            const navLinks = document.querySelectorAll('.nav a');

            navLinks.forEach(link => {
                const linkPath = link.getAttribute('href');

                if (currentPath.includes(linkPath) && linkPath !== '/') {
                    link.classList.add('active');
                } else {
                    link.classList.remove('active');
                }
            });
        },

        /**
         * Setup mobile menu toggle (if needed)
         */
        setupMobileMenu() {
            const menuToggle = document.getElementById('mobile-menu-toggle');
            const nav = document.querySelector('.nav');

            if (!menuToggle || !nav) return;

            menuToggle.addEventListener('click', () => {
                nav.classList.toggle('active');
                menuToggle.classList.toggle('active');
            });
        },

        /**
         * Smooth scroll for anchor links
         */
        setupSmoothScroll() {
            const anchorLinks = document.querySelectorAll('a[href^="#"]');

            anchorLinks.forEach(link => {
                link.addEventListener('click', (e) => {
                    const targetId = link.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);

                    if (targetElement) {
                        e.preventDefault();
                        targetElement.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                });
            });
        }
    };

    // ==========================================
    // Utilities
    // ==========================================

    const Utils = {
        /**
         * Add copy button to code blocks
         */
        addCopyButtonsToCodeBlocks() {
            const codeBlocks = document.querySelectorAll('pre code');

            codeBlocks.forEach(codeBlock => {
                const pre = codeBlock.parentElement;
                const button = document.createElement('button');

                button.className = 'copy-code-btn';
                button.textContent = 'Copy';
                button.style.cssText = 'position: absolute; top: 8px; right: 8px; padding: 4px 8px; font-size: 0.8rem; background: var(--accent-green); color: white; border: none; border-radius: 4px; cursor: pointer;';

                pre.style.position = 'relative';
                pre.appendChild(button);

                button.addEventListener('click', () => {
                    const code = codeBlock.textContent;
                    navigator.clipboard.writeText(code).then(() => {
                        button.textContent = 'Copied!';
                        setTimeout(() => {
                            button.textContent = 'Copy';
                        }, 2000);
                    });
                });
            });
        },

        /**
         * Setup external links to open in new tab
         */
        setupExternalLinks() {
            const links = document.querySelectorAll('a[href^="http"]');

            links.forEach(link => {
                if (!link.hostname.includes(window.location.hostname)) {
                    link.setAttribute('target', '_blank');
                    link.setAttribute('rel', 'noopener noreferrer');
                }
            });
        },

        /**
         * Ensure manual images wrap correctly on narrow screens
         */
        enhanceManualImages() {
            const manualImages = document.querySelectorAll('.manual-image');

            manualImages.forEach(img => {
                const parent = img.parentElement;
                if (parent && !parent.classList.contains('manual-image-wrapper')) {
                    parent.classList.add('manual-image-wrapper');
                }
            });
        }
    };

    // ==========================================
    // Initialize Everything
    // ==========================================

    function init() {
        // Wait for DOM to be ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initAll);
        } else {
            initAll();
        }
    }

    function initAll() {
        Theme.init();
        Language.init();
        Navigation.setActiveLink();
        Navigation.setupMobileMenu();
        Navigation.setupSmoothScroll();
        Utils.addCopyButtonsToCodeBlocks();
        Utils.setupExternalLinks();
        Utils.enhanceManualImages();
    }

    // Start initialization
    init();

    // Expose API for external use if needed
    window.JWTimeWebsite = {
        Theme,
        Language,
        Navigation,
        Utils
    };

})();
