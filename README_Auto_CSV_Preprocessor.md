# Auto CSV Preprocessor

A web-based CSV analysis and preprocessing tool built with **FastAPI, Python, Pandas, NumPy, and scikit-learn**, with a simple HTML/CSS/JavaScript frontend. Upload a CSV file, review dataset-quality information, configure preprocessing, and download the processed dataset and (when a target column is selected) train/test splits.

## Features

- Upload CSV files and validate file type.
- Analyze dataset dimensions, column types, missing values, duplicate rows, unique values, and constant columns.
- Display a dataset health score and analysis summary.
- Configure missing-value handling, duplicate removal, outlier handling, categorical encoding, and numerical scaling.
- Optionally select a target column and create train/test datasets with a configurable test size, random state, and stratification setting.
- Download the processed CSV and available train/test CSV files.
- FastAPI endpoints and interactive API documentation.

> **Note:** Preprocessing choices can change your dataset. Review the configuration and inspect the output before using it for model training. This project is intended as a development/learning tool, not as a guarantee that every dataset is automatically ML-ready.

## Tech Stack

- Python
- FastAPI and Uvicorn
- Pandas and NumPy
- scikit-learn
- HTML, CSS, JavaScript

## Project Structure

```text
csv_auto_perprocessing/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── services/
│   │   ├── analyzer.py
│   │   ├── health.py
│   │   └── perprocessor.py
│   └── utils/
│       └── file_handler.py
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
├── uploads/       # created at runtime; not committed
├── outputs/       # created at runtime; not committed
├── requirements.txt
├── .gitignore
└── README.md
```

## Setup and Run

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/csv-auto-preprocessor.git
cd csv-auto-preprocessor
```

Replace `YOUR-USERNAME` with your GitHub username and use the repository URL you create.

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can use Command Prompt and run `.venv\Scripts\activate.bat`, or use `python -m pip` with the environment's Python executable.

**macOS/Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Start the API and frontend

Run this command from the project root (the directory containing `app/` and `frontend/`):

```bash
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000** in your browser. API documentation is available at **http://127.0.0.1:8000/docs** and the health endpoint at **http://127.0.0.1:8000/api/health**.

## Main API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/health` | Check whether the API is running |
| `POST` | `/upload` | Upload and analyze a CSV file |
| `POST` | `/preprocess/{file_id}` | Preprocess an uploaded dataset using the supplied configuration |
| `GET` | `/download/{file_id}` | Download the processed CSV |
| `GET` | `/download/train/{file_id}` | Download the training split, when generated |
| `GET` | `/download/test/{file_id}` | Download the test split, when generated |

Use `/docs` to view request schemas and try the endpoints interactively.

## GitHub Upload

1. Create a **new empty repository** on GitHub, for example `csv-auto-preprocessor`. Do not initialize it with a README if you already have this project locally.
2. Open a terminal in the project root.
3. Run:

```bash
git init
git add .
git commit -m "Initial commit: Auto CSV Preprocessor"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/csv-auto-preprocessor.git
git push -u origin main
```

Replace the remote URL with your own repository URL. If Git asks you to sign in, complete the browser authentication flow. Do not commit credentials, private datasets, or personally identifiable data.

## Limitations and Responsible Use

- CSV files can contain sensitive data. Use sample or anonymized data when testing and do not upload confidential datasets to a public deployment.
- Review preprocessing choices and the output before model training; the best strategy depends on the dataset and task.
- Large files may require additional upload limits, validation, and resource controls before deployment.

## Future Improvements

- Add automated tests and example datasets that contain no sensitive information.
- Add clearer validation messages and configurable file-size limits.
- Add deployment configuration and a hosted demo.

## Author

**Your Name** — replace this with your name and add your GitHub/LinkedIn profile links if desired.
