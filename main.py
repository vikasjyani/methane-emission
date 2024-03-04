from datetime import datetime
import os
import pandas as pd
import streamlit as st
from PIL import Image
import plotly.express as px

# Load and resize the logo
img = Image.open('Vasudha_Logo_PNG.png')
resized_img = img.resize((300, 300))

# Display the logo and title
col1, col2 = st.columns([1, 5])
col1.image(resized_img, use_column_width=True)
col2.title('Methane Emission Calculation Web App')

# Functions for file and sheet selection
def get_state_excel_files(folder_path):
    state_excel_files = {}
    for root, _, files in os.walk(folder_path):
        for file in files:
            if file.endswith(".xlsx"):
                state = os.path.basename(root)
                state_excel_files.setdefault(state, []).append(os.path.join(root, file))
    return state_excel_files

def get_district_sheets(excel_file):
    return pd.ExcelFile(excel_file).sheet_names

def select_files_and_sheets(state, folder_path):
    state_excel_files = get_state_excel_files(folder_path)
    col1,col2=st.columns(2)
    state_display_names = [os.path.splitext(os.path.basename(file))[0] for file in state_excel_files[state]]
    with col1:
        selected_file_index = st.selectbox("Select State", range(len(state_excel_files[state])), format_func=lambda x: state_display_names[x])
    selected_file_full_path = state_excel_files[state][selected_file_index]
    selected_file = os.path.basename(selected_file_full_path)
    district_sheets = get_district_sheets(selected_file_full_path)
    with col2:
        selected_sheet = st.selectbox("Selected district", district_sheets)
    return selected_file, selected_sheet, selected_file_index

# Function to plot data
def ploting_data(df, selected_date,selected_location):
    data1 = df[['latitude', 'longitude', selected_date]].dropna()
    # Plot map
    for_contours = df.drop(['latitude', 'longitude'], axis=1)
    min_values = for_contours.min()
    max_values = for_contours.max()
    # Extract minimum and maximum values from Pandas Series
    
    #min_value = min_values.min()
    #max_value = max_values.max()
    min_value = data1[selected_date].min()
    max_value = data1[selected_date].max()
    fig = px.scatter_mapbox(data1, 
                            lat="latitude", 
                            lon="longitude", 
                            color=selected_date, 
                            zoom=6, 
                            mapbox_style='open-street-map', 
                            color_continuous_scale='Viridis',
                            range_color=[min_value, max_value],
                            color_continuous_midpoint=(min_value + max_value) / 2) # Set midpoint for color scale

    # Update layout to set legend title
    total_methane = round(data1[selected_date].sum(), 2)

    fig.update_layout(coloraxis_colorbar_title="Methane in Tonnes ",title= f"Total methane content in the atmosphere is {total_methane} tonnes for {selected_location}")

    # Show the plot
    st.plotly_chart(fig)


# Main application logic
def main():

    folder_path =  "results"
    states = list(get_state_excel_files(folder_path).keys())
    selected_state = states[0]
    selected_file, selected_sheet, _ = select_files_and_sheets(selected_state, folder_path)
    st.write(f"Selected district: {selected_sheet}")

    file_path = 'results'
    df = pd.read_excel(os.path.join(file_path, selected_file), sheet_name=selected_sheet)
    columns_to_update = df.columns.difference(['latitude', 'longitude'])
    df[columns_to_update] = df[columns_to_update].apply(lambda x: round((0.706 * 10000 * 1113.2 * 1113.2 * x) / (1000 * 1000000*1000), 2))

    district_df=df
    min_date = datetime(2014, 1, 1)
    max_date = datetime(2023, 12, 1)
    col1,col2=st.columns(2)
    with col1:
        
        selected_start_date = st.date_input("Select start month and year:", min_value=min_date, max_value=max_date, value=min_date)
    with col2:
        st.link_button("Go Real Time Satellite imeges prediction", "https://methane-emission-webapp-vasudhafoundation.streamlit.app/")
    selected_start_month = selected_start_date.month
    selected_start_year = selected_start_date.year
    selected_start_time = f'{selected_start_year}_{selected_start_month:02d}_01'
    selected_date = selected_start_time

    if selected_date not in df.columns:
        st.write('Please select another date')
        selected_date = st.selectbox('Select date', df.columns.drop(['latitude', 'longitude']).tolist())

    ploting_data(df, selected_date,selected_sheet)

    # Read the Excel file
    excel_file_path = f'results/{selected_file}'
    excel_data = pd.read_excel(excel_file_path, sheet_name=None)

    # Initialize an empty list to store DataFrames
    dfs = []

    # Iterate over each sheet and append it to the list
    for sheet_name, df in excel_data.items():
        dfs.append(df)

    # Concatenate all DataFrames in the list along the rows
    combined_df = pd.concat(dfs, ignore_index=True)
    # Select all columns except 'latitude' and 'longitude'
    columns_to_update = combined_df.columns.difference(['latitude', 'longitude'])

    # Apply the multiplication operation to selected columns
    combined_df[columns_to_update] = combined_df[columns_to_update].apply(lambda x: round((0.706 * 10000 * 1113.2 * 1113.2 * x) / (1000 * 1000000*1000), 2))
    # Display the combined DataFrame
    print(combined_df)
    ploting_data(combined_df, selected_date,'selected State')

    months = range(1, 13) # Months from January to December

    # Generate a list of formatted date strings for each month
    selected_times_line_plot = [f'{selected_start_year}_{month:02d}_01' for month in months]
    data_district = []
    months=[]
    for date in selected_times_line_plot:
        try:
            methane_mean = district_df[date].mean()
            data_district.append(methane_mean)
            months.append(date)
        except KeyError:

            pass

    df_line = pd.DataFrame({'Month': months, 'Mean_Methane': data_district})

    # Plot the line chart for district
    fig = px.line(df_line, x='Month', y='Mean_Methane', title=f'Mean Methane Concentration from January to December for {selected_sheet} per 1.23Km^2')
    fig.update_xaxes(title='Month')
    fig.update_yaxes(title='Mean Methane Concentration')
    st.plotly_chart(fig)

    data_state = []
    months=[]
    for date in selected_times_line_plot:
        try:
            methane_mean = combined_df[date].mean()
            data_state.append(methane_mean)
            months.append(date)
        except KeyError:

            pass
    df_line = pd.DataFrame({'Month': months, 'Mean_Methane': data_state})

    # Plot the line chart for state
    fig = px.line(df_line, x='Month', y='Mean_Methane', title=f'Mean Methane Concentration from January to December for state per 1.23Km^2')
    fig.update_xaxes(title='Month')
    fig.update_yaxes(title='Mean Methane Concentration')
    st.plotly_chart(fig)

if __name__ == "__main__":
    main()
