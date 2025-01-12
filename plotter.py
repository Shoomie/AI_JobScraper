import json
import os
import glob
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def visualize_job_data(data_folder):
    """
    Visualizes job data for Anthropic, OpenAI, and xAI from JSON files, 
    creating a combined plot for total jobs and separate plots for each company's job areas.

    Args:
        data_folder: The path to the folder containing JSON files.
    """

    all_company_data = {}
    json_files = glob.glob(os.path.join(data_folder, "*.json"))

    if not json_files:
        print(f"Error: No JSON files found in {data_folder}")
        return

    for json_file in json_files:
        company_name = os.path.basename(json_file).split("_")[0]
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)['data']
                if company_name not in all_company_data:
                    all_company_data[company_name] = []
                all_company_data[company_name].extend(data)
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON format in {json_file}")
            continue

    # Sort data for each company by time
    for company_data in all_company_data.values():
        company_data.sort(key=lambda x: x['time'])

    # Create combined dataframe for total jobs plot
    combined_total_jobs_data = []
    for company, data in all_company_data.items():
        for entry in data:
            combined_total_jobs_data.append({'time': entry['time'], 'company': company, 'total_jobs': entry['total_jobs']})
    df_combined_total_jobs = pd.DataFrame(combined_total_jobs_data)

    # Plot 1: Combined total jobs for all companies
    fig_total = px.line(df_combined_total_jobs, x="time", y="total_jobs", color="company",
                        title="Total Jobs Over Time for All Companies",
                        labels={"time": "Time", "total_jobs": "Total Jobs", "company": "Company"})
    fig_total.show()

    # Create individual plots for each company
    for company, data in all_company_data.items():
        df_company = pd.DataFrame(data)

        # Prepare data for job areas plot
        job_areas_list = []
        for entry in data:
            for area, count in entry['job_areas'].items():
                job_areas_list.append({'time': entry['time'], 'area': area, 'count': count})
        df_job_areas = pd.DataFrame(job_areas_list)

        # Create subplots for total jobs and jobs per area
        fig = make_subplots(rows=2, cols=1, subplot_titles=[f"Total {company.capitalize()} Jobs Over Time",
                                                          f"{company.capitalize()} Jobs per Area Over Time"])

        # Plot total jobs for the company
        fig.add_trace(go.Scatter(x=df_company['time'], y=df_company['total_jobs'], mode='lines', name='Total Jobs'), row=1, col=1)

        # Plot jobs per area for the company
        for area in df_job_areas['area'].unique():
            df_area = df_job_areas[df_job_areas['area'] == area]
            fig.add_trace(go.Scatter(x=df_area['time'], y=df_area['count'], mode='lines', name=area), row=2, col=1)

        # Update layout for better readability
        fig.update_xaxes(title_text="Time", row=1, col=1)
        fig.update_yaxes(title_text="Total Jobs", row=1, col=1)
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Number of Jobs", row=2, col=1)
        fig.update_layout(title_text=f"{company.capitalize()} Job Trends", showlegend=True)
        fig.show()

if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    data_folder_path = os.path.join(script_dir, "data")
    visualize_job_data(data_folder_path)