---
trigger: always_on
---

When preparing new text that will be visible to user use internationalization features  and update translations of EN, ES, FR and PL stored in "locales" folder.

When preparing adding or removing features from applications analyze ADR files in "docs/adr" for potential modifications. Start with README.md and then analyze further files as needed.

Environment does have Python 3.12 available as "python3" - do not use "python" to test application.

After finishing changes and proving summary of changes provide additionally a one line change description for git commit. Use "feat:" or "fix:" at the begining of the line.