
const API_URL = "";

let fileId = null;
let datasetAnalysis = null;


// ===================================
// File Selection
// ===================================

document
    .getElementById("csvFile")
    .addEventListener("change", function () {

        const file = this.files[0];

        if (file) {
            document.getElementById("fileName").textContent =
                file.name;
        }
    });


// ===================================
// Upload CSV
// ===================================

async function uploadCSV() {

    const fileInput =
        document.getElementById("csvFile");

    if (!fileInput.files.length) {
        showError("Please select a CSV file first.");
        return;
    }

    const file = fileInput.files[0];

    if (!file.name.toLowerCase().endsWith(".csv")) {
        showError("Only CSV files are supported.");
        return;
    }

    const formData = new FormData();

    formData.append("file", file);

    showLoading(true);
    hideError();

    try {

        const response = await fetch(
            `${API_URL}/upload`,
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.detail || "Upload failed."
            );
        }

        // Save file UUID
        fileId = data.file_id;

        displayAnalysis(data);

    } catch (error) {

        showError(error.message);

    } finally {

        showLoading(false);
    }
}


// ===================================
// Display Analysis
// ===================================

function displayAnalysis(data) {

    const analysis = data.analysis;
    const health = data.health;

    datasetAnalysis = analysis;

    document
        .getElementById("analysisSection")
        .classList.remove("hidden");

    document
        .getElementById("preprocessSection")
        .classList.remove("hidden");

    document
        .getElementById("resultsSection")
        .classList.add("hidden");


    // Dataset stats

    document.getElementById("rows").textContent =
        analysis.shape?.rows ?? "-";

    document.getElementById("columns").textContent =
        analysis.shape?.columns ?? "-";

    document.getElementById("missing").textContent =
        analysis.missing_values?.total ?? 0;

    document.getElementById("duplicates").textContent =
        analysis.duplicates ?? 0;


    // Health score

    let score = health?.score;

    if (score === undefined) {
        score = health?.health_score;
    }

    document.getElementById("healthScore").textContent =
        score ?? "-";


    // Detected columns

    const columnsList =
        document.getElementById("columnsList");

    columnsList.innerHTML = "";

    (analysis.columns || []).forEach(column => {

        const tag =
            document.createElement("span");

        tag.className = "column-tag";

        tag.textContent = column;

        columnsList.appendChild(tag);

    });


    // Missing values table

    displayMissingValues(analysis);


    // Target columns

    const targetSelect =
        document.getElementById("targetColumn");

    targetSelect.innerHTML =
        '<option value="">Select target column</option>';

    let targetColumns =
        analysis.potential_target_columns || [];

    if (targetColumns.length === 0) {
        targetColumns =
            analysis.columns || [];
    }

    targetColumns.forEach(column => {

        const option =
            document.createElement("option");

        option.value = column;
        option.textContent = column;

        targetSelect.appendChild(option);

    });


    // Default missing strategy

    const missingStrategy =
        document.getElementById("missingStrategy");

    missingStrategy.value = "auto";

    document
        .getElementById("columnMissingConfig")
        .classList.add("hidden");

    document
        .getElementById("missingColumnControls")
        .replaceChildren();


    document
        .getElementById("analysisSection")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// ===================================
// Missing Values
// ===================================

function getMissingColumns(analysis) {

    const missing =
        analysis?.missing_values?.columns || {};

    if (
        missing &&
        typeof missing === "object" &&
        !Array.isArray(missing)
    ) {
        return missing;
    }

    return {};
}


function getColumnDataType(analysis, column) {

    return (
        analysis?.data_types?.[column] ||
        "Unknown"
    );
}


function isNumericType(dataType) {

    const type =
        String(dataType).toLowerCase();

    return (
        type.includes("int") ||
        type.includes("float") ||
        type.includes("number")
    );
}


// ===================================
// Missing Values Table
// ===================================

function displayMissingValues(analysis) {

    const tableBody =
        document.getElementById(
            "missingTableBody"
        );

    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = "";

    const missingColumns =
        getMissingColumns(analysis);

    const totalRows =
        Number(
            analysis?.shape?.rows || 0
        );


    if (
        Object.keys(missingColumns).length === 0
    ) {

        tableBody.innerHTML = `
            <tr>
                <td colspan="4" class="no-missing">
                    No missing values found.
                </td>
            </tr>
        `;

        return;
    }


    Object.entries(missingColumns).forEach(
        ([column, count]) => {

            const row =
                document.createElement("tr");

            const percentage =
                totalRows > 0
                    ? (
                        Number(count) /
                        totalRows *
                        100
                    ).toFixed(2)
                    : "0.00";

            const dataType =
                getColumnDataType(
                    analysis,
                    column
                );


            row.innerHTML = `
                <td>
                    <strong>
                        ${escapeHTML(column)}
                    </strong>
                </td>

                <td>
                    <span class="type-badge">
                        ${escapeHTML(dataType)}
                    </span>
                </td>

                <td>
                    <strong>
                        ${Number(count)}
                    </strong>
                </td>

                <td>
                    ${percentage}%
                </td>
            `;

            tableBody.appendChild(row);

        }
    );
}


// ===================================
// Column-wise Missing Configuration
// ===================================

function createMissingColumnControls() {

    const container =
        document.getElementById(
            "missingColumnControls"
        );

    if (!container) {
        return;
    }

    container.innerHTML = "";

    if (!datasetAnalysis) {
        return;
    }


    const missingColumns =
        getMissingColumns(datasetAnalysis);


    if (
        Object.keys(missingColumns).length === 0
    ) {

        container.innerHTML = `
            <p class="no-missing">
                No columns contain missing values.
            </p>
        `;

        return;
    }


    Object.entries(missingColumns).forEach(
        ([column, count]) => {

            const dataType =
                getColumnDataType(
                    datasetAnalysis,
                    column
                );


            const row =
                document.createElement("div");

            row.className =
                "missing-column-row";


            let options = `
                <option value="none">
                    Do Nothing
                </option>

                <option value="drop">
                    Drop Rows
                </option>
            `;


            // Numeric columns
            if (isNumericType(dataType)) {

                options += `
                    <option value="mean">
                        Mean
                    </option>

                    <option value="median">
                        Median
                    </option>
                `;
            }


            // Available for all columns
            options += `
                <option value="mode">
                    Mode
                </option>

                <option value="constant">
                    Constant
                </option>
            `;


            row.innerHTML = `

                <div class="missing-column-info">

                    <strong>
                        ${escapeHTML(column)}
                    </strong>

                    <span>
                        ${Number(count)}
                        missing values
                    </span>

                </div>


                <select
                    class="column-missing-select"
                    data-column="${escapeHTML(column)}"
                >

                    ${options}

                </select>

            `;


            container.appendChild(row);

        }
    );
}


// ===================================
// Missing Strategy Change
// ===================================

const missingStrategyElement =
    document.getElementById(
        "missingStrategy"
    );

if (missingStrategyElement) {

    missingStrategyElement.addEventListener(
        "change",
        function () {

            const config =
                document.getElementById(
                    "columnMissingConfig"
                );


            if (this.value === "custom") {

                config.classList.remove(
                    "hidden"
                );

                createMissingColumnControls();

            } else {

                config.classList.add(
                    "hidden"
                );
            }
        }
    );
}


// ===================================
// Preprocess Dataset
// ===================================

async function preprocessDataset() {

    if (!fileId) {

        showError(
            "Please upload and analyze a CSV first."
        );

        return;
    }


    const targetColumn =
        document.getElementById(
            "targetColumn"
        ).value;


    if (!targetColumn) {

        showError(
            "Please select a target column."
        );

        return;
    }


    const missingStrategy =
        document.getElementById(
            "missingStrategy"
        ).value;


    // Per-column strategies

    const missingColumnStrategies = {};


    if (
        missingStrategy === "custom"
    ) {

        document
            .querySelectorAll(
                ".column-missing-select"
            )
            .forEach(select => {

                const column =
                    select.dataset.column;

                missingColumnStrategies[column] =
                    select.value;

            });
    }


    const testSize =
        parseFloat(
            document.getElementById(
                "testSize"
            ).value
        );


    if (
        Number.isNaN(testSize) ||
        testSize <= 0 ||
        testSize >= 1
    ) {

        showError(
            "Test size must be between 0 and 1."
        );

        return;
    }


    const config = {

        target_column:
            targetColumn,

        missing_value_strategy:
            missingStrategy,

        missing_value_columns:
            missingColumnStrategies,

        missing_value_constants:
            {},

        remove_duplicates:
            document.getElementById(
                "duplicatesStrategy"
            ).value === "true",

        outlier_method:
            document.getElementById(
                "outlierMethod"
            ).value,

        outlier_action:
            document.getElementById(
                "outlierAction"
            ).value,

        encoding:
            document.getElementById(
                "encoding"
            ).value,

        scaling:
            document.getElementById(
                "scaling"
            ).value,

        test_size:
            testSize,

        random_state:
            42,

        stratify:
            true
    };


    showLoading(true);
    hideError();


    try {

        const response =
            await fetch(
                `${API_URL}/preprocess/${fileId}`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body:
                        JSON.stringify(config)
                }
            );


        const data =
            await response.json();


        if (!response.ok) {

            throw new Error(
                data.detail ||
                "Preprocessing failed."
            );
        }


        displayResults(data);

    } catch (error) {

        showError(error.message);

    } finally {

        showLoading(false);
    }
}


