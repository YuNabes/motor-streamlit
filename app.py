import pandas as pd
import plotly.graph_objects as go
import streamlit as st

def load_csv(file):
    """Load CSV file into a pandas DataFrame, ignoring comment lines."""
    df = pd.read_csv(file, comment='#')
    return df

def validate_data_labels(raw_data, shaping_data):
    """
    Validate that all data labels in the raw data and shaping data match.
    Raise an error if mismatches are found.
    """
    raw_labels = set(raw_data.columns[1:])  # Exclude the time column
    shaping_labels = set(shaping_data.columns[1:])

    # Check for labels in raw data that are not in shaping data
    extra_raw_labels = raw_labels - shaping_labels
    if extra_raw_labels:
        raise ValueError(f"Error: The following data labels in the raw data file are not specified in the shaping data file: {', '.join(extra_raw_labels)}")

    # Check for labels in shaping data that are not in raw data
    extra_shaping_labels = shaping_labels - raw_labels
    if extra_shaping_labels:
        raise ValueError(f"Error: The following data labels in the shaping data file are not found in the raw data file: {', '.join(extra_shaping_labels)}")

def process_data(raw_data, shaping_data, time_offset):
    """Process raw data based on shaping data and apply time offset."""
    scaling = shaping_data.iloc[0, 1:].to_dict()  # First row, except the time column
    offset = shaping_data.iloc[1, 1:].to_dict()   # Second row, except the time column

    # Apply time offset to the raw data's time column
    raw_data[raw_data.columns[0]] = raw_data[raw_data.columns[0]] + time_offset

    processed_data = raw_data.copy()
    for col in raw_data.columns[1:]:
        if col in scaling:
            processed_data[col] = raw_data[col] * scaling[col] + offset[col]

    return processed_data

def plot_data(processed_data, selected_columns, title, y_axis_label, x_range=None):
    """Plot processed data using Plotly."""
    fig = go.Figure()

    for col in selected_columns:
        fig.add_trace(go.Scatter(
            x=processed_data[processed_data.columns[0]],
            y=processed_data[col],
            mode='lines',
            name=col
        ))

    # Set x-axis range if provided
    if x_range:
        fig.update_xaxes(range=x_range)

    fig.update_layout(
        title=title,
        xaxis_title='Time [s]',
        yaxis_title=y_axis_label,
        template='plotly_white',
        legend=dict(title='Legend', itemsizing='constant'),  # Ensure legend visibility
        showlegend=True  # Always show legend, even for single data
    )

    st.plotly_chart(fig)

def main():
    """Main function to execute the Streamlit app."""
    st.title('Motor Data Visualization')

    st.sidebar.header('Upload CSV Files')
    raw_data_file = st.sidebar.file_uploader("Choose the raw data CSV file", type="csv")
    shaping_data_file = st.sidebar.file_uploader("Choose the data shaping CSV file", type="csv")

    if raw_data_file is not None and shaping_data_file is not None:
        try:
            raw_data = load_csv(raw_data_file)
            shaping_data = load_csv(shaping_data_file)

            # Extract the time offset from the shaping data (1st column, 2nd row in 1-based index)
            time_offset = shaping_data.iloc[1, 0]  # 1-based index: 1st column, 2nd row (0-based index: 0th column, 1st row)
            time_offset = float(time_offset)  # Ensure the offset is a float

            # Validate the data labels
            validate_data_labels(raw_data, shaping_data)

            # Process data with the time offset
            processed_data = process_data(raw_data, shaping_data, time_offset)

            st.sidebar.header('Customize Graphs')

            num_graphs = st.sidebar.slider('Number of Graphs', min_value=1, max_value=10, value=3)

            available_columns = processed_data.columns[1:]

            # x-axis range slider for all graphs
            st.sidebar.header('Select X-axis Range for All Graphs')
            x_min, x_max = st.sidebar.slider(
                "Select the x-axis range", 
                min_value=float(processed_data[processed_data.columns[0]].min()), 
                max_value=float(processed_data[processed_data.columns[0]].max()), 
                value=(float(processed_data[processed_data.columns[0]].min()), 
                       float(processed_data[processed_data.columns[0]].max())),
                step=0.01
            )
            x_range = [x_min, x_max]

            for i in range(1, num_graphs + 1):
                st.sidebar.subheader(f'Graph {i} Settings')
                selected_columns = st.sidebar.multiselect(f'Choose columns for Graph {i}', available_columns, key=f'columns_{i}')
                y_axis_label = st.sidebar.selectbox(
                    f'Choose Y-axis Label for Graph {i}',
                    options=['Voltage[V]', 'Current[A]', 'Speed[rpm]', 'angle[rad]', 'angle[deg]', 'Speed[rad/s]', 'Custom'],
                    key=f'y_label_{i}'
                )
                if y_axis_label == 'Custom':
                    custom_label = st.sidebar.text_input(f'Enter custom Y-axis label for Graph {i}:', key=f'custom_label_{i}')
                    if custom_label:
                        y_axis_label = custom_label

                custom_title = st.sidebar.text_input(f'Enter title for Graph {i}:', f'Graph {i}: Selected Columns', key=f'title_{i}')

                if selected_columns:
                    plot_data(processed_data, selected_columns, custom_title, y_axis_label, x_range)
                else:
                    st.sidebar.warning(f'Please select at least one column for Graph {i}.')

        except ValueError as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
