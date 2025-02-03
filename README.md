# Diagnostic Clinic Dashboard

## Overview
This is a **Streamlit** dashboard designed to analyze diagnostic clinic data. The dashboard processes two main datasets:
1. **Dashboard Cancel No Show** - Contains appointment status information (e.g., cancellations, no-shows).
2. **Patients Seen Report** - Contains the count of procedures performed over a given period.

The dashboard provides insights into cancellations, employee activity, and procedure trends, while also categorizing procedures into standardized medical categories.

---

## Features
- **Total Procedures Metric**: Summarizes the total number of procedures performed from the "Patients Seen Report."
- **Cancellation Analysis**:
  - Date-based filtering for cancellations.
  - Breakdown of cancellations by procedure type.
  - Visualization of cancellation rates.
  - Weekly trend analysis.
- **Employee Activity Analysis**:
  - Insights into procedures scheduled by employees.
  - Heatmaps showing procedure distribution per employee.
  - Cancellation behavior by employees.
- **Procedure Categorization**:
  - Categorizes procedures using a keyword-based approach.
  - Ensures accurate grouping for analysis.
- **Time-to-Cancellation Analysis**:
  - Measures the time between appointment creation and cancellation.
  - Provides distribution insights.
- **Employee Cancellations**:
  - Tracks who is canceling appointments the most.
  - Provides individual cancellation breakdowns.

---

## Setup Instructions
### **1. Install Required Dependencies**
Ensure Python and the necessary libraries are installed:
```sh
pip install streamlit pandas plotly openpyxl
```

### **2. Prepare the Data File**
- Place the Excel file **`dashboard_data.xlsx`** in the working directory.
- Ensure it has the following sheets:
  - **Dashboard Cancel No Show**: Contains appointment data.
  - **Patients Seen Report**: Contains procedure counts.

Alternatively, you can set an environment variable to specify the file path:
```sh
export DASHBOARD_DATA_PATH="/path/to/dashboard_data.xlsx"
```

### **3. Run the Streamlit App**
To launch the dashboard, run:
```sh
streamlit run app.py
```

---

## Data Processing
### **Categorizing Procedures**
Procedures in the "Patients Seen Report" are assigned to categories based on predefined keywords. The script scans procedure names and maps them to the following categories:

- **OPEN MRI**: OPEN MRI, OPEN MAGNETIC
- **US**: US, ULTRA, SONOGRAM
- **CT**: CT, CAT SCAN, COMPUTED TOMOGRAPHY
- **SLEEP STUDY**: SLEEP
- **MRI**: MRI, MAGNETIC
- **PET/CT**: PET/CT, PET CT
- **XRAY**: XRAY, X-RAY, X RAY, RAD
- **MAMMOGRAM**: MAMMO, BREAST
- **NCS**: NCS, NERVE, CONDUCTION
- **BONE DENSITY**: BONE, DEXA, DENSITOMETRY
- **NUCLEAR MEDICINE**: NUC MED, NUCLEAR, THYROID UPTAKE
- **CARDIAC PET**: CARDIAC PET, HEART PET
- **OTHER**: Any procedure that does not match the predefined categories.

This categorization ensures that procedure types are consistently grouped for analysis.

### **Processing the "Dashboard Cancel No Show" Sheet**
- Extracts relevant columns:
  - `Appointment Date`, `Type`, `Status`, `Created By`, `Created Date`, `Canceled By`, `Canceled Date`.
- Converts date fields into **datetime format**.
- Categorizes procedures using the `categorize_procedure()` function.

### **Processing the "Patients Seen Report" Sheet**
- Drops empty rows and columns.
- Extracts the first column as `Procedure Type`.
- Converts remaining columns into numeric values.
- Calculates the **total procedures performed** by summing all values.

---

## Dashboard Sections
### **1. Total Procedures Overview**
- Displays the total number of procedures from "Patients Seen Report."
- Provides a quick summary of clinic activity.

### **2. Cancellations & No-Shows Analysis**
- Filters appointment data by date range.
- Computes total cancellations per procedure type.
- Displays cancellation rates using a bar chart.
- Identifies procedures in the "OTHER" category that may need reclassification.

### **3. Employee Analysis**
- Tracks which employees schedule the most procedures.
- Provides a heatmap of procedure types per employee.
- Identifies employees with the highest cancellation rates.

### **4. Cancellation Timing**
- Analyzes how quickly appointments are canceled after scheduling.
- Groups cancellations into time bins (`<10 mins`, `10m-1h`, etc.).
- Displays trends in cancellation timing.

### **5. Employee Cancellations**
- Tracks which employees are responsible for the most cancellations.
- Allows filtering by date range.
- Displays cancellation trends per employee.

---

## Troubleshooting
### **1. No Data Found**
- Ensure `dashboard_data.xlsx` is in the correct location.
- Check if the sheet names match exactly (`Dashboard Cancel No Show`, `Patients Seen Report`).
- If using a custom file path, confirm `DASHBOARD_DATA_PATH` is set correctly.

### **2. Errors in File Reading**
- Ensure the file format is **Excel (.xlsx)**.
- Check if all required columns exist in the dataset.
- If an error occurs during number conversion, check for incorrect data types in numeric columns.

### **3. Dashboard Not Loading Correctly**
- Restart the Streamlit server (`Ctrl+C` and rerun `streamlit run app.py`).
- Check the terminal for error messages.
- Ensure all required dependencies are installed.

---

## Future Improvements
- Implement **automatic category updates** when new procedures are detected.
- Add **employee performance benchmarking** for productivity analysis.
- Introduce **machine learning predictions** for appointment no-shows.

---
