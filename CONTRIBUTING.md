# Contributing to Suduku-Arena

Thank you for your interest in contributing! Here's how to get started.

---

## 🛠️ Development Setup

1. **Clone the repository**

   ```bash
   git clone https://github.com/shakthicode/Suduku-Arena.git
   cd Suduku-Arena
   ```

2. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` if you want to customize the server configuration.

4. **Start the server**

   Using the launcher:
   ```cmd
   run.bat
   ```
   Or manually:
   ```bash
   python backend/server.py
   ```

5. Open [http://127.0.0.1:8888](http://127.0.0.1:8888) in your browser.

---

## 📋 Guidelines

### Code Style

- **Python**: Follow [PEP 8](https://peps.python.org/pep-0008/) conventions.
- **JavaScript/JSX**: Use consistent formatting with the existing codebase.
- **HTML/CSS**: Maintain the TailwindCSS utility-first approach used in the project.

### Commit Messages

Use clear, descriptive commit messages:

```
feat: add multiplayer lobby UI
fix: resolve timer reset on page refresh
docs: update API endpoint documentation
refactor: extract score calculation into utility
```

### Pull Requests

1. Fork the repository and create a feature branch.
2. Make your changes with clear, focused commits.
3. Test your changes locally (start the server, verify functionality).
4. Open a pull request with a description of what you changed and why.

---

## 🐛 Reporting Bugs

Open an issue with:

- Steps to reproduce
- Expected behavior
- Actual behavior
- Browser and OS information

---

## 💡 Feature Requests

Open an issue describing:

- The feature you'd like
- Why it would be useful
- Any implementation ideas you have

---

## 📄 License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
