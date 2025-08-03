# ADR-006: Service Layer Pattern for Business Logic

**Title:** Service Layer Pattern for Business Logic  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The application needed to organize business logic that didn't belong in UI components or domain models:

- Notification management with timing logic
- Task tracking with database operations
- External integrations (Gotify notifications)
- Cross-cutting concerns that span multiple domain objects
- Complex workflows involving multiple components

The challenge was avoiding fat controllers (UI components with too much logic) while keeping domain models focused on data and core business rules.

## Decision

We implemented a Service Layer pattern with dedicated service classes in the `services/` directory:

```python
services/
├── notification_service.py    # Activity notifications and timing
├── task_tracking_service.py   # Task persistence and statistics
└── __init__.py
```

**Service Characteristics:**
- Stateful services injected into main application
- Encapsulate complex business workflows
- Handle external system integrations
- Coordinate between domain models and persistence
- Provide clean APIs for UI layer consumption

**Example Implementation:**
```python
class NotificationService:
    def __init__(self, now_provider, on_activity_change=None):
        self.now_provider = now_provider
        self.on_activity_change = on_activity_change
        
    def check_and_send_notifications(self, schedule, current_activity):
        # Complex notification timing logic
        
class TaskTrackingService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self._init_database()
        
    def mark_task_done(self, activity_name, task_name):
        # Database operations and business rules
```

## Consequences

**Positive:**
- Clear separation between UI, business logic, and data access
- Services are easily testable in isolation
- Complex workflows are encapsulated and reusable
- UI components remain focused on presentation
- Business logic is centralized and discoverable
- Easy to mock services for testing UI components

**Negative:**
- Additional abstraction layer increases initial complexity
- Service dependencies need careful management
- Risk of services becoming too large if not properly decomposed

## Alternatives

1. **Fat Controllers**: Business logic in UI components - rejected due to poor testability
2. **Domain Services**: Logic in domain models - rejected as models should focus on data
3. **Utility Functions**: Stateless functions - rejected as services need state and lifecycle
4. **Manager Classes**: Similar to services but less clear naming convention
