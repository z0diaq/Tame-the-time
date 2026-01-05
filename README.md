# Tame-the-time

THIS IS THE LAST RELEASE OF THIS APPLICATION

DUE TO ATTACK OF US FORCES ON VENEZUELA I DECIDED TO STOP MAINTAINING THIS PROJECT AS PROTEST


**Version:** 0.1.4

[![Build and Release](https://github.com/z0diaq/Tame-the-time/actions/workflows/release.yml/badge.svg)](https://github.com/z0diaq/Tame-the-time/actions/workflows/release.yml)
[![Test Build](https://github.com/z0diaq/Tame-the-time/actions/workflows/test.yml/badge.svg)](https://github.com/z0diaq/Tame-the-time/actions/workflows/test.yml)

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

## Installation

### Using Poetry (Recommended)

1. Install Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
2. Clone the repository: `git clone https://github.com/z0diaq/Tame-the-time.git`
3. Navigate to directory: `cd Tame-the-time`
4. Install dependencies: `poetry install`
5. Run the application: `poetry run python TameTheTime.py`

### Using pip (Alternative)

1. Install dependencies: `pip install -r requirements.txt`
2. Run the application: `python3 TameTheTime.py`

### Check Version

```bash
python3 TameTheTime.py --version
```

## Quick Start

1. Run the application (see Installation above)
2. Load an example schedule: File → Open → Select an example YAML file
3. Customize activities: Right-click on any card to edit or add tasks
4. Track your progress: Use the statistics view to see completion rates

## Screenshots

Software Engineer...
![Software Engineer - undone tasks](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_sw_eng.png)

ADHD person...
![ADHD person - daily progress](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_ADHD.png)

Basic charts...
![Basic charts](https://github.com/z0diaq/Tame-the-time/blob/main/examples/251117_charts.png)

---

## Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed installation instructions for end users
- **[Release Process](docs/RELEASE_PROCESS.md)** - How to create releases with GitHub Actions
- **[Version Update Guide](docs/VersionUpdate.md)** - Semantic versioning and version management
- **[ADR Documentation](docs/adr/README.md)** - Architecture Decision Records
- **[CHANGELOG](CHANGELOG.md)** - Version history and changes

## Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Clone your fork**: `git clone https://github.com/YOUR_USERNAME/Tame-the-time.git`
3. **Install with Poetry**: `poetry install`
4. **Create a branch**: `git checkout -b feature/your-feature-name`
5. **Make your changes** and test thoroughly
6. **Commit**: Follow [Conventional Commits](https://www.conventionalcommits.org/)
7. **Push** and create a Pull Request

See [docs/adr/README.md](docs/adr/README.md) to understand the architecture.

## Releases

Releases are automated via GitHub Actions:
- Push a tag like `v0.1.0` to trigger a release
- Distribution packages (.whl and .tar.gz) are automatically built
- GitHub Release is created with downloadable assets
- See [docs/RELEASE_PROCESS.md](docs/RELEASE_PROCESS.md) for details

## License

GPL-3.0-or-later - see [LICENSE](LICENSE) file for details

## Support

- **Issues**: [GitHub Issues](https://github.com/z0diaq/Tame-the-time/issues)
- **Discussions**: [GitHub Discussions](https://github.com/z0diaq/Tame-the-time/discussions)

