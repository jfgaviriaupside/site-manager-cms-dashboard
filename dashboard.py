import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import os

# Add this function after load_data() and before the main app
def categorize_procedure(procedure_type):
    """Categorize procedure types into standard categories"""
    procedure_type = str(procedure_type).upper()
    
    categories = {
        'OPEN MRI': ['OPEN MRI', 'OPEN MAGNETIC'],
        'US': ['US', 'ULTRA', 'SONOGRAM'],
        'CT': ['CT', 'CAT SCAN', 'COMPUTED TOMOGRAPHY'],
        'SLEEP STUDY': ['SLEEP'],
        'MRI': ['MRI', 'MAGNETIC'],
        'PET/CT': ['PET/CT', 'PET CT'],
        'XRAY': ['XRAY', 'X-RAY', 'X RAY', 'RAD'],
        'MAMMOGRAM': ['MAMMO', 'BREAST'],
        'NCS': ['NCS', 'NERVE', 'CONDUCTION'],
        'BONE DENSITY': ['BONE', 'DEXA', 'DENSITOMETRY'],
        'NUCLEAR MEDICINE': ['NUC MED', 'NUCLEAR', 'THYROID UPTAKE'],
        'CARDIAC PET': ['CARDIAC PET', 'HEART PET']
    }
    
    for category, keywords in categories.items():
        if any(keyword in procedure_type for keyword in keywords):
            return category
    
    return 'OTHER'

# Load and clean data function
@st.cache_data
def load_data():
    try:
        file_path = os.getenv('DASHBOARD_DATA_PATH', 'dashboard_data.xlsx')
        
        if not os.path.exists(file_path):
            st.error(f"Data file not found at {file_path}. Please ensure the data file exists.")
            return pd.DataFrame(), 0
            
        # Load cancellation data
        df = pd.read_excel(file_path, sheet_name='Dashboard Cancel No Show')
        
        # Process cancellation data
        df = df[['Appt Date', 'Type', 'Status', 'Created By', 'Created Date/Time', 'Canceled By', 'Canceled Date/Time']]
        df.columns = ['Appointment Date', 'Type', 'Status', 'Created By', 'Created Date', 'Canceled By', 'Canceled Date']

        for col in ['Appointment Date', 'Created Date', 'Canceled Date']:
            df[col] = pd.to_datetime(df[col], errors='coerce')

        df['Procedure Category'] = df['Type'].apply(categorize_procedure)
        
        # Load and process Patients Seen Report
        try:
            patients_seen_df = pd.read_excel(file_path, sheet_name='Patients Seen Report')
            
            # Drop completely empty rows and columns
            patients_seen_df = patients_seen_df.dropna(how='all')
            patients_seen_df = patients_seen_df.dropna(axis=1, how='all')
            
            # First column contains procedure names, rest should be numeric
            numeric_cols = patients_seen_df.columns[1:]
            
            # Convert numeric columns, replacing errors with 0
            for col in numeric_cols:
                patients_seen_df[col] = pd.to_numeric(patients_seen_df[col], errors='coerce').fillna(0)
            
            # Calculate total procedures
            total_procedures = patients_seen_df[numeric_cols].sum().sum()
            
        except Exception as e:
            st.warning(f"Could not process Patients Seen Report: {str(e)}")
            total_procedures = 0
        
        return df, total_procedures
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return pd.DataFrame(), 0

# Main app
st.title('Diagnostic Clinic Dashboard')

data, total_procedures = load_data()

if data.empty:
    st.warning("No data available. Please check if the data file exists and is accessible.")
    st.stop()

# Display total procedures metric at the top
st.metric("Total Procedures Performed", f"{int(total_procedures):,}")

# Tabs for different analyses
tab1, tab2, tab3, tab4 = st.tabs([
    "Cancelled/No-Show Overview", 
    "Employee Analysis", 
    "Cancellation Timing", 
    "Employee Cancellations"
])

