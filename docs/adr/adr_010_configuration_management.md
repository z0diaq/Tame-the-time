# ADR-010: Configuration Management Strategy

**Title:** Configuration Management Strategy  
**Status:** Accepted  
**Date:** 2025-08-03  

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

## Consequences

**Positive:**
- Clear separation between different configuration types
- User settings persist automatically with debounced saves
- Constants are easily discoverable and modifiable
- Schedule templates support version control and sharing
- Runtime overrides enable testing and debugging

**Negative:**
- Multiple configuration mechanisms to maintain
- No centralized configuration validation
- Potential for configuration conflicts between layers

## Alternatives

1. **Single Configuration File**: All settings in one file - rejected due to mixing concerns
2. **Database Configuration**: Store all config in SQLite - rejected as overkill
3. **Environment Variables**: System-level config - rejected for user-specific settings
4. **Registry/System Preferences**: Platform-specific - rejected for cross-platform compatibility
