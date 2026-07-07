# Sudoko-Arena Windows Launcher Documentation

This document describes the design, operational features, and advanced deployment options of the professional Windows launcher (`run.bat`) for the **Sudoko-Arena** application.

---

## 🏗️ Core Launcher Design (`run.bat`)

The [run.bat](../run.bat) script automates the complete lifecycle of starting, verifying, and stopping the local Sudoko-Arena application. It eliminates manual environment setup steps and isolates dependencies to guarantee a consistent "double-click" runtime experience for end users.

### Lifecycle Phases:
1. **Environment Check**:
   - Searches PATH for `python` or `py` execution commands.
   - Ensures the installed Python version is **3.10+**.
2. **Virtual Environment Isolation**:
   - Checks if a localized `.venv` folder exists.
   - If missing, builds it automatically: `python -m venv .venv`. This avoids modifying the global Python environment.
   - Activates the virtual environment context.
3. **Optimized Dependency Management**:
   - Runs a fast Python verification command (`import bcrypt, dotenv`) to check if the required packages are already present.
   - Runs `pip install` only when libraries are missing, bypassing redundant install checks on every startup.
4. **Port Conflict Management**:
   - Checks if the port (default `8888`) is occupied using `netstat`.
   - If occupied, looks for `logs/server.pid`. If it belongs to an orphaned instance of this app, it terminates it.
   - If it belongs to another application, it stops safely and prompts the user.
5. **Background Server Launch**:
   - Writes a command wrapper `logs/start_server.cmd` that activates the venv and spawns `server.py` in a background shell.
   - Spawns the server process and stores the process ID (PID) to `logs/server.pid`.
6. **Wait Loop Verification**:
   - Runs a PowerShell connection test loop to `127.0.0.1:8888`.
   - Displays progress dots (`...`) while waiting, verifying when the endpoint returns a `200 OK`.
7. **Browser Launch**:
   - Spawns the system's default browser to load `http://127.0.0.1:8888/`.
8. **Graceful Shutdown**:
   - Blocks terminal closure and prompts user to press ENTER to stop the game.
   - Reads the exact PID from `logs/server.pid`, terminates that process, and deletes the temporary PID log.

---

## 🤫 Option A: Silent Launching (No Console Window)

By default, double-clicking `run.bat` leaves a Command Prompt window open in the background. If you want to start the app silently without any console window visible, you can use a lightweight VBScript wrapper.

### Setup Instructions:
1. Create a new text file named `run_silent.vbs` in the project root directory.
2. Copy and paste the following code into the file:

```vbs
Set WshShell = CreateObject("WScript.Shell")
WshShell.Run Chr(34) & WshShell.CurrentDirectory & "\run.bat" & Chr(34), 0, False
Set WshShell = Nothing
```

3. Double-clicking `run_silent.vbs` will execute `run.bat` in a completely hidden background state.
4. *To stop the server in silent mode*: End the `python.exe` process from Windows Task Manager, or run the following command in a terminal:
   ```cmd
   taskkill /F /FI "IMAGENAME eq python.exe"
   ```

---

## 📦 Option B: Installer-Ready Packaging (Inno Setup)

To package Sudoko-Arena as a standalone offline Windows desktop installer, we recommend using **Inno Setup** (a free, open-source installer generator).

### Packaging Workflow:
1. Ensure the project root folder has a clean configuration:
   - Run `run.bat` once to pre-compile the `.venv` and download Python dependencies while online.
   - Verify that `database/` is cleared of test user profiles.
2. Download and install [Inno Setup](https://jrsoftware.org/isinfo.php).
3. Create an installation script (e.g., `setup.iss`) in the parent directory:

```ini
[Setup]
AppName=Sudoku Arena
AppVersion=1.0
DefaultDirName={userpf}\SudokuArena
DefaultGroupName=Sudoku Arena
UninstallDisplayIcon={app}\run.bat
Compression=lzma2
SolidCompression=yes
OutputDir=userdocs:SudokuArenaInstaller

[Files]
; Copy all project files including the pre-compiled .venv directory
Source: "C:\path\to\Sudoko-Arena\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

[Icons]
; Create a Desktop shortcut pointing to the launcher script
Name: "{userdesktop}\Sudoku Arena"; Filename: "{app}\run.bat"; WorkingDir: "{app}"
; Create Start Menu shortcuts
Name: "{group}\Sudoku Arena"; Filename: "{app}\run.bat"; WorkingDir: "{app}"
Name: "{group}\Uninstall Sudoku Arena"; Filename: "{uninstiseqe}"
```

4. Compile the Inno Setup script. The output executable will pack the React frontend, Python backend, all libraries in the `.venv` directory, and your custom launcher into a single desktop installer.
5. When the user installs and double-clicks the desktop icon, the `run.bat` script runs in its local directory and launches the application offline instantly!
