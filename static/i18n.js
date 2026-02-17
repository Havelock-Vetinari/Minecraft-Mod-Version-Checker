const i18n = {
    currentLang: 'en',

    init() {
        // Ensure translations object exists
        if (typeof translations === 'undefined') {
            console.error('Translations not loaded!');
            return;
        }
        const savedLang = localStorage.getItem('language');
        if (savedLang && translations[savedLang]) {
            this.currentLang = savedLang;
        } else {
            const browserLang = navigator.language.split('-')[0];
            if (translations[browserLang]) {
                this.currentLang = browserLang;
            }
        }
        this.updateUI();
    },

    setLanguage(lang) {
        if (translations[lang]) {
            this.currentLang = lang;
            localStorage.setItem('language', lang);
            this.updateUI();
            // Refresh dynamic data to apply new language to dynamic strings
            if (typeof loadInitialData === 'function') {
                loadInitialData();
            }
        }
    },

    t(key, params = {}) {
        const keys = key.split('.');
        let value = translations[this.currentLang];

        for (const k of keys) {
            if (value && value[k]) {
                value = value[k];
            } else {
                // Fallback to English if key not found in current language
                value = translations['en'];
                for (const ek of keys) {
                    if (value && value[ek]) {
                        value = value[ek];
                    } else {
                        return key; // Return key if not found at all
                    }
                }
                break;
            }
        }

        if (typeof value === 'string') {
            Object.keys(params).forEach(param => {
                value = value.replace(`{${param}}`, params[param]);
            });
            return value;
        }
        return key;
    },

    translateLog(message) {
        const langData = translations[this.currentLang] || translations['en'];
        const patterns = langData.log_patterns || translations['en'].log_patterns;

        for (const entry of patterns) {
            const match = message.match(entry.pattern);
            if (match) {
                let translated = entry.replacement;
                for (let i = 1; i < match.length; i++) {
                    translated = translated.replace(`$${i}`, match[i]);
                }
                return translated;
            }
        }
        return message;
    },

    updateUI() {
        // Update document layout orientation if needed (not needed for PL/EN)
        document.documentElement.lang = this.currentLang;

        // Update elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const attr = el.getAttribute('data-i18n-attr');

            if (attr) {
                el.setAttribute(attr, this.t(key));
            } else {
                el.textContent = this.t(key);
            }
        });

        // Update language selector if exists
        const selector = document.getElementById('languageSelector');
        if (selector) {
            selector.value = this.currentLang;
        }
    }
};

// Auto-init on load
document.addEventListener('DOMContentLoaded', () => i18n.init());