// ===================================
// Display Results
// ===================================

function displayResults(data) {

    document
        .getElementById("resultsSection")
        .classList.remove("hidden");


    document.getElementById("rowsBefore")
        .textContent =
        data.before?.rows ?? "-";


    document.getElementById("rowsAfter")
        .textContent =
        data.after?.rows ?? "-";


    document.getElementById("columnsBefore")
        .textContent =
        data.before?.columns ?? "-";


    document.getElementById("columnsAfter")
        .textContent =
        data.after?.columns ?? "-";


    displayOperations(
        data.operations || []
    );


    document
        .getElementById("resultsSection")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// ===================================
// Operations
// ===================================

function displayOperations(operations) {

    const container =
        document.getElementById(
            "operationsList"
        );

    container.innerHTML = "";


    if (
        !Array.isArray(operations) ||
        operations.length === 0
    ) {

        container.innerHTML = `
            <p class="no-missing">
                No preprocessing operations were applied.
            </p>
        `;

        return;
    }


    operations.forEach(operation => {

        const div =
            document.createElement("div");

        div.className =
            "operation";


        if (
            operation.operation ===
            "missing_value"
        ) {

            div.innerHTML = `

                <div class="operation-title">
                    Missing Values
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Column:</strong>
                        ${escapeHTML(
                operation.column ?? "-"
            )}
                    </span>

                    <span>
                        <strong>Strategy:</strong>
                        ${formatStrategy(
                operation.strategy
            )}
                    </span>

                    <span>
                        <strong>Before:</strong>
                        ${Number(
                operation.missing_before ?? 0
            )}
                    </span>

                    <span>
                        <strong>Filled:</strong>
                        ${Number(
                operation.filled ?? 0
            )}
                    </span>

                    <span>
                        <strong>After:</strong>
                        ${Number(
                operation.missing_after ?? 0
            )}
                    </span>

                </div>
            `;
        }


        else if (
            operation.operation ===
            "auto_recommendation"
        ) {

            div.innerHTML = `

                <div class="operation-title">
                    Auto Recommendation
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Column:</strong>
                        ${escapeHTML(
                operation.column ?? "-"
            )}
                    </span>

                    <span>
                        <strong>Recommended:</strong>
                        ${formatStrategy(
                operation.recommended_strategy
            )}
                    </span>

                    <span class="operation-wide">
                        <strong>Reason:</strong>
                        ${escapeHTML(
                operation.reason ?? "-"
            )}
                    </span>

                </div>
            `;
        }


        else if (
            operation.operation ===
            "outliers"
        ) {

            div.innerHTML = `

                <div class="operation-title">
                    Outlier Treatment
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Method:</strong>
                        ${formatStrategy(
                operation.method
            )}
                    </span>

                    <span>
                        <strong>Action:</strong>
                        ${formatStrategy(
                operation.action
            )}
                    </span>

                    <span>
                        <strong>Processed:</strong>
                        ${Number(
                operation.processed ?? 0
            )}
                    </span>

                </div>
            `;
        }


        else if (
            operation.operation ===
            "encoding"
        ) {

            const columns =
                Array.isArray(operation.columns)
                    ? operation.columns.join(", ")
                    : "-";


            div.innerHTML = `

                <div class="operation-title">
                    Categorical Encoding
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Method:</strong>
                        ${formatStrategy(
                operation.method
            )}
                    </span>

                    <span class="operation-wide">
                        <strong>Columns:</strong>
                        ${escapeHTML(columns)}
                    </span>

                </div>
            `;
        }


        else if (
            operation.operation ===
            "scaling"
        ) {

            const columns =
                Array.isArray(operation.columns)
                    ? operation.columns
                    : [];


            div.innerHTML = `

                <div class="operation-title">
                    Feature Scaling
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Method:</strong>
                        ${formatStrategy(
                operation.method
            )}
                    </span>

                    <span>
                        <strong>Columns:</strong>
                        ${columns.length}
                    </span>

                </div>
            `;
        }


        else if (
            operation.operation ===
            "duplicates"
        ) {

            div.innerHTML = `

                <div class="operation-title">
                    Duplicate Records
                </div>

                <div class="operation-details">

                    <span>
                        <strong>Action:</strong>
                        ${escapeHTML(
                operation.action ??
                "Processed"
            )}
                    </span>

                    <span>
                        <strong>Removed:</strong>
                        ${Number(
                operation.removed ??
                operation.processed ??
                0
            )}
                    </span>

                </div>
            `;
        }


        else {

            div.innerHTML = `

                <div class="operation-title">
                    ${escapeHTML(
                formatStrategy(
                    operation.operation ||
                    "Operation"
                )
            )}
                </div>

                <div class="operation-details">
                    <span>
                        Operation applied successfully.
                    </span>
                </div>
            `;
        }


        container.appendChild(div);

    });
}


// ===================================
// Formatting Helpers
// ===================================

function formatStrategy(value) {

    if (
        value === null ||
        value === undefined ||
        value === ""
    ) {
        return "-";
    }

    return String(value)
        .replace(/_/g, " ")
        .replace(/\b\w/g, char =>
            char.toUpperCase()
        );
}


function escapeHTML(value) {

    return String(value ?? "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}


// ===================================
// DOWNLOAD FUNCTIONS
// ===================================

async function downloadFile(
    url,
    filename
) {

    if (!fileId) {

        showError(
            "Please preprocess the dataset first."
        );

        return;
    }


    showLoading(true);
    hideError();


    try {

        const response =
            await fetch(url, {
                method: "GET"
            });


        if (!response.ok) {

            let message =
                "Download failed.";

            try {

                const errorData =
                    await response.json();

                message =
                    errorData.detail ||
                    message;

            } catch {

                // Response was not JSON.
            }

            throw new Error(message);
        }


        // Convert response to CSV Blob

        const blob =
            await response.blob();


        // Create temporary browser URL

        const blobUrl =
            window.URL.createObjectURL(blob);


        // Create download link

        const link =
            document.createElement("a");

        link.href = blobUrl;

        link.download = filename;

        document.body.appendChild(link);

        link.click();

        link.remove();


        // Clean temporary URL

        window.URL.revokeObjectURL(
            blobUrl
        );


    } catch (error) {

        console.error(
            "Download error:",
            error
        );

        showError(
            error.message ||
            "Unable to download file."
        );

    } finally {

        showLoading(false);
    }
}


// ===================================
// Download Processed
// ===================================

function downloadProcessed() {

    if (!fileId) {

        showError(
            "Please preprocess the dataset first."
        );

        return;
    }


    downloadFile(
        `${API_URL}/download/${fileId}`,
        "processed.csv"
    );
}


// ===================================
// Download Train
// ===================================

function downloadTrain() {

    if (!fileId) {

        showError(
            "Please preprocess the dataset first."
        );

        return;
    }


    downloadFile(
        `${API_URL}/download/train/${fileId}`,
        "train.csv"
    );
}


// ===================================
// Download Test
// ===================================

function downloadTest() {

    if (!fileId) {

        showError(
            "Please preprocess the dataset first."
        );

        return;
    }


    downloadFile(
        `${API_URL}/download/test/${fileId}`,
        "test.csv"
    );
}


// ===================================
// Loading
// ===================================

function showLoading(show) {

    const loading =
        document.getElementById("loading");

    if (!loading) {
        return;
    }


    if (show) {

        loading.classList.remove(
            "hidden"
        );

    } else {

        loading.classList.add(
            "hidden"
        );
    }
}


// ===================================
// Error
// ===================================

function showError(message) {

    const error =
        document.getElementById("error");

    if (!error) {
        return;
    }


    error.textContent =
        message;


    error.classList.remove(
        "hidden"
    );


    error.scrollIntoView({
        behavior: "smooth",
        block: "center"
    });
}


function hideError() {

    const error =
        document.getElementById("error");

    if (!error) {
        return;
    }


    error.classList.add(
        "hidden"
    );
}