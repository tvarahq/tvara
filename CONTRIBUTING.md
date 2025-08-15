# Contributing to Tvara

First off, thank you for considering contributing to Tvara! We welcome contributions of all kinds: bug fixes, new features, documentation improvements, and more. This guide will help you follow our workflow and naming conventions to keep our repository organized.

---

## Branch Naming Conventions

To keep our branches consistent and easy to track:

- **Bug fixes:**  
  Branch name should start with `fix/`  
  **Example:** `fix/auth-cache-bug`

- **New features:**  
  Branch name should start with `feature/`  
  **Example:** `feature/multi-agent-workflow`

- **Documentation updates:**  
  Branch name should start with `docs/`  
  **Example:** `docs/adding-new-prompt-template`

- **Experimental or WIP work:**  
  Branch name should start with `wip/`  
  **Example:** `wip/realtime-agent-loop`

> **Tip:** Keep branch names descriptive but concise. Include ticket numbers if applicable (e.g., `feature/123-add-gmail-tool`).

---

## Workflow

We follow a standard GitHub flow:

1. **Fork the repository** to your own account.
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/your-username/tvara.git
   cd tvara
   ```
3. **Create a new branch** for your feature or bug fix:

   ```bash
   git checkout -b feature/my-new-feature
   ```
4. **Make your changes** and commit them:

   ```bash
   git add .
   git commit -m "Add my new feature"
   ```
5. **Push your changes** to your fork:

   ```bash
   git push origin feature/my-new-feature
   ```
6. **Create a pull request** on GitHub to merge your changes into the main repository. Include:
    - Summary of changes.
    - Motivation and context.
    - Screenshots or examples if relevant.
    - Any potential issues or breaking changes.

## Code Guidelines

- Follow PEP 8 for Python code style.
- Write docstrings for public functions and classes.
- Ensure code is type-annotated where applicable.
- Use descriptive variable and function names.
- Break large functions into smaller, reusable components.
- Ensure backwards compatibility whenever possible.

## Reporting Issues

If you find a bug or have a feature request:

- Check existing issues to avoid duplicates.
- Open a new issue with:
    - A descriptive title
    - Steps to reproduce (for bugs)
    - Expected vs. actual behavior
    - Screenshots or logs if applicable
    - Environment details (Python version, OS, etc.)

## Communication

- Join our Slack community for discussions and help.
- Be respectful and considerate in all interactions.
- Ask questions and seek clarification if unsure about workflows.

Thank you for helping make Tvara better! Your contributions make a real difference.