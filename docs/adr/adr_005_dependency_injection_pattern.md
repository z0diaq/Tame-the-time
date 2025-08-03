# ADR-005: Dependency Injection Pattern for Time Provider

**Title:** Dependency Injection Pattern for Time Provider  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The application needed a way to handle time-dependent functionality that would:

- Enable testing with controlled time scenarios
- Support time simulation and timelapse features
- Allow debugging at specific times
- Maintain consistent time handling across the application
- Support real-time updates and scheduling

The challenge was that many components needed current time information, but hardcoding `datetime.now()` calls would make testing and time simulation impossible.

## Decision

We implemented a dependency injection pattern for time provision using a `now_provider` parameter:

```python
class TimeboxApp(tk.Tk):
    def __init__(self, schedule: List[Dict], config_path: str, now_provider=datetime.now):
        self.now_provider = now_provider
        # Pass to services and components
        self.notification_service = NotificationService(now_provider, ...)
        
class TaskCard:
    def __init__(self, activity: Dict, ..., now_provider=None):
        self.now_provider = now_provider
        
    def is_active_at(self, time_obj):
        # Use injected time provider for consistency
```

**Implementation Details:**
- Default parameter `now_provider=datetime.now` for production use
- Injectable custom time providers for testing and simulation
- Consistent time handling across UI, services, and models
- Support for command-line time override (`--time "2025-06-04T16:55:00"`)

## Consequences

**Positive:**
- Enables comprehensive testing with controlled time scenarios
- Supports debugging at specific times without system clock changes
- Allows time simulation and timelapse features
- Maintains consistent time across all components
- Clean separation between time logic and business logic
- Easy to mock for unit tests

**Negative:**
- Additional parameter to pass through component hierarchy
- Slight complexity increase in constructor signatures
- Requires discipline to use injected provider instead of direct datetime calls

## Alternatives

1. **Global Time Service**: Singleton pattern but harder to test and control
2. **System Clock Direct**: Simple but impossible to test time-dependent scenarios
3. **Time Context Manager**: More complex setup for dependency management
4. **Observer Pattern**: Overkill for time provision, adds unnecessary complexity
