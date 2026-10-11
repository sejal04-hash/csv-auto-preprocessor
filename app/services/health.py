def calculate_health(analysis):

    rows = analysis["shape"]["rows"]
    columns = analysis["shape"]["columns"]

    score = 100

    reasons = []
    recommendations = []

    # --------------------------------
    # Missing values
    # --------------------------------

    missing = analysis["missing_values"]["total"]

    total_cells = rows * columns

    missing_ratio = (
        missing / total_cells
        if total_cells > 0
        else 0
    )

    if missing_ratio > 0.30:

        score -= 30
        reasons.append(
            "More than 30% of the dataset contains missing values."
        )

        recommendations.append(
            "Consider removing or imputing missing values."
        )

    elif missing_ratio > 0.10:

        score -= 20
        reasons.append(
            "Dataset contains a significant amount of missing data."
        )

        recommendations.append(
            "Apply an appropriate missing-value strategy."
        )

    elif missing_ratio > 0:

        score -= 10
        reasons.append(
            "Some missing values are present."
        )

        recommendations.append(
            "Consider imputing missing values."
        )

    # --------------------------------
    # Duplicates
    # --------------------------------

    duplicates = analysis["duplicates"]

    duplicate_ratio = (
        duplicates / rows
        if rows > 0
        else 0
    )

    if duplicate_ratio > 0.10:

        score -= 15

        reasons.append(
            "More than 10% of rows are duplicates."
        )

        recommendations.append(
            "Consider removing duplicate rows."
        )

    elif duplicates > 0:

        score -= 5

        reasons.append(
            f"{duplicates} duplicate rows were detected."
        )

        recommendations.append(
            "Review duplicate rows."
        )

    # --------------------------------
    # Constant columns
    # --------------------------------

    constant_columns = analysis["constant_columns"]

    if constant_columns:

        score -= min(
            15,
            len(constant_columns) * 5
        )

        reasons.append(
            "Constant columns were detected."
        )

        recommendations.append(
            "Remove columns with no variation."
        )

    # --------------------------------
    # Outliers
    # --------------------------------

    outliers = analysis["outliers"]["total"]

    if rows > 0:

        outlier_ratio = outliers / rows

        if outlier_ratio > 0.20:

            score -= 15

            reasons.append(
                "A high number of potential outliers were detected."
            )

            recommendations.append(
                "Investigate outliers using IQR or another method."
            )

        elif outliers > 0:

            score -= 5

            reasons.append(
                "Potential outliers were detected."
            )

            recommendations.append(
                "Review numerical outliers."
            )

    # --------------------------------
    # Small dataset
    # --------------------------------

    if rows < 100:

        score -= 10

        reasons.append(
            "Dataset contains fewer than 100 rows."
        )

        recommendations.append(
            "Consider collecting more data before training complex models."
        )

    # --------------------------------
    # Final score
    # --------------------------------

    score = max(0, min(100, score))

    if score >= 90:
        status = "Excellent"
    elif score >= 75:
        status = "Good"
    elif score >= 50:
        status = "Needs Cleaning"
    elif score >= 25:
        status = "Poor"
    else:
        status = "Critical"

    return {

        "score": score,

        "status": status,

        "missing_ratio": round(
            missing_ratio * 100,
            2
        ),

        "reasons": reasons,

        "recommendations": recommendations
    }