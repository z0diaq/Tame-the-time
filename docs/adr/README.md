# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records for the Tame-the-Time timeboxing application.

NOTE: These files have been added retroactively and dates are not (yet) based on actual commits' history.
This will be fixed at a later time.

## ADR Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-000](adr_000.md) | ADR Template | Template | - |
| [ADR-001](adr_001_layered_architecture.md) | Layered Architecture with Separation of Concerns | Accepted | 2025-08-03 |
| [ADR-002](adr_002_tkinter_ui_framework.md) | Tkinter as UI Framework | Accepted | 2025-08-03 |
| [ADR-003](adr_003_sqlite_task_tracking.md) | SQLite for Task Tracking Database | Accepted | 2025-08-03 |
| [ADR-004](adr_004_yaml_configuration.md) | YAML for Schedule Configuration | Accepted | 2025-08-03 |
| [ADR-005](adr_005_dependency_injection_pattern.md) | Dependency Injection Pattern for Time Provider | Accepted | 2025-08-03 |
| [ADR-006](adr_006_service_layer_pattern.md) | Service Layer Pattern for Business Logic | Accepted | 2025-08-03 |
| [ADR-007](adr_007_canvas_based_rendering.md) | Canvas-Based Rendering for Timeline Visualization | Accepted | 2025-08-03 |
| [ADR-008](adr_008_matplotlib_statistics.md) | Matplotlib for Statistics Visualization | Accepted | 2025-08-03 |
| [ADR-009](adr_009_event_driven_ui.md) | Event-Driven UI Architecture | Accepted | 2025-08-03 |
| [ADR-010](adr_010_configuration_management.md) | Configuration Management Strategy | Accepted | 2025-08-03 |
| [ADR-011](adr_011_unique_activity_ids.md) | Unique Activity IDs for Activity Identification | Accepted | 2025-08-04 |

## ADR Categories

### Architecture & Design Patterns
- **ADR-001**: Layered Architecture - Overall system organization
- **ADR-005**: Dependency Injection - Time provider pattern
- **ADR-006**: Service Layer - Business logic organization
- **ADR-009**: Event-Driven UI - User interaction handling

### Technology Choices
- **ADR-002**: Tkinter - UI framework selection
- **ADR-003**: SQLite - Database technology
- **ADR-004**: YAML - Configuration format
- **ADR-008**: Matplotlib - Charts and visualization

### Implementation Strategies
- **ADR-007**: Canvas Rendering - Timeline visualization approach
- **ADR-010**: Configuration Management - Multi-layered config strategy
- **ADR-011**: Unique Activity IDs - Activity identification and duplicate name resolution

## How to Use ADRs

1. **For New Contributors**: Read ADRs 001, 002, and 006 to understand the overall architecture
2. **For UI Development**: Focus on ADRs 002, 007, and 009
3. **For Data/Persistence**: Review ADRs 003, 004, and 010
4. **For Testing**: ADR-005 explains the dependency injection pattern crucial for testing

## Creating New ADRs

When making significant architectural decisions:

1. Copy the template from `adr_000.md`
2. Number sequentially (ADR-011, ADR-012, etc.)
3. Follow the format: Title, Status, Context, Decision, Consequences, Alternatives
4. Update this index file
5. Consider if any existing ADRs should be marked as "Superseded"
