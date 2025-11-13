# ADR-015: URL Extraction from Task Context Menu

**Title:** URL Extraction and Opening from Task Context Menu  
**Status:** Accepted  
**Date:** 2025-11-13

## Context

Users often include URLs in their task descriptions for quick reference to documentation, pull requests, tickets, or other resources. However, there was no way to easily access these URLs from the application UI. Users had to:

1. Open the tasks dialog
2. Read the task text
3. Manually copy the URL
4. Paste it into a browser

This workflow was cumbersome and interrupted the user's focus. Many modern applications provide direct URL opening functionality, and users expect to be able to click links without manual copy-paste operations.

Additionally, since tasks can be marked as done, we only want to show URLs from active (not-done) tasks to keep the context menu relevant and focused on current work.

## Decision

We will implement URL extraction and opening functionality directly in the card context menu with the following features:

### URL Extraction Logic

1. **Detect URLs in Task Text**: Use regex pattern matching to find URLs in task descriptions
2. **Support Multiple Formats**: Recognize both explicit protocols (`http://`, `https://`) and common patterns (`www.`)
3. **Filter by Task Status**: Only extract URLs from not-done tasks to show relevant active work
4. **Multiple URLs per Card**: Support multiple URLs across different tasks with a submenu

### Context Menu Integration

1. **"Open URL" Cascade Menu**: Add a new top-level menu option that expands to show all found URLs
2. **Task Context Display**: Show a truncated version of the task name (max 50 chars) as the menu label
3. **System Browser Integration**: Use Python's `webbrowser` module to open URLs in the user's default browser
4. **Conditional Display**: Only show the "Open URL" option if URLs are actually found

### Technical Implementation

**URL Pattern Recognition:**
```python
url_pattern = re.compile(
    r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
    r'|www\\.(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
)
```

**Key Components:**
- `extract_urls_from_tasks(card_obj)`: Extracts URLs from not-done tasks
- Submenu creation with `tk.Menu(menu, tearoff=0)`
- Closure pattern to capture URL in command callback
- Automatic `http://` prefix for `www.` URLs

### Internationalization

Translated menu labels added to all language files:
- **English**: "Open URL"
- **Spanish**: "Abrir URL"
- **French**: "Ouvrir URL"

## Consequences

**Positive:**
- **Improved Workflow**: Users can access URLs with 2 clicks instead of 6+ steps
- **Context Preservation**: Stay focused without switching to other applications
- **Task-Aware**: Only shows URLs from active work, reducing clutter
- **Multiple URL Support**: Handles cards with multiple tasks containing different URLs
- **Cross-Platform**: `webbrowser` module works on Linux, macOS, and Windows
- **User-Friendly**: Truncates long task names to keep menu readable
- **Localized**: Fully supports all three languages (English, Spanish, French)

**Negative:**
- **Regex Limitations**: May miss unconventional URL formats or markdown links
- **Security Consideration**: Opens URLs without validation (relies on browser security)
- **Menu Clutter**: Cards with many URLs could create long submenus
- **No URL Preview**: Users can't see the full URL before clicking (just task name)

**Neutral:**
- **Performance**: Regex matching is fast for typical task text lengths
- **Dependency**: Adds `re` and `webbrowser` module dependencies (both standard library)
- **Code Location**: Keeps all context menu logic centralized in `ui/context_menu.py`

## Use Cases

### Scenario 1: Single URL in Task
```
Task: "Review PR at https://github.com/user/repo/pull/123"
Right-click → "Open URL" → "Review PR at https://github.com/user/repo/..."
Click → Opens in browser
```

### Scenario 2: Multiple URLs Across Tasks
```
Tasks:
- "Check docs at https://docs.example.com" (not done)
- "Review ticket https://jira.example.com/PROJ-456" (not done)
- "Read article https://blog.example.com/post" (done - hidden)

Right-click → "Open URL" → Shows 2 submenu items
```

### Scenario 3: No URLs Present
```
Tasks:
- "Write code" (not done)
- "Test feature" (not done)

Right-click → No "Open URL" option shown
```

### Scenario 4: www. Format URL
```
Task: "Check www.github.com for updates" (not done)
Right-click → "Open URL" → "Check www.github.com for updates"
Click → Opens http://www.github.com (auto-prefixed)
```

## Alternatives Considered

### 1. Inline Clickable Links
**Description**: Make URLs clickable directly in the task text within the task dialog  
**Rejected**: Would require custom text widget with link detection, more complex UI changes

### 2. URL Icon on Card
**Description**: Show a link icon on cards with URLs that opens a popup  
**Rejected**: Adds visual clutter, less discoverable than context menu

### 3. All URLs Regardless of Status
**Description**: Show URLs from all tasks, including completed ones  
**Rejected**: Clutters menu with no longer relevant information

### 4. URL Validation Before Opening
**Description**: Validate URL accessibility before adding to menu  
**Rejected**: Would slow down context menu display, network dependency

### 5. Copy URL to Clipboard
**Description**: Instead of opening, copy URL to clipboard  
**Rejected**: Still requires user to manually paste and navigate

## Related ADRs

- **ADR-002**: Tkinter UI Framework (context menu implementation)
- **ADR-009**: Event-Driven UI Architecture (right-click event handling)
- **ADR-012**: JSON Internationalization (menu label translation)

## Implementation Details

**Files Modified:**
- `ui/context_menu.py`: Added `extract_urls_from_tasks()` and URL submenu logic
- `locales/en.json`: Added "context_menu.open_url" translation
- `locales/es.json`: Added "context_menu.open_url" translation
- `locales/fr.json`: Added "context_menu.open_url" translation

**Dependencies:**
- `re` (standard library): URL pattern matching
- `webbrowser` (standard library): System browser integration

## Future Considerations

1. **URL Preview Tooltip**: Show full URL on hover before clicking
2. **Custom URL Actions**: Allow users to configure what happens with different URL types (e.g., copy vs. open)
3. **Markdown Link Support**: Parse markdown-style links `[text](url)`
4. **URL Validation**: Add optional URL reachability check with caching
5. **URL History**: Track frequently accessed URLs for quick access
6. **Deep Link Support**: Handle application-specific URLs (e.g., `slack://`, `vscode://`)
7. **URL Shortening Display**: Show shortened versions of very long URLs
