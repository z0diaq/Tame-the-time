# ADR-010: Configuration Management Strategy

**Title:** Configuration Management Strategy  
**Status:** Accepted  
**Date:** 2025-08-03
**Updated:** 2025-08-15

## Context

The application needed to manage multiple types of configuration data:

- User settings (window position, notification preferences)
- Application constants (UI dimensions, colors, timeouts)
- Schedule templates (daily activity configurations)
- Runtime parameters (debug settings, time overrides)

Requirements:
- Persistent user preferences across sessions
- Easy modification of application constants
- Template sharing and version control
- Runtime configuration for testing and debugging

## Decision

We implemented a multi-layered configuration management approach:

**1. User Settings (JSON)**
```python
# ~/.tame_the_time_settings.json
{
    "window_position": "400x700+100+100",
    "gotify_token": "...",
    "gotify_url": "https://..."
}
```

**2. Application Constants (Python)**
```python
# constants.py
class UIConstants:
    CARD_LEFT_RATIO = 0.05
    CARD_RIGHT_RATIO = 0.95
    SETTINGS_SAVE_DEBOUNCE_MS = 1000
```

**3. Schedule Configuration (YAML)**
```python
# default_settings.yaml, Monday_settings.yaml, etc.
- name: "Morning Routine"
  start_time: "07:00"
  end_time: "08:30"
  tasks: [...]
```

**4. Runtime Configuration (Command Line)**
```bash
python TameTheTime.py --time "2025-06-04T16:55:00" --no-notification
```

### Notification Configuration Management

The application provides a user-friendly interface for managing notification settings through the Global Options dialog:

**UI Components:**
- **Notification Dropdown**: Allows selection between "Disabled" and "Gotify"
- **Dynamic Fields**: Gotify URL and Token fields appear only when "Gotify" is selected
- **Secure Input**: Token field uses password masking for security
- **Auto-Detection**: Current notification type is determined by existing configuration

**Configuration Flow:**
1. User opens Global Options dialog (File → Global Options)
2. Current notification settings are loaded from `utils.notification` module
3. UI displays "Gotify" if both URL and token are configured, otherwise "Disabled"
4. When "Gotify" is selected, URL and token fields become visible and editable
5. Changes are saved immediately to `~/.tame_the_time_settings.json` on OK
6. Settings are applied to the `utils.notification` module for runtime use

**Storage Format:**
```json
{
    "window_position": "400x700+100+100",
    "gotify_token": "AaBbCc123...",
    "gotify_url": "https://gotify.example.com/message"
}
```

**Security Considerations:**
- Token field uses password masking in the UI
- Empty strings disable notifications (both URL and token must be present)
- Settings are stored in user's home directory with standard file permissions

## Consequences

**Positive:**
- Clear separation between different configuration types
- User settings persist automatically with debounced saves
- Constants are easily discoverable and modifiable
- Schedule templates support version control and sharing
- Runtime overrides enable testing and debugging
- Notification settings are configurable through Global Options UI
- Gotify credentials are securely stored and managed
- Dynamic UI shows/hides notification fields based on selection

**Negative:**
- Multiple configuration mechanisms to maintain
- No centralized configuration validation
- Potential for configuration conflicts between layers

## Alternatives

1. **Single Configuration File**: All settings in one file - rejected due to mixing concerns
2. **Database Configuration**: Store all config in SQLite - rejected as overkill
3. **Environment Variables**: System-level config - rejected for user-specific settings
4. **Registry/System Preferences**: Platform-specific - rejected for cross-platform compatibility