# Tab 1: Cancelled/No-Show Overview
with tab1:
    st.header("Procedure Cancellation Analysis")

    # Date range filter
    min_date = data['Appointment Date'].min().date()
    max_date = data['Appointment Date'].max().date()
    start_date, end_date = st.date_input(
        "Select date range", [min_date, max_date], key="tab1_dates"
    )

    # Filter data based on date range
    mask = (data['Appointment Date'].dt.date >= start_date) & (data['Appointment Date'].dt.date <= end_date)
    filtered_data = data[mask]

    # Calculate metrics focusing on cancellations
    proc_metrics = filtered_data.groupby('Procedure Category').agg({
        'Status': lambda x: (x == 'Cancelled').sum()
    }).reset_index()
    
    proc_metrics.columns = ['Procedure Category', 'Cancelled']
    
    # Calculate cancellation rate against total procedures
    proc_metrics['Cancellation Rate'] = (
        proc_metrics['Cancelled'] / total_procedures * 100
        if total_procedures > 0 else 0
    ).round(1)
    
    proc_metrics = proc_metrics.sort_values('Cancellation Rate', ascending=False)

    # Update the metrics display
    st.subheader("Cancellation Overview")
    col1, col2 = st.columns(2)
    with col1:
        st.metric(
            "Total Procedures Performed", 
            f"{int(total_procedures):,}",
            help="Total procedures from Patients Seen Report"
        )
    with col2:
        st.metric(
            "Total Cancellations", 
            f"{proc_metrics['Cancelled'].sum():,}",
            help="Total number of cancelled appointments"
        )

    # Update visualization to show cancellation rates
    st.subheader("Cancellation Analysis by Procedure Type")
    
    fig_cancellation = px.bar(
        proc_metrics[proc_metrics['Procedure Category'] != 'OTHER'],
        x='Procedure Category',
        y='Cancellation Rate',
        text='Cancellation Rate',
        labels={
            'Procedure Category': 'Procedure Type',
            'Cancellation Rate': 'Cancellation Rate (%)'
        },
        height=400
    )
    fig_cancellation.update_traces(
        texttemplate='%{text:.1f}%',
        textposition='outside'
    )
    fig_cancellation.update_layout(
        yaxis_title='Percentage of Total Procedures (%)',
        xaxis_title='Procedure Type'
    )
    st.plotly_chart(fig_cancellation, use_container_width=True)

    # Detailed metrics table
    st.subheader("Detailed Metrics")
    st.dataframe(
        proc_metrics.style
        .format({
            'Cancelled': '{:,}',
            'Cancellation Rate': '{:.1f}%'
        })
        .background_gradient(subset=['Cancellation Rate'], cmap='RdYlGn_r'),
        use_container_width=True
    )

    # Time series of cancellations
    st.subheader("Cancellation Trends")
    weekly_cancels = filtered_data[filtered_data['Status'] == 'Cancelled'].set_index('Appointment Date')
    weekly_cancels = weekly_cancels.groupby(['Procedure Category', pd.Grouper(freq='W')])['Status'].count().reset_index()
    
    fig_trend = px.line(
        weekly_cancels,
        x='Appointment Date',
        y='Status',
        color='Procedure Category',
        title='Weekly Cancellations by Procedure Type',
        labels={'Status': 'Number of Cancellations', 'Appointment Date': 'Week'},
        height=400
    )
    fig_trend.update_xaxes(rangeslider_visible=True)
    st.plotly_chart(fig_trend, use_container_width=True)

    # Add OTHER category analysis
    st.subheader("OTHER Category Analysis")
    other_procedures = filtered_data[filtered_data['Procedure Category'] == 'OTHER']
    
    if not other_procedures.empty:
        # Group and count unique procedure types in OTHER category with cancellation metrics
        other_types = other_procedures.groupby('Type').agg({
            'Status': ['count', lambda x: (x == 'Cancelled').sum()]
        }).reset_index()
        
        other_types.columns = ['Procedure Type', 'Total', 'Cancelled']
        other_types['Cancellation Rate'] = (other_types['Cancelled'] / other_types['Total'] * 100).round(1)
        other_types = other_types.sort_values('Total', ascending=False)
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write("Most Common Procedures in OTHER Category")
            fig_other = px.bar(
                other_types.head(10),
                x='Procedure Type',
                y='Cancellation Rate',
                text='Cancellation Rate',
                color='Total',
                orientation='v',
                title='Top 10 Most Common "OTHER" Procedures',
                labels={
                    'Procedure Type': 'Procedure Type',
                    'Cancellation Rate': 'Cancellation Rate (%)',
                    'Total': 'Total Appointments'
                },
                height=400
            )
            fig_other.update_traces(
                texttemplate='%{text:.1f}%',
                textposition='outside',
                textfont=dict(size=12)
            )
            fig_other.update_layout(
                xaxis_tickangle=-45,
                uniformtext_minsize=8,
                uniformtext_mode='hide'
            )
            st.plotly_chart(fig_other, use_container_width=True)
        
        with col2:
            st.write("Detailed Metrics")
            st.dataframe(
                other_types.head(20).style.format({
                    'Total': '{:,}',
                    'Cancelled': '{:,}',
                    'Cancellation Rate': '{:.1f}%'
                }).background_gradient(subset=['Cancellation Rate'], cmap='RdYlGn_r'),
                use_container_width=True
            )
            
        st.caption(f"Total unique procedure types in OTHER category: {len(other_types)}")
        
        # Add high cancellation rate analysis
        st.subheader("High Cancellation Rate Procedures")
        high_cancel = other_types[
            (other_types['Total'] >= 5) &  # Filter for procedures with at least 5 appointments
            (other_types['Cancellation Rate'] > other_types['Cancellation Rate'].median())
        ].sort_values('Cancellation Rate', ascending=False)
        
        if not high_cancel.empty:
            st.write("Procedures with above-median cancellation rates (minimum 5 appointments)")
            st.dataframe(
                high_cancel.style.format({
                    'Total': '{:,}',
                    'Cancelled': '{:,}',
                    'Cancellation Rate': '{:.1f}%'
                }).background_gradient(subset=['Cancellation Rate'], cmap='RdYlGn_r'),
                use_container_width=True
            )
        else:
            st.info("No procedures meeting the high cancellation rate criteria found.")
    else:
        st.info("No procedures categorized as OTHER in the selected date range.")

