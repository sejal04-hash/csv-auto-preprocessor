import pandas as pd
import numpy as np

from sklearn.preprocessing import (
    StandardScaler,
    MinMaxScaler,
    LabelEncoder,
    OrdinalEncoder,
    RobustScaler
)


class DataPreprocessor:

    def __init__(self, config):

        self.config = config

        self.operations = []

    # ==================================================
    # MISSING VALUE - SINGLE COLUMN
    # ==================================================

    def fill_column(self, df, column, strategy, constant=None):

        if column not in df.columns:
            return df

        missing_before = int(
            df[column].isnull().sum()
        )

        if missing_before == 0:
            return df

        # ----------------------------------------------
        # DROP
        # ----------------------------------------------

        if strategy == "drop":

            df = df.dropna(
                subset=[column]
            )

        # ----------------------------------------------
        # MEAN
        # ----------------------------------------------

        elif strategy == "mean":

            if not pd.api.types.is_numeric_dtype(
                df[column]
            ):
                raise ValueError(
                    f"Mean cannot be used for "
                    f"non-numeric column '{column}'"
                )

            value = df[column].mean()

            df[column] = df[column].fillna(value)

        # ----------------------------------------------
        # MEDIAN
        # ----------------------------------------------

        elif strategy == "median":

            if not pd.api.types.is_numeric_dtype(
                df[column]
            ):
                raise ValueError(
                    f"Median cannot be used for "
                    f"non-numeric column '{column}'"
                )

            value = df[column].median()

            df[column] = df[column].fillna(value)

        # ----------------------------------------------
        # MODE
        # ----------------------------------------------

        elif strategy == "mode":

            mode = df[column].mode()

            if not mode.empty:

                df[column] = df[column].fillna(
                    mode.iloc[0]
                )

        # ----------------------------------------------
        # CONSTANT
        # ----------------------------------------------

        elif strategy == "constant":

            if constant is None:
                constant = 0

            df[column] = df[column].fillna(
                constant
            )

        # ----------------------------------------------
        # NONE
        # ----------------------------------------------

        elif strategy == "none":

            return df

        else:

            raise ValueError(
                f"Invalid strategy '{strategy}' "
                f"for column '{column}'"
            )

        missing_after = int(
            df[column].isnull().sum()
        )

        self.operations.append({

            "operation": "missing_value",

            "column": column,

            "strategy": strategy,

            "missing_before": missing_before,

            "missing_after": missing_after,

            "filled": missing_before - missing_after
        })

        return df

    # ==================================================
    # AUTO STRATEGY
    # ==================================================

    def get_auto_strategy(self, df, column):

        series = df[column]

        # ----------------------------------------------
        # Categorical
        # ----------------------------------------------

        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_categorical_dtype(series)
        ):

            return {
                "strategy": "mode",
                "reason": "Categorical column"
            }

        # ----------------------------------------------
        # Numeric
        # ----------------------------------------------

        if pd.api.types.is_numeric_dtype(series):

            clean = series.dropna()

            if len(clean) == 0:

                return {
                    "strategy": "constant",
                    "reason": "Column contains only missing values"
                }

            # Check skewness
            skewness = clean.skew()

            # Check IQR outliers
            q1 = clean.quantile(0.25)
            q3 = clean.quantile(0.75)

            iqr = q3 - q1

            if iqr == 0:

                outlier_ratio = 0

            else:

                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr

                outliers = (
                    (clean < lower)
                    |
                    (clean > upper)
                )

                outlier_ratio = (
                    outliers.sum()
                    / len(clean)
                )

            # ------------------------------------------
            # High skew / many outliers
            # → Median
            # ------------------------------------------

            if (
                abs(skewness) > 1
                or outlier_ratio > 0.05
            ):

                return {
                    "strategy": "median",
                    "reason": (
                        "Numerical column has "
                        "high skewness or outliers"
                    )
                }

            # ------------------------------------------
            # Approximately normal
            # → Mean
            # ------------------------------------------

            return {
                "strategy": "mean",
                "reason": (
                    "Numerical column has "
                    "low skewness and few outliers"
                )
            }

        # ----------------------------------------------
        # Unknown datatype
        # ----------------------------------------------

        return {
            "strategy": "mode",
            "reason": "Fallback strategy"
        }

    # ==================================================
    # MISSING VALUE HANDLER
    # ==================================================

    def handle_missing(self, df):

        strategy = self.config.get(
            "missing_value_strategy",
            "none"
        )

        # ----------------------------------------------
        # NONE
        # ----------------------------------------------

        if strategy == "none":

            return df

        total_before = int(
            df.isnull().sum().sum()
        )

        # =================================================
        # GLOBAL STRATEGIES
        # =================================================

        if strategy in [
            "drop",
            "mean",
            "median",
            "mode",
            "constant"
        ]:

            if strategy == "drop":

                before = len(df)

                df = df.dropna()

                self.operations.append({

                    "operation": "missing_values",

                    "strategy": "drop",

                    "rows_removed": (
                        before - len(df)
                    )
                })

                return df

            # Apply strategy column by column
            for column in df.columns:

                constant = (
                    self.config
                    .get(
                        "missing_value_constant",
                        0
                    )
                )

                self.fill_column(
                    df,
                    column,
                    strategy,
                    constant
                )

            return df

        # =================================================
        # AUTO
        # =================================================

        if strategy == "auto":

            for column in df.columns:

                if df[column].isnull().any():

                    recommendation = (
                        self.get_auto_strategy(
                            df,
                            column
                        )
                    )

                    selected_strategy = (
                        recommendation["strategy"]
                    )

                    constant = None

                    if selected_strategy == "constant":

                        constant = 0

                    self.fill_column(
                        df,
                        column,
                        selected_strategy,
                        constant
                    )

                    self.operations.append({

                        "operation":
                            "auto_recommendation",

                        "column": column,

                        "recommended_strategy":
                            selected_strategy,

                        "reason":
                            recommendation["reason"]
                    })

            return df

        # =================================================
        # CUSTOM / HYBRID
        # =================================================

        if strategy == "custom":

            custom_columns = self.config.get(
                "missing_value_columns",
                {}
            )

            constants = self.config.get(
                "missing_value_constants",
                {}
            )

            for column, selected_strategy in (
                custom_columns.items()
            ):

                if column not in df.columns:
                    continue

                constant = constants.get(
                    column,
                    0
                )

                self.fill_column(
                    df,
                    column,
                    selected_strategy,
                    constant
                )

            return df

        # =================================================
        # INVALID
        # =================================================

        raise ValueError(
            f"Invalid missing value strategy: {strategy}"
        )

    # ==================================================
    # DUPLICATES
    # ==================================================

    def handle_duplicates(self, df):

        remove = self.config.get(
            "remove_duplicates",
            False
        )

        if not remove:

            return df

        before = len(df)

        df = df.drop_duplicates()

        removed = (
            before - len(df)
        )

        self.operations.append({

            "operation": "duplicates",

            "removed": removed
        })

        return df

    # ==================================================
    # OUTLIERS
    # ==================================================

    def handle_outliers(self, df):

        method = self.config.get(
            "outlier_method",
            "none"
        )

        action = self.config.get(
            "outlier_action",
            "remove"
        )

        if method == "none":

            return df

        numeric_columns = (
            df.select_dtypes(
                include=np.number
            )
            .columns
            .tolist()
        )

        total_processed = 0

        for column in numeric_columns:

            series = df[column]

            if method == "iqr":

                q1 = series.quantile(0.25)

                q3 = series.quantile(0.75)

                iqr = q3 - q1

                if iqr == 0:
                    continue

                lower = q1 - 1.5 * iqr

                upper = q3 + 1.5 * iqr

            elif method == "zscore":

                mean = series.mean()

                std = series.std()

                if (
                    std == 0
                    or pd.isna(std)
                ):
                    continue

                lower = mean - 3 * std

                upper = mean + 3 * std

            else:

                raise ValueError(
                    f"Invalid outlier method: {method}"
                )

            mask = (
                (df[column] < lower)
                |
                (df[column] > upper)
            )

            count = int(
                mask.sum()
            )

            total_processed += count

            if action == "remove":

                df = df.loc[
                    ~mask
                ].copy()

            elif action == "cap":

                df[column] = (
                    df[column]
                    .clip(
                        lower=lower,
                        upper=upper
                    )
                )

            else:

                raise ValueError(
                    f"Invalid outlier action: {action}"
                )

        self.operations.append({

            "operation": "outliers",

            "method": method,

            "action": action,

            "processed": total_processed
        })

        return df

    # ==================================================
    # CATEGORICAL ENCODING
    # ==================================================

    def encode_categorical(self, df):

        method = self.config.get(
            "encoding",
            "none"
        )

        if method == "none":

            return df

        categorical_columns = (
            df.select_dtypes(
                include=[
                    "object",
                    "category"
                ]
            )
            .columns
            .tolist()
        )

        if not categorical_columns:

            return df

        if method == "one_hot":

            df = pd.get_dummies(
                df,
                columns=categorical_columns,
                drop_first=False,
                dtype=int
            )

        elif method == "label":

            for column in categorical_columns:

                encoder = LabelEncoder()

                df[column] = (
                    encoder.fit_transform(
                        df[column].astype(str)
                    )
                )

        elif method == "ordinal":

            encoder = OrdinalEncoder()

            df[categorical_columns] = (
                encoder.fit_transform(
                    df[categorical_columns]
                )
            )

        else:

            raise ValueError(
                f"Invalid encoding method: {method}"
            )

        self.operations.append({

            "operation": "encoding",

            "method": method,

            "columns": categorical_columns
        })

        return df

    # ==================================================
    # SCALING
    # ==================================================

    def scale_numeric(self, df):

        method = self.config.get(
            "scaling",
            "none"
        )

        if method == "none":

            return df

        numeric_columns = (
            df.select_dtypes(
                include=np.number
            )
            .columns
            .tolist()
        )

        if not numeric_columns:

            return df

        if method == "standard":

            scaler = StandardScaler()

        elif method == "minmax":

            scaler = MinMaxScaler()

        elif method == "robust":

            scaler = RobustScaler()

        else:

            raise ValueError(
                f"Invalid scaling method: {method}"
            )

        df[numeric_columns] = (
            scaler.fit_transform(
                df[numeric_columns]
            )
        )

        self.operations.append({

            "operation": "scaling",

            "method": method,

            "columns": numeric_columns
        })

        return df

    # ==================================================
    # MAIN PIPELINE
    # ==================================================

    def transform(self, df):

        # 1. Missing values
        df = self.handle_missing(df)

        # 2. Duplicates
        df = self.handle_duplicates(df)

        # 3. Outliers
        df = self.handle_outliers(df)

        # 4. Encoding
        df = self.encode_categorical(df)

        # 5. Scaling
        df = self.scale_numeric(df)

        return df