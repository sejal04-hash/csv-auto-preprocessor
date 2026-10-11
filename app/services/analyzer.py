import pandas as pd
import numpy as np


def analyze_data(file_path: str):

    # READ DATASET

    df = pd.read_csv(file_path)

    rows, columns = df.shape

    # DATA TYPE DETECTION

    numerical_columns = (
        df.select_dtypes(include=np.number)
        .columns
        .tolist()
    )

    categorical_columns = (
        df.select_dtypes(
            include=["object", "category"]
        )
        .columns
        .tolist()
    )

    datetime_columns = []

    # Only try columns whose names suggest dates
    date_keywords = [
        "date",
        "time",
        "timestamp",
        "datetime",
        "dob",
        "birth",
        "created",
        "updated"
    ]

    for col in categorical_columns:

        column_name = col.lower()

        looks_like_date = any(
            keyword in column_name
            for keyword in date_keywords
        )

        if not looks_like_date:
            continue

        try:

            converted = pd.to_datetime(
                df[col],
                errors="coerce"
            )

            valid_ratio = converted.notna().mean()

            if valid_ratio >= 0.8:
                datetime_columns.append(col)

        except Exception:
            pass

    # Remove datetime columns from categorical
    categorical_columns = [
        col
        for col in categorical_columns
        if col not in datetime_columns
    ]

    # =========================================
    # MISSING VALUE DETECTION
    # =========================================

    missing = df.isnull().sum()

    missing_columns = {
        column: int(value)
        for column, value in missing.items()
        if value > 0
    }

    total_missing = int(
        missing.sum()
    )

    # =========================================
    # DUPLICATE DETECTION
    # =========================================

    duplicates = int(
        df.duplicated().sum()
    )

    # =========================================
    # UNIQUE VALUE DETECTION
    # =========================================

    unique_values = {
        column: int(
            df[column].nunique(
                dropna=True
            )
        )
        for column in df.columns
    }

    # =========================================
    # CONSTANT COLUMN DETECTION
    # =========================================

    constant_columns = [
        column
        for column in df.columns
        if df[column].nunique(
            dropna=False
        ) <= 1
    ]

    # =========================================
    # POTENTIAL ID COLUMN DETECTION
    # =========================================

    id_columns = []

    for column in df.columns:

        unique_ratio = (
            df[column].nunique(
                dropna=True
            )
            / max(rows, 1)
        )

        name = column.lower()

        if (
            unique_ratio > 0.95
            and (
                "id" in name
                or "index" in name
                or name in ["id", "uuid"]
            )
        ):

            id_columns.append(column)

    # =========================================
    # BASIC STATISTICS
    # =========================================

    statistics = {}

    if len(numerical_columns) > 0:

        statistics = (
            df[numerical_columns]
            .describe()
            .replace({np.nan: None})
            .to_dict()
        )

    # =========================================
    # OUTLIER DETECTION
    # IQR METHOD
    # =========================================

    outliers = {}

    for column in numerical_columns:

        series = df[column].dropna()

        if len(series) < 4:
            continue

        q1 = series.quantile(0.25)

        q3 = series.quantile(0.75)

        iqr = q3 - q1

        # Avoid division / boundary issues
        # for constant numerical columns
        if iqr == 0:
            continue

        lower = q1 - 1.5 * iqr

        upper = q3 + 1.5 * iqr

        count = int(
            (
                (series < lower)
                |
                (series > upper)
            ).sum()
        )

        if count > 0:

            outliers[column] = count

    total_outliers = int(
        sum(outliers.values())
    )

    # =========================================
    # POTENTIAL TARGET COLUMN
    # =========================================

    target_columns = []

    common_target = [
        "target",
        "label",
        "class",
        "output",
        "y",
        "survived",
        "price",
        "churn"
    ]

    for column in df.columns:

        if column.lower() in common_target:

            target_columns.append(column)

    # =========================================
    # FINAL RESULT
    # =========================================

    return {

        "shape": {

            "rows": int(rows),

            "columns": int(columns)
        },

        "columns": df.columns.tolist(),

        "data_types": {

            column: str(dtype)

            for column, dtype
            in df.dtypes.items()
        },

        "column_types": {

            "numerical": numerical_columns,

            "categorical": categorical_columns,

            "datetime": datetime_columns
        },

        "missing_values": {

            "total": total_missing,

            "columns": missing_columns
        },

        "duplicates": duplicates,

        "unique_values": unique_values,

        "constant_columns": constant_columns,

        "potential_id_columns": id_columns,

        "potential_target_columns": target_columns,

        "statistics": statistics,

        "outliers": {

            "total": total_outliers,

            "columns": outliers
        }
    }