# Tab 2: Employee Analysis
with tab2:
    st.header("Employee Procedure Creation Analysis")

    # Date range filter for tab 2
    min_date = data['Appointment Date'].min().date()
    max_date = data['Appointment Date'].max().date()
    start_date, end_date = st.date_input(
        "Select date range", [min_date, max_date], key="tab2_dates"
    )

    # Filter data based on date range
    mask = (data['Appointment Date'].dt.date >= start_date) & (data['Appointment Date'].dt.date <= end_date)
    filtered_data = data[mask]

    # Create employee procedure creation metrics
    employee_procedures = filtered_data.groupby(['Created By', 'Procedure Category']).size().reset_index(name='Count')
    employee_total = filtered_data.groupby('Created By').size().reset_index(name='Total')
    
    # Create pivot table for heatmap
    heatmap_data = employee_procedures.pivot(
        index='Created By',
        columns='Procedure Category',
        values='Count'
    ).fillna(0)
    
    # Calculate percentage distribution
    heatmap_pct = heatmap_data.div(heatmap_data.sum(axis=1), axis=0) * 100
    
    # Main visualizations
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Procedure Distribution by Employee")
        fig_heatmap = px.imshow(
            heatmap_pct,
            labels=dict(x="Procedure Type", y="Employee", color="% of Employee's Work"),
            aspect="auto",
            height=600,
            color_continuous_scale="Viridis"
        )
        fig_heatmap.update_traces(
            hovertemplate="Employee: %{y}<br>Procedure: %{x}<br>Count: %{customdata}<br>Percentage: %{z:.1f}%<extra></extra>"
        )
        fig_heatmap.data[0].customdata = heatmap_data.values
        
        fig_heatmap.update_layout(
            xaxis_tickangle=-45,
            yaxis_title="Employee",
            xaxis_title="Procedure Type"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    with col2:
        st.subheader("Employee Volume")
        fig_volume = px.bar(
            employee_total.sort_values('Total', ascending=True).tail(10),
            x='Total',
            y='Created By',
            orientation='h',
            title='Top 10 Employees by Volume',
            labels={'Created By': 'Employee', 'Total': 'Total Procedures Created'},
            height=400
        )
        fig_volume.update_traces(texttemplate="%{x:.0f}", textposition="outside")
        st.plotly_chart(fig_volume, use_container_width=True)

    # Employee selector moved below the first two graphs
    employees = sorted(filtered_data['Created By'].unique())
    selected_employee = st.selectbox("Select Employee for Detailed Analysis", employees)

    # Selected Employee Analysis
    st.subheader(f"Detailed Analysis for {selected_employee}")
    
    # Filter data for selected employee
    employee_data = filtered_data[filtered_data['Created By'] == selected_employee]
    
    # Calculate metrics
    total_procedures = len(employee_data)
    cancelled_procedures = len(employee_data[employee_data['Status'] == 'Cancelled'])
    cancellation_rate = (cancelled_procedures / total_procedures * 100) if total_procedures > 0 else 0
    
    # Display metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Procedures", f"{total_procedures:,}")
    with col2:
        st.metric("Cancelled Procedures", f"{cancelled_procedures:,}")
    with col3:
        st.metric("Cancellation Rate", f"{cancellation_rate:.1f}%")

    # Procedure type distribution for selected employee
    col1, col2 = st.columns(2)
    
    with col1:
        proc_dist = employee_data['Procedure Category'].value_counts()
        fig_proc = px.pie(
            values=proc_dist.values,
            names=proc_dist.index,
            title='Procedure Type Distribution'
        )
        st.plotly_chart(fig_proc, use_container_width=True)
    
    with col2:
        cancel_by_type = employee_data.groupby('Procedure Category').agg({
            'Status': ['count', lambda x: (x == 'Cancelled').sum()]
        }).reset_index()
        cancel_by_type.columns = ['Procedure Category', 'Total', 'Cancelled']
        cancel_by_type['Cancellation Rate'] = (cancel_by_type['Cancelled'] / cancel_by_type['Total'] * 100).round(1)
        
        fig_cancel = px.bar(
            cancel_by_type,
            x='Procedure Category',
            y='Cancellation Rate',
            title='Cancellation Rate by Procedure Type',
            labels={'Cancellation Rate': 'Cancellation Rate (%)'}
        )
        fig_cancel.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_cancel, use_container_width=True)

    # List of all procedures scheduled by the selected employee
    st.subheader(f"Procedures Scheduled by {selected_employee}")
    st.dataframe(employee_data[['Appointment Date', 'Procedure Category', 'Status']], use_container_width=True)

# Tab 3: Cancellation Timing
with tab3:
    st.header("Cancellation Timing Analysis")

    # Calculate time to cancellation for cancelled appointments
    cancelled_data = data[data['Status'] == 'Cancelled'].copy()
    if not cancelled_data.empty:
        # Calculate time difference in hours
        cancelled_data['Time to Cancellation'] = (
            (cancelled_data['Canceled Date'] - cancelled_data['Created Date'])
            .dt.total_seconds() / 3600
        )
        
        # Remove rows where time calculation is invalid
        cancelled_data = cancelled_data.dropna(subset=['Time to Cancellation'])
        
        if not cancelled_data.empty:
            bins = [0, 0.1667, 1, 5, 24, float('inf')]  # 10min, 1hr, 5hr, 24hr, >24hr
            labels = ['<10 mins', '10m-1h', '1-5h', '5-24h', '>24h']
            
            cancelled_data['Time Category'] = pd.cut(
                cancelled_data['Time to Cancellation'], 
                bins=bins, 
                labels=labels
            )

            fig = px.pie(
                cancelled_data, 
                names='Time Category', 
                title="Time Between Scheduling and Cancellation"
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Add summary statistics
            st.subheader("Summary Statistics")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Average Hours", f"{cancelled_data['Time to Cancellation'].mean():.1f}")
            with col2:
                st.metric("Median Hours", f"{cancelled_data['Time to Cancellation'].median():.1f}")
            with col3:
                st.metric("Max Hours", f"{cancelled_data['Time to Cancellation'].max():.1f}")
        else:
            st.warning("No valid time differences found in cancellations.")
    else:
        st.warning("No cancelled appointments found.")

# Tab 4: Employee Cancellations
with tab4:
    st.header("Employee Cancellation Analysis")

    # Date range filter
    min_date = data['Appointment Date'].min().date()
    max_date = data['Appointment Date'].max().date()
    start_date, end_date = st.date_input(
        "Select date range", [min_date, max_date], key="tab4_dates"
    )

    # Filter data based on date range
    mask = (data['Appointment Date'].dt.date >= start_date) & (data['Appointment Date'].dt.date <= end_date)
    filtered_data = data[mask]

    # Calculate cancellation metrics by employee
    cancel_metrics = filtered_data[filtered_data['Status'] == 'Cancelled'].groupby('Canceled By').agg({
        'Status': 'count',
        'Procedure Category': lambda x: len(x.unique())
    }).reset_index()
    cancel_metrics.columns = ['Employee', 'Cancellations', 'Unique Procedures']
    cancel_metrics = cancel_metrics.sort_values('Cancellations', ascending=True)

    # Visualization of cancellations by employee
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Cancellations by Employee")
        fig = px.bar(
            cancel_metrics.tail(15),  # Show top 15 employees
            x='Cancellations',
            y='Employee',
            orientation='h',
            color='Unique Procedures',
            labels={'Unique Procedures': 'Number of Different Procedures'},
            height=500
        )
        fig.update_traces(texttemplate="%{x}", textposition="outside")
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Summary Statistics")
        total_cancellations = cancel_metrics['Cancellations'].sum()
        avg_cancellations = cancel_metrics['Cancellations'].mean()
        max_cancellations = cancel_metrics['Cancellations'].max()
        
        st.metric("Total Cancellations", f"{total_cancellations:,}")
        st.metric("Average per Employee", f"{avg_cancellations:.1f}")
        st.metric("Maximum by Single Employee", f"{max_cancellations:,}")

    # Employee selector for detailed analysis
    st.subheader("Detailed Cancellation Analysis")
    employees = sorted(cancel_metrics['Employee'].unique())
    selected_employee = st.selectbox("Select Employee", employees, key='tab4_employee')

    # Get detailed cancellation data for selected employee
    employee_cancellations = filtered_data[
        (filtered_data['Status'] == 'Cancelled') & 
        (filtered_data['Canceled By'] == selected_employee)
    ].copy()

    if not employee_cancellations.empty:
        # Show detailed table of cancellations
        st.subheader(f"Cancelled Appointments by {selected_employee}")
        detailed_view = employee_cancellations[[
            'Appointment Date', 
            'Type',
            'Created Date',
            'Canceled Date'
        ]].sort_values('Appointment Date', ascending=False)

        # Helper function to safely format dates
        def format_date(x):
            try:
                if pd.isna(x):
                    return 'N/A'
                return x.strftime('%Y-%m-%d %H:%M')
            except:
                return 'N/A'

        st.dataframe(
            detailed_view.style.format({
                'Appointment Date': format_date,
                'Created Date': format_date,
                'Canceled Date': format_date
            }),
            use_container_width=True
        )

        # Add distribution of cancellations by actual procedure type
        st.subheader("Cancellations by Procedure Type")
        proc_dist = employee_cancellations['Type'].value_counts()
        fig = px.pie(
            values=proc_dist.values,
            names=proc_dist.index,
            title=f'Distribution of Cancelled Procedures by {selected_employee}'
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info(f"No cancellations found for {selected_employee} in the selected date range.")

st.sidebar.markdown("### Filters")
st.sidebar.info("Use date filters in individual tabs for specific analyses.")