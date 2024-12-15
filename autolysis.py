import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import openai
from tenacity import retry, stop_after_attempt, wait_fixed

# Load API key from environment variable
API_KEY = os.environ.get("AIPROXY_TOKEN")
if not API_KEY:
    print("Error: AIPROXY_TOKEN environment variable not set.")
    sys.exit(1)

openai.api_key = API_KEY

@retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
def call_llm(prompt, model="gpt-4o-mini"):
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "You are an expert data analyst."},
                      {"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error during LLM call: {e}")
        raise

# Helper functions for visualization
def save_correlation_heatmap(df, output_file):
    plt.figure(figsize=(10, 8))
    corr = df.corr(numeric_only=True)
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm")
    plt.title("Correlation Matrix")
    plt.savefig(output_file)
    plt.close()

def save_histograms(df, output_prefix):
    for column in df.select_dtypes(include=np.number).columns:
        plt.figure()
        sns.histplot(df[column].dropna(), kde=True, bins=30, color="blue")
        plt.title(f"Distribution of {column}")
        plt.xlabel(column)
        plt.ylabel("Frequency")
        output_file = f"{output_prefix}_{column}.png"
        plt.savefig(output_file)
        plt.close()

# Process the dataset and generate analysis and visualizations
def analyze_dataset(filename):
    try:
        df = pd.read_csv(filename)
    except Exception as e:
        print(f"Error loading file {filename}: {e}")
        sys.exit(1)

    # Basic statistics
    basic_stats = df.describe(include="all").to_string()
    missing_values = df.isnull().sum().to_string()
    unique_values = df.nunique().to_string()

    # Save visualizations
    save_correlation_heatmap(df, "correlation_heatmap.png")
    save_histograms(df, "histogram")

    # LLM analysis prompts
    column_info = df.dtypes.to_string()
    sample_values = df.head(5).to_string()

    prompt = f"""
    You are analyzing a dataset with the following characteristics:
    - Columns and their data types:
    {column_info}
    - Sample data:
    {sample_values}
    - Summary statistics:
    {basic_stats}
    - Missing values per column:
    {missing_values}
    - Unique values per column:
    {unique_values}

    Based on this information:
    1. Summarize the dataset.
    2. Suggest and describe interesting analyses that can be performed.
    """

    summary = call_llm(prompt)

    # Write narrative to README.md
    with open("README.md", "w") as readme:
        readme.write("# Automated Analysis Report\n\n")
        readme.write("## Dataset Summary\n")
        readme.write(summary + "\n")
        readme.write("\n## Visualizations\n")
        readme.write("![Correlation Heatmap](correlation_heatmap.png)\n")
        for column in df.select_dtypes(include=np.number).columns:
            readme.write(f"![Histogram of {column}](histogram_{column}.png)\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    dataset_file = sys.argv[1]
    analyze_dataset(dataset_file)

