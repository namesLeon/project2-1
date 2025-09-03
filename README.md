# Team_08 GitLab Coding & Collaboration Rules

To ensure consistency, maintainability, and smooth collaboration across Team_08, we follow these rules when working with GitLab.

---

##  Repository Structure
- Keep the repository clean and organized.
- Place code in appropriate directories (`src/`, `tests/`, `docs/`, etc.).
- Avoid committing generated or build files (use `.gitignore`).

---

##  Branching Strategy
- **Main branch**: always production-ready and passing tests.
- **Develop branch**: staging area for features before merging into `main`.
- **Feature branches**:  
  - Use the naming convention:  
    ```
    feature/<short-description>
    bugfix/<short-description>
    hotfix/<short-description>
    ```
  - Example: `feature/login-auth`, `bugfix/navbar-overlap`.

---

##  Commit Messages
-   To be honest, just keep it short