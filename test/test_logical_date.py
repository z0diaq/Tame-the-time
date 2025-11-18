#!/usr/bin/env python3
"""
Test script to verify logical date calculation based on day_start configuration.
This validates that database entries are created for the correct logical day.
"""

from datetime import datetime, date, timedelta
from utils.time_utils import TimeUtils


def test_logical_date():
    """Test TimeUtils.get_logical_date with various scenarios."""
    
    print("=" * 70)
    print("Testing Logical Date Calculation")
    print("=" * 70)
    
    test_cases = [
        # (current_time, day_start, expected_date, description)
        (datetime(2025, 11, 18, 3, 0), 0, date(2025, 11, 18), "Midnight day_start: 3 AM is Nov 18"),
        (datetime(2025, 11, 18, 3, 0), 6, date(2025, 11, 17), "6 AM day_start: 3 AM is still Nov 17"),
        (datetime(2025, 11, 18, 8, 0), 6, date(2025, 11, 18), "6 AM day_start: 8 AM is Nov 18"),
        (datetime(2025, 11, 18, 23, 30), 6, date(2025, 11, 18), "6 AM day_start: 11:30 PM is Nov 18"),
        (datetime(2025, 11, 18, 5, 59), 6, date(2025, 11, 17), "6 AM day_start: 5:59 AM is Nov 17"),
        (datetime(2025, 11, 18, 6, 0), 6, date(2025, 11, 18), "6 AM day_start: 6:00 AM is Nov 18"),
        (datetime(2025, 11, 18, 18, 0), 18, date(2025, 11, 18), "6 PM day_start: 6:00 PM is Nov 18"),
        (datetime(2025, 11, 18, 17, 59), 18, date(2025, 11, 17), "6 PM day_start: 5:59 PM is Nov 17"),
        (datetime(2025, 11, 18, 0, 0), 18, date(2025, 11, 17), "6 PM day_start: midnight is Nov 17"),
        (datetime(2025, 11, 18, 4, 0), 4, date(2025, 11, 18), "4 AM day_start: 4:00 AM is Nov 18"),
        (datetime(2025, 11, 18, 3, 59), 4, date(2025, 11, 17), "4 AM day_start: 3:59 AM is Nov 17"),
    ]
    
    all_passed = True
    
    for current_time, day_start, expected, description in test_cases:
        result = TimeUtils.get_logical_date(current_time, day_start)
        passed = result == expected
        all_passed = all_passed and passed
        
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"\n{status}: {description}")
        print(f"  Current time: {current_time.strftime('%Y-%m-%d %H:%M')}")
        print(f"  day_start: {day_start}")
        print(f"  Expected: {expected}")
        print(f"  Got: {result}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL TESTS PASSED")
    else:
        print("✗ SOME TESTS FAILED")
    print("=" * 70)
    
    return all_passed


def test_use_case_scenarios():
    """Test real-world scenarios from the application."""
    
    print("\n" + "=" * 70)
    print("Testing Real-World Use Case Scenarios")
    print("=" * 70)
    
    scenarios = [
        {
            "name": "Night shift worker (day_start=18)",
            "day_start": 18,
            "cases": [
                (datetime(2025, 11, 18, 20, 0), date(2025, 11, 18), "Working at 8 PM"),
                (datetime(2025, 11, 19, 2, 0), date(2025, 11, 18), "Still working at 2 AM next day"),
                (datetime(2025, 11, 19, 17, 0), date(2025, 11, 18), "End of shift at 5 PM"),
                (datetime(2025, 11, 19, 18, 0), date(2025, 11, 19), "New shift starts at 6 PM"),
            ]
        },
        {
            "name": "Late night worker (day_start=4)",
            "day_start": 4,
            "cases": [
                (datetime(2025, 11, 18, 5, 0), date(2025, 11, 18), "Start work at 5 AM"),
                (datetime(2025, 11, 18, 2, 0), date(2025, 11, 17), "Still yesterday at 2 AM"),
                (datetime(2025, 11, 18, 23, 0), date(2025, 11, 18), "Late night work"),
            ]
        },
        {
            "name": "Standard user (day_start=0)",
            "day_start": 0,
            "cases": [
                (datetime(2025, 11, 18, 0, 0), date(2025, 11, 18), "Midnight marks new day"),
                (datetime(2025, 11, 18, 23, 59), date(2025, 11, 18), "End of day"),
            ]
        },
    ]
    
    all_passed = True
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print("-" * 70)
        
        for current_time, expected, desc in scenario['cases']:
            result = TimeUtils.get_logical_date(current_time, scenario['day_start'])
            passed = result == expected
            all_passed = all_passed and passed
            
            status = "✓" if passed else "✗"
            print(f"  {status} {desc}")
            print(f"     Time: {current_time.strftime('%Y-%m-%d %H:%M')} → Logical date: {result}")
            if not passed:
                print(f"     EXPECTED: {expected}")
    
    print("\n" + "=" * 70)
    if all_passed:
        print("✓ ALL SCENARIOS PASSED")
    else:
        print("✗ SOME SCENARIOS FAILED")
    print("=" * 70)
    
    return all_passed


if __name__ == "__main__":
    test1_passed = test_logical_date()
    test2_passed = test_use_case_scenarios()
    
    print("\n" + "=" * 70)
    print("FINAL RESULT")
    print("=" * 70)
    
    if test1_passed and test2_passed:
        print("✓ All tests passed successfully!")
        print("\nThe logical date calculation is working correctly.")
        print("DB entries will now be created for the correct logical day based on day_start.")
        exit(0)
    else:
        print("✗ Some tests failed!")
        exit(1)
