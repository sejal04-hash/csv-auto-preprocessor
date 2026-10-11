const API_URL = "http://127.0.0.1:8000";

let fileId = null;


// -----------------------------------
// File Selection
// -----------------------------------

document
    .getElementById("csvFile")
    .addEventListener("change", function () {

        const file = this.files[0];

        if (file) {
            document.getElementById("fileName").textContent =
                file.name;
        }

    });


// -----------------------------------
// Upload CSV
// -----------------------------------

async function uploadCSV() {

    const fileInput = document.getElementById("csvFile");

    if (!fileInput.files.length) {
        showError("Please select a CSV file first.");
        return;
    }

    const file = fileInput.files[0];

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
                data.detail || "Upload failed"
            );
        }

        // Save UUID
        fileId = data.file_id;

        displayAnalysis(data);

    } catch (error) {

        showError(error.message);

    } finally {

        showLoading(false);

    }
}


// -----------------------------------
// Display Analysis
// -----------------------------------

function displayAnalysis(data) {

    const analysis = data.analysis;
    const health = data.health;

    document
        .getElementById("analysisSection")
        .classList.remove("hidden");

    document
        .getElementById("preprocessSection")
        .classList.remove("hidden");


    // Dataset stats

    document.getElementById("rows").textContent =
        analysis.shape.rows;

    document.getElementById("columns").textContent =
        analysis.shape.columns;

    document.getElementById("missing").textContent =
        analysis.missing_values.total;

    document.getElementById("duplicates").textContent =
        analysis.duplicates;


    // Health

    let score = health.score;

    if (score === undefined) {
        score = health.health_score;
    }

    document.getElementById("healthScore").textContent =
        score ?? "-";


    // Columns

    const columnsList =
        document.getElementById("columnsList");

    columnsList.innerHTML = "";


    analysis.columns.forEach(column => {

        const tag = document.createElement("span");

        tag.className = "column-tag";

        tag.textContent = column;

        columnsList.appendChild(tag);

    });


    // Target columns

    const targetSelect =
        document.getElementById("targetColumn");

    targetSelect.innerHTML =
        '<option value="">Select target column</option>';


    let targetColumns =
        analysis.potential_target_columns || [];


    if (targetColumns.length === 0) {
        targetColumns = analysis.columns;
    }


    targetColumns.forEach(column => {

        const option =
            document.createElement("option");

        option.value = column;
        option.textContent = column;

        targetSelect.appendChild(option);

    });


    // Scroll

    document
        .getElementById("analysisSection")
        .scrollIntoView({
            behavior: "smooth"
        });
}


// -----------------------------------
// Preprocess Dataset
// -----------------------------------

async function preprocessDataset() {

    if (!fileId) {
        showError("Please upload and analyze a CSV first.");
        return;
    }


    const targetColumn =
        document.getElementById("targetColumn").value;


    if (!targetColumn) {
        showError("Please select a target column.");
        return;
    }


    const config = {

        target_column: targetColumn,

        missing_value_strategy:
            document.getElementById(
                "missingStrategy"
            ).value,

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
            parseFloat(
                document.getElementById(
                    "testSize"
                ).value
            ),

        random_state: 42,

        stratify: true
    };


    showLoading(true);
    hideError();


    try {

        const response = await fetch(
            `${API_URL}/preprocess/${fileId}`,
            {
                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify(config)
            }
        );


        const data = await response.json();


        if (!response.ok) {
            throw new Error(
                data.detail ||
                "Preprocessing failed"
            );
        }


        displayResults(data);


    } catch (error) {

        showError(error.message);

    } finally {

        showLoading(false);

    }

}


// -----------------------------------
// Display Results
// -----------------------------------

function displayResults(data) {

    document
        .getElementById("resultsSection")
        .classList.remove("hidden");


    document.getElementById("rowsBefore")
        .textContent =
        data.before.rows;


    document.getElementById("rowsAfter")
        .textContent =
        data.after.rows;


    document.getElementById("columnsBefore")
        .textContent =
        data.before.columns;


    document.getElementById("columnsAfter")
        .textContent =
        data.after.columns;


    // Operations

    const operationsList =
        document.getElementById(
            "operationsList"
        );


    operationsList.innerHTML = "";


    if (
        !data.operations ||
        data.operations.length === 0
    ) {

        operationsList.textContent =
            "No preprocessing operations were applied.";

    } else {

        data.operations.forEach(operation => {

            const div =
                document.createElement("div");

            div.className = "operation";

            div.textContent =
                JSON.stringify(operation);

            operationsList.appendChild(div);

        });

    }


    // Scroll to results

    document
        .getElementById("resultsSection")
        .scrollIntoView({
            behavior: "smooth"
        });

}


// -----------------------------------
// Downloads
// -----------------------------------

function downloadProcessed() {

    if (!fileId) return;

    window.open(
        `${API_URL}/download/${fileId}`,
        "_blank"
    );

}


function downloadTrain() {

    if (!fileId) return;

    window.open(
        `${API_URL}/download/train/${fileId}`,
        "_blank"
    );

}


function downloadTest() {

    if (!fileId) return;

    window.open(
        `${API_URL}/download/test/${fileId}`,
        "_blank"
    );

}


// -----------------------------------
// Loading
// -----------------------------------

function showLoading(show) {

    const loading =
        document.getElementById("loading");

    if (show) {
        loading.classList.remove("hidden");
    } else {
        loading.classList.add("hidden");
    }

}


// -----------------------------------
// Error
// -----------------------------------

function showError(message) {

    const error =
        document.getElementById("error");

    error.textContent = message;

    error.classList.remove("hidden");

}


function hideError() {

    document
        .getElementById("error")
        .classList.add("hidden");

}