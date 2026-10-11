from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from pathlib import Path
import shutil
import uuid
import pandas as pd
from sklearn.model_selection import train_test_split

from app.services.analyzer import analyze_data
from app.services.health import calculate_health
from app.services.perprocessor import DataPreprocessor
from app.schemas import PreprocessingConfig


# =========================================================
# APP
# =========================================================

app = FastAPI(
    title="Auto CSV Preprocessor",
    description="Automatic CSV dataset analysis and preprocessing API",
    version="1.0.0"
)


# =========================================================
# CORS
# =========================================================
# The frontend is served by the same FastAPI server, so CORS is
# not required for normal public deployment. Keeping this enabled
# also allows local development from another frontend origin.

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# DIRECTORIES
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent

UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "outputs"
FRONTEND_DIR = BASE_DIR / "frontend"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# API HEALTH
# =========================================================

@app.get("/api/health")
def api_health():
    return {
        "status": "running",
        "service": "Auto CSV Preprocessor"
    }


# =========================================================
# UPLOAD CSV
# =========================================================

@app.post("/upload")
async def upload_csv(file: UploadFile = File(...)):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected."
        )

    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported."
        )

    file_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{file_id}.csv"

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        analysis = analyze_data(str(file_path))
        health = calculate_health(analysis)

    except Exception as e:
        file_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=400,
            detail=f"Could not process CSV: {str(e)}"
        )

    return {
        "status": "success",
        "file_id": file_id,
        "filename": file.filename,
        "analysis": analysis,
        "health": health
    }


# =========================================================
# PREPROCESS CSV
# =========================================================

@app.post("/preprocess/{file_id}")
async def preprocess_csv(
    file_id: str,
    config: PreprocessingConfig
):

    file_path = UPLOAD_DIR / f"{file_id}.csv"

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="CSV file not found."
        )

    try:
        # -----------------------------------------------------
        # READ DATA
        # -----------------------------------------------------

        df = pd.read_csv(file_path)

        rows_before = len(df)
        columns_before = len(df.columns)
        missing_before = int(df.isnull().sum().sum())
        duplicates_before = int(df.duplicated().sum())

        # -----------------------------------------------------
        # TARGET VALIDATION + SEPARATION
        # -----------------------------------------------------

        target_column = config.target_column

        if target_column:
            if target_column not in df.columns:
                raise HTTPException(
                    status_code=400,
                    detail=f"Target column '{target_column}' not found in dataset."
                )

            y = df[target_column].copy()
            X = df.drop(columns=[target_column]).copy()

        else:
            X = df.copy()
            y = None

        # -----------------------------------------------------
        # PREPROCESS FEATURES
        # -----------------------------------------------------

        settings = config.model_dump()

        processor = DataPreprocessor(settings)

        X_processed = processor.transform(X.copy())

        # -----------------------------------------------------
        # REATTACH TARGET
        # -----------------------------------------------------

        if y is not None:
            # Important: preprocessing may remove rows.
            y = y.loc[X_processed.index]

            final_df = X_processed.copy()
            final_df[target_column] = y

        else:
            final_df = X_processed.copy()

        # -----------------------------------------------------
        # TRAIN / TEST SPLIT
        # -----------------------------------------------------

        train_path = None
        test_path = None
        split_summary = None

        if (
            y is not None
            and 0 < config.test_size < 1
        ):

            y_final = final_df[target_column]
            X_final = final_df.drop(columns=[target_column])

            stratify_value = None

            if config.stratify:
                value_counts = y_final.value_counts()

                # Stratification requires more than one class and
                # at least two samples in every class.
                if (
                    len(value_counts) > 1
                    and value_counts.min() >= 2
                ):
                    stratify_value = y_final

            X_train, X_test, y_train, y_test = train_test_split(
                X_final,
                y_final,
                test_size=config.test_size,
                random_state=config.random_state,
                stratify=stratify_value
            )

            # -------------------------------------------------
            # SAVE TRAIN
            # -------------------------------------------------

            train_df = X_train.copy()
            train_df[target_column] = y_train

            train_path = OUTPUT_DIR / f"{file_id}_train.csv"

            train_df.to_csv(
                train_path,
                index=False
            )

            # -------------------------------------------------
            # SAVE TEST
            # -------------------------------------------------

            test_df = X_test.copy()
            test_df[target_column] = y_test

            test_path = OUTPUT_DIR / f"{file_id}_test.csv"

            test_df.to_csv(
                test_path,
                index=False
            )

            split_summary = {
                "enabled": True,
                "test_size": config.test_size,
                "random_state": config.random_state,
                "stratified": stratify_value is not None,
                "train_rows": len(train_df),
                "test_rows": len(test_df)
            }

        # -----------------------------------------------------
        # SAVE COMPLETE PROCESSED DATASET
        # -----------------------------------------------------

        output_path = OUTPUT_DIR / f"{file_id}_processed.csv"

        final_df.to_csv(
            output_path,
            index=False
        )

        # -----------------------------------------------------
        # AFTER STATISTICS
        # -----------------------------------------------------

        rows_after = len(final_df)
        columns_after = len(final_df.columns)
        missing_after = int(final_df.isnull().sum().sum())
        duplicates_after = int(final_df.duplicated().sum())

        # -----------------------------------------------------
        # AFTER HEALTH
        # -----------------------------------------------------

        after_analysis = analyze_data(str(output_path))
        after_health = calculate_health(after_analysis)

        # -----------------------------------------------------
        # RESPONSE
        # -----------------------------------------------------

        return {
            "status": "success",
            "file_id": file_id,

            "target": {
                "selected": target_column,
                "target_separated": target_column is not None
            },

            "before": {
                "rows": rows_before,
                "columns": columns_before,
                "missing_values": missing_before,
                "duplicates": duplicates_before
            },

            "after": {
                "rows": rows_after,
                "columns": columns_after,
                "missing_values": missing_after,
                "duplicates": duplicates_after
            },

            "health": {
                "score": after_health["score"],
                "status": after_health["status"]
            },

            "operations": processor.operations,

            "train_test_split": split_summary,

            "files": {
                "processed": f"/download/{file_id}",
                "train": (
                    f"/download/train/{file_id}"
                    if train_path else None
                ),
                "test": (
                    f"/download/test/{file_id}"
                    if test_path else None
                )
            }
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Preprocessing failed: {str(e)}"
        )


# =========================================================
# DOWNLOAD PROCESSED
# =========================================================

@app.get("/download/{file_id}")
async def download_file(file_id: str):

    output_path = OUTPUT_DIR / f"{file_id}_processed.csv"

    if not output_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Processed file not found."
        )

    return FileResponse(
        path=str(output_path),
        filename="processed.csv",
        media_type="text/csv"
    )


# =========================================================
# DOWNLOAD TRAIN
# =========================================================

@app.get("/download/train/{file_id}")
async def download_train(file_id: str):

    path = OUTPUT_DIR / f"{file_id}_train.csv"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Training file not found."
        )

    return FileResponse(
        path=str(path),
        filename="train_processed.csv",
        media_type="text/csv"
    )


# =========================================================
# DOWNLOAD TEST
# =========================================================

@app.get("/download/test/{file_id}")
async def download_test(file_id: str):

    path = OUTPUT_DIR / f"{file_id}_test.csv"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="Testing file not found."
        )

    return FileResponse(
        path=str(path),
        filename="test_processed.csv",
        media_type="text/csv"
    )


# =========================================================
# FRONTEND
# =========================================================
# IMPORTANT:
# Keep this LAST.
#
# FastAPI will serve:
#   /
#   /index.html
#   /script.js
#   /style.css
#
# API routes above are registered before this mount.

if not FRONTEND_DIR.exists():
    raise RuntimeError(
        f"Frontend directory not found: {FRONTEND_DIR}"
    )

app.mount(
    "/",
    StaticFiles(
        directory=str(FRONTEND_DIR),
        html=True
    ),
    name="frontend"
)
