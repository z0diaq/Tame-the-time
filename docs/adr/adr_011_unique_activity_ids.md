# ADR-011: Unique Activity IDs

**Title:** Unique Activity IDs for Activity Identification  
**Status:** Accepted  
**Date:** 2025-08-04  

## Context

The application previously used name-based lookup (`find_activity_by_name()`) to identify activities in the schedule. This approach had a critical flaw: when multiple activities shared the same name, the method would always return the first matching activity, causing incorrect updates when editing cards.

**Problem Scenario:**
```yaml
- name: "Work Block"
  start_time: "09:00"
  end_time: "10:00"
  description: ["First work session"]

- name: "Work Block"  # Same name!
  start_time: "11:00"
  end_time: "12:00"
  description: ["Second work session"]
```

When editing the second "Work Block", the system would incorrectly update the first one due to name-based lookup returning the first match.

**Requirements:**
- Unique identification of activities regardless of name conflicts
- Backward compatibility with existing YAML files
- No data loss during migration
- Maintain all existing functionality

## Decision

Implement UUID-based unique identification for all activities:

1. **Add unique IDs to activity data structure** using UUID4 format
2. **Replace name-based lookups** with `find_activity_by_id()` method
3. **Automatic ID generation** for activities without IDs during app startup and file loading
4. **Update serialization** to include IDs in YAML files
5. **Maintain backward compatibility** by auto-generating IDs for legacy data

**Implementation Details:**
- Each activity gets a `"id"` field with UUID4 string value
- `find_activity_by_id(activity_id)` replaces `find_activity_by_name(name)`
- `ensure_activity_ids()` method generates IDs for activities missing them
- `generate_activity_id()` creates new UUIDs for new activities
- All activity creation, editing, and lookup operations use ID-based approach

## Consequences

**Positive:**
- **Eliminates duplicate name conflicts** - each activity uniquely identifiable
- **Robust activity identification** - IDs never change or conflict
- **Backward compatible** - existing YAML files work without modification
- **Future-proof** - supports any naming scenarios without conflicts
- **Clean separation** - activity identity vs display name are distinct concepts

**Negative:**
- **Increased data size** - each activity now stores a UUID (~36 characters)
- **Migration complexity** - requires careful handling of existing data
- **YAML file changes** - files now include ID fields (though optional)
- **Debugging complexity** - IDs are less human-readable than names

**Migration Impact:**
- Existing YAML files automatically get IDs generated on first load
- No user action required - migration is transparent
- Files saved after migration will include ID fields

## Alternatives

1. **Position-based lookup** - Use array index for identification
   - Rejected: Fragile if order changes, not persistent across saves
   
2. **Enhanced name-based lookup** - Add time-based disambiguation
   - Rejected: Still possible conflicts, complex matching logic
   
3. **Reference-based approach** - Store direct object references
   - Rejected: Memory management complexity, serialization issues
   
4. **Composite keys** - Use name + start_time + end_time combination
   - Rejected: Still possible conflicts, unwieldy for frequent use
