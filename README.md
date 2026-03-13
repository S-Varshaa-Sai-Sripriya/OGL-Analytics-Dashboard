# OGL Dashboard

Interactive Streamlit dashboard for exploring OGL data using charts, grouping, and filters.

## What this project does

- Loads data from Excel (`.xlsx`, `.xls`) or CSV (`.csv`)
- Supports multi-sheet Excel files
- Lets you group data by up to 5 fields
- Generates multiple chart types (bar, stacked bar, pie, donut, line, scatter, area)
- Optionally shows and exports matching line items

## Project structure

```
D - OGL Dashboard/
├── app.py
├── requirements.txt
├── Dataset/
├── templates/
│   └── index.html
└── README.md
```

## Prerequisites

Install the following before running:

1. **Python 3.10+** (recommended)
2. **pip** (comes with Python)
3. Internet access for installing packages

> Verify installation:
>
> ```bash
> python --version
> pip --version
> ```

---

## Setup and run (step-by-step)

### 1) Open terminal in project folder

```bash
cd "<location>"
```

### 2) Create a virtual environment (recommended)

**Windows (PowerShell):**

```powershell
python -m venv .venv
```

**macOS/Linux:**

```bash
python3 -m venv .venv
```

### 3) Activate virtual environment

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, run once:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again.

**Windows (Command Prompt):**

```cmd
.venv\Scripts\activate.bat
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

### 4) Install dependencies

```bash
pip install -r requirements.txt
```

This installs:

- `streamlit`
- `pandas`
- `plotly`
- `openpyxl`

### 5) Run the app

Use Streamlit to launch:

```bash
streamlit run app.py
```

If `streamlit` is not recognized, use:

```bash
python -m streamlit run app.py
```

### 6) Open in browser

Streamlit usually opens automatically. If not, open:

- `http://localhost:8501`

---

## How to use the dashboard

1. In the sidebar, either:
   - Click **Load Default File** (uses `Dataset/OGL_Consolidated.xlsx`), or
   - Upload your own Excel/CSV file
2. Select sheet (for Excel files)
3. Select graph type
4. Choose 1–5 filter/group columns
5. (Optional) Enable:
   - **Filter Top X Records**
   - **Show Corresponding Line Items**
6. Click **Generate Graph**

---

## Important notes

- Default file button works only if this file exists:
  - `Dataset/OGL_Consolidated.xlsx`
- The app tries to auto-detect a status column using names like:
  - `SBU Developer Status`, `Developer Status`, `SBU Status`, `Status`
- For best results, keep column headers clean and avoid fully empty rows/columns.

---

## Troubleshooting

### Error: `ModuleNotFoundError`

You are likely using a different Python environment.

Fix:

```bash
pip install -r requirements.txt
python -m streamlit run app.py
```

(Ensure your virtual environment is activated first.)

### App runs but default file does not load

Check that this path exists exactly:

- `Dataset/OGL_Consolidated.xlsx`

### `streamlit` command not found

Use:

```bash
python -m streamlit run app.py
```

### Wrong Python being used

Check interpreter path:

```bash
python -c "import sys; print(sys.executable)"
```

It should point to your project virtual environment (for example, `.venv`).

---

## Stop the app

In terminal, press:

- `Ctrl + C`

---

## Quick start (copy/paste)

**Windows PowerShell:**

```powershell
cd "d:\Projects\D - OGL Dashboard"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run app.py
```

**macOS/Linux:**

```bash
cd "/path/to/D - OGL Dashboard"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```
