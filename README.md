# Tame-the-time
Timeboxing UI application with gamification

Features:
- per day templates
- activities and tasks tracking
- history and charts
- optional Gotify notifications
- sometime in the future: gamification features (streaks, achievements etc.)


## Use Cases & Benefits

Tame-the-Time is designed to help anyone who wants to structure their day and stay focused. Here are some examples of how different people can use it effectively:

### 🧑‍💻 Software Engineers & Developers
**Use Case:** Balance coding sessions, meetings, code reviews, and breaks to maintain high productivity

**Benefits:**
- **Deep Work Protection**: Dedicated time blocks for coding prevent context switching
- **Meeting Management**: Clear boundaries between collaborative and focused work
- **Break Reminders**: Regular breaks prevent burnout and maintain code quality
- **Task Tracking**: Monitor progress on features, bugs, and technical debt
- **Visual Timeline**: See your entire day at a glance and plan around meetings

**Example Schedule:** See `examples/software_engineer.yaml`

---

### 🎓 College Students
**Use Case:** Organize study time across multiple subjects with proper breaks and assignment deadlines

**Benefits:**
- **Subject Balance**: Ensure equal attention to all courses
- **Focus Enhancement**: Time-boxed study sessions improve concentration
- **Break Management**: Structured breaks prevent study fatigue
- **Assignment Tracking**: Track progress on papers, projects, and problem sets
- **Exam Preparation**: Allocate specific time for review and practice
- **Routine Building**: Consistent daily schedule improves academic performance

**Example Schedule:** See `examples/college_student.yaml`

---

### 🧠 Individuals with ADHD
**Use Case:** Create external structure with frequent task switches, reminders, and clear boundaries

**Benefits:**
- **External Structure**: Visual timeline provides the structure ADHD brains need
- **Task Initiation**: Clear start times remove decision paralysis
- **Hyperfocus Management**: Time limits prevent getting stuck on one task
- **Transition Support**: Scheduled breaks between tasks ease context switching
- **Dopamine Hits**: Checking off completed tasks provides immediate reward
- **Notification Reminders**: Gotify notifications help with time blindness
- **Anxiety Reduction**: Knowing what's next reduces planning anxiety
- **Energy Management**: Schedule demanding tasks during peak energy periods

**Example Schedule:** See `examples/adhd_structure.yaml`

---

## Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python TameTheTime.py`
3. Load an example schedule: File → Open → Select an example YAML file
4. Customize activities: Right-click on any card to edit or add tasks
5. Track your progress: Use the statistics view to see completion rates

## Screenshots

Software Engineer...
![Software Engineer - undone tasks](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_sw_eng.png)

ADHD person...
![ADHD person - daily progress](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_ADHD.png)

Basic charts...
![Basic charts](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_charts.png)

