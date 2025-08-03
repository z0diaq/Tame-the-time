# ADR-004: YAML for Schedule Configuration

**Title:** YAML for Schedule Configuration  
**Status:** Accepted  
**Date:** 2025-08-03  

## Context

The application needed a human-readable configuration format for daily schedules that would:

- Allow easy manual editing of activities and tasks
- Support version control and diff-friendly changes
- Enable template creation for different days (Monday, Tuesday, etc.)
- Provide structured data with nested elements (activities containing tasks)
- Be readable by non-technical users for schedule customization

Example schedule structure needed:
```
- Activity with time bounds
  - List of tasks
  - Description points
  - Start/end times
```

## Decision

We adopted YAML as the configuration format for schedule files with the following structure:

```yaml
- name: "Morning Routine"
  start_time: "07:00"
  end_time: "08:30"
  description:
    - "Review daily goals"
    - "Check calendar"
  tasks:
    - "Meditation"
    - "Exercise"
    - "Breakfast"

- name: "Work Block 1"
  start_time: "09:00"
  end_time: "11:00"
  description:
    - "Focus on high-priority tasks"
  tasks:
    - "Code review"
    - "Feature development"
```

**Implementation Details:**
- Files stored with `.yaml` extension
- PyYAML library for parsing and serialization
- Default templates provided for different weekdays
- File dialog integration for save/load operations
- Automatic backup and version suggestions

## Consequences

**Positive:**
- Human-readable and editable with any text editor
- Excellent version control support (meaningful diffs)
- Nested structure naturally represents activity-task relationships
- Comments supported for documentation
- Wide tooling support and syntax highlighting
- Easy template sharing between users

**Negative:**
- Indentation-sensitive syntax can cause parsing errors
- Requires PyYAML dependency
- Less validation than schema-based formats
- Potential for user syntax errors

## Alternatives

1. **JSON**: Machine-readable but less human-friendly, no comments support
2. **XML**: Too verbose for simple schedule data, poor readability
3. **INI/Config Files**: Flat structure inadequate for nested activity-task data
4. **Custom DSL**: Would require parser development and user learning curve
5. **Database Storage**: Less portable, harder for users to edit and share templates
