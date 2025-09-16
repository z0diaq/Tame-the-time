Title: JSON-Based Internationalization System
Status: Accepted
Context: The Tame-the-Time application currently has all user-facing text hardcoded in English throughout the UI components. Users have requested the ability to select different languages for the application interface, including menu options, window titles, dialog fields, and error messages. The solution needs to be easily maintainable, simple for translators to work with, and allow easy addition of new languages through language files.

Decision: Implement a JSON-based internationalization (i18n) system with the following components:
- A centralized Translator class in utils/translator.py that manages language loading and text lookup
- JSON language files stored in a locales/ directory (e.g., en.json, es.json, fr.json)
- Nested JSON structure for organized translation keys (e.g., "window.main_title", "menu.file")
- Language selection integrated into the Global Options dialog
- Automatic fallback to English for missing translations
- Language preference stored in user settings for persistence across sessions

Consequences:
Positive:
- Simple implementation requiring no external dependencies beyond Python's built-in json module
- Fast loading and lookup performance suitable for desktop applications
- Easy for translators to work with - standard JSON format with clear key-value structure
- Organized translation keys using dot notation for logical grouping
- Seamless integration with existing settings system
- Maintains consistency with application's preference for lightweight solutions

Negative:
- JSON doesn't support comments, making it slightly less translator-friendly than YAML
- Requires systematic refactoring of all UI components to replace hardcoded strings
- No built-in pluralization support (though can be implemented if needed)
- Manual management of translation completeness across languages

Alternatives:
- Python gettext: Industry standard but more complex setup, requires compilation step (.po → .mo files), and steeper learning curve
- YAML-based system: More readable with comment support but requires PyYAML dependency and slightly slower parsing
- Direct dictionary approach: Simpler but less maintainable and harder for translators to work with
- External i18n libraries: Overkill for desktop application and adds unnecessary dependencies
