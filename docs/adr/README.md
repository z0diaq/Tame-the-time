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
| [ADR-012](adr_012_json_internationalization.md) | JSON-Based Internationalization System | Accepted | 2025-09-16 |
| [ADR-013](adr_013_day_start_configuration.md) | Day Start Configuration for Card Management | Accepted | 2025-09-20 |
| [ADR-014](adr_014_forgiving_streak_counting.md) | Forgiving Streak Counting Logic for Task Completion | Accepted | 2025-10-24 |
| [ADR-015](adr_015_url_extraction_context_menu.md) | URL Extraction and Opening from Task Context Menu | Accepted | 2025-11-13 |
| [ADR-016](adr_016_card_repositioning.md) | Interactive Card Repositioning with Time Validation | Accepted | 2025-11-22 |

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
- **ADR-012**: JSON Internationalization - Multi-language support system
- **ADR-013**: Day Start Configuration - Flexible daily schedule alignment
- **ADR-014**: Forgiving Streak Counting - User-friendly task streak logic

### User Experience Features
- **ADR-015**: URL Extraction from Context Menu - Quick access to task-embedded URLs
- **ADR-016**: Card Repositioning - Interactive card movement with validation

## How to Use ADRs

1. **For New Contributors**: Read ADRs 001, 002, and 006 to understand the overall architecture
2. **For UI Development**: Focus on ADRs 002, 007, 009, 015, and 016
3. **For Data/Persistence**: Review ADRs 003, 004, and 010
4. **For Task Tracking & Statistics**: See ADRs 003 and 014 for database and streak logic
5. **For Testing**: ADR-005 explains the dependency injection pattern crucial for testing
6. **For User Experience**: See ADRs 015 and 016 for context menu enhancements

## Creating New ADRs

When making significant architectural decisions:

1. Copy the template from `adr_000.md`
2. Number sequentially (ADR-011, ADR-012, etc.)
3. Follow the format: Title, Status, Context, Decision, Consequences, Alternatives
4. Update this index file
5. Consider if any existing ADRs should be marked as "Superseded"
