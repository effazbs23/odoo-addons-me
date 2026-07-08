// Template Loader - System to load and inject HTML templates

class TemplateLoader {
    constructor() {
        this.templates = new Map();
        this.loadingPromises = new Map();
    }

    async loadTemplate(templatePath) {
        // Return cached template if already loaded
        if (this.templates.has(templatePath)) {
            return this.templates.get(templatePath);
        }

        // Return existing promise if already loading
        if (this.loadingPromises.has(templatePath)) {
            return this.loadingPromises.get(templatePath);
        }

        // Create new loading promise
        const loadingPromise = fetch(templatePath)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load template: ${templatePath}`);
                }
                return response.text();
            })
            .then(html => {
                this.templates.set(templatePath, html);
                this.loadingPromises.delete(templatePath);
                return html;
            })
            .catch(error => {
                this.loadingPromises.delete(templatePath);
                console.error('Template loading error:', error);
                return `<div class="error">Failed to load template: ${templatePath}</div>`;
            });

        this.loadingPromises.set(templatePath, loadingPromise);
        return loadingPromise;
    }

    async injectTemplate(containerId, templatePath, data = {}) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container not found: ${containerId}`);
            return;
        }

        try {
            let html = await this.loadTemplate(templatePath);
            
            // Simple template variable replacement
            if (data && Object.keys(data).length > 0) {
                html = this.replaceTemplateVariables(html, data);
            }

            container.innerHTML = html;
            
            // Re-initialize Lucide icons after injecting template
            if (typeof lucide !== 'undefined') {
                lucide.createIcons();
            }
            
        } catch (error) {
            console.error('Template injection error:', error);
            container.innerHTML = `<div class="error">Failed to load content</div>`;
        }
    }

    replaceTemplateVariables(html, data) {
        return html.replace(/\{\{(\w+)\}\}/g, (match, key) => {
            return data[key] !== undefined ? data[key] : match;
        });
    }

    async loadMultipleTemplates(templates) {
        const promises = templates.map(async ({ containerId, templatePath, data }) => {
            return this.injectTemplate(containerId, templatePath, data);
        });
        
        return Promise.all(promises);
    }
}

// Create global instance
const templateLoader = new TemplateLoader();

// Make available globally
if (typeof window !== 'undefined') {
    window.templateLoader = templateLoader;
}