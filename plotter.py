import json
import os
import glob
import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

def visualize_job_data(data_folder, output_folder="images"):
    """
    Visualizes job data and saves plots as higher resolution images with thinner lines,
    smaller text, sorted legend order, and overwrites previous images.
    """
    os.makedirs(output_folder, exist_ok=True)

    # --- Clear the output folder before generating new images ---
    for filename in os.listdir(output_folder):
        file_path = os.path.join(output_folder, filename)
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {e}")
    print(f"Cleared existing images from {output_folder}")


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

    # --- Sort Companies for Combined Plot Legend ---
    latest_total_jobs = df_combined_total_jobs.groupby('company')['total_jobs'].last().sort_values(ascending=False)
    sorted_companies_combined = latest_total_jobs.index.tolist()
    df_combined_total_jobs['company'] = pd.Categorical(df_combined_total_jobs['company'], categories=sorted_companies_combined, ordered=True)


    # Plot 1: Combined total jobs for all companies
    fig_total = px.line(df_combined_total_jobs, x="time", y="total_jobs", color="company",
                        title="Total Jobs Over Time for All Companies",
                        labels={"time": "Time", "total_jobs": "Total Jobs", "company": "Company"},
                        line_shape='linear',
                        category_orders={"company": sorted_companies_combined}) # Apply category order

    # Customize line thickness and text size for combined plot
    fig_total.update_traces(line=dict(width=1.5))
    fig_total.update_layout(
        title=dict(font=dict(size=16)),
        xaxis=dict(titlefont=dict(size=12)),
        yaxis=dict(titlefont=dict(size=12)),
        legend=dict(font=dict(size=10))
    )

    # Save combined total jobs plot with higher resolution and adjusted style
    fig_total_filepath = os.path.join(output_folder, "total_jobs_combined.png")
    fig_total.write_image(fig_total_filepath, scale=2)
    print(f"Saved combined total jobs plot to: {fig_total_filepath}")


    # Create individual plots for each company
    for company, data in all_company_data.items():
        df_company = pd.DataFrame(data)

        # Prepare data for job areas plot
        job_areas_list = []
        for entry in data:
            for area, count in entry['job_areas'].items():
                job_areas_list.append({'time': entry['time'], 'area': area, 'count': count})
        df_job_areas = pd.DataFrame(job_areas_list)

        # --- Sort Job Areas for Company Plot Legend ---
        latest_job_areas_counts = df_job_areas.groupby('area')['count'].last().sort_values(ascending=False)
        sorted_job_areas = latest_job_areas_counts.index.tolist()


        # Create subplots for total jobs and jobs per area
        fig = make_subplots(rows=2, cols=1, subplot_titles=[f"Total {company.capitalize()} Jobs Over Time",
                                                          f"{company.capitalize()} Jobs per Area Over Time"])

        # Plot total jobs for the company
        fig.add_trace(go.Scatter(x=df_company['time'], y=df_company['total_jobs'], mode='lines', name='Total Jobs', line=dict(width=1.5)), row=1, col=1)

        # Plot jobs per area for the company - in sorted order
        for area in sorted_job_areas: # Iterate through sorted job areas
            df_area = df_job_areas[df_job_areas['area'] == area] # Corrected line
            fig.add_trace(go.Scatter(x=df_area['time'], y=df_area['count'], mode='lines', name=area, line=dict(width=1.5)), row=2, col=1)

        # Update layout for better readability and smaller text
        fig.update_xaxes(title_text="Time", titlefont=dict(size=12), row=1, col=1)
        fig.update_yaxes(title_text="Total Jobs", titlefont=dict(size=12), row=1, col=1)
        fig.update_xaxes(title_text="Time", titlefont=dict(size=12), row=2, col=1)
        fig.update_yaxes(title_text="Number of Jobs", titlefont=dict(size=12), row=2, col=1)
        fig.update_layout(
            title_text=f"{company.capitalize()} Job Trends",
            title_font=dict(size=16),
            showlegend=True,
            legend=dict(font=dict(size=10)),
            font=dict(size=10)
        )
        fig.for_each_annotation(lambda a: a.update(font_size=14))


        # Save company-specific plot with higher resolution and adjusted style
        fig_company_filepath = os.path.join(output_folder, f"{company}_job_trends.png")
        fig.write_image(fig_company_filepath, scale=2)
        print(f"Saved {company.capitalize()} job trends plot to: {fig_company_filepath}")


if __name__ == "__main__":
    script_dir = os.path.dirname(__file__)
    data_folder_path = os.path.join(script_dir, "data")
    output_images_folder = "images"
    visualize_job_data(data_folder_path, output_images_folder)