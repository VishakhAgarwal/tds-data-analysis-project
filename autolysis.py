#!/usr/bin/env python3

# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "pandas",
#   "seaborn",
#   "matplotlib",
#   "openai",
#   "tenacity"
# ]
# ///

import os
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from tenacity import retry, stop_after_attempt, wait_fixed
from openai import OpenAI

class DataAnalysisAssistant:
    def __init__(self, dataset_path):
        self.dataset_path = dataset_path
        self.df = pd.read_csv(dataset_path)
        self.client = OpenAI(api_key=os.environ.get("AIPROXY_TOKEN"))

    def basic_analysis(self):
        """Perform basic statistical analysis."""
        analysis = {
            'total_rows': len(self.df),
            'total_columns': len(self.df.columns),
            'column_types': dict(self.df.dtypes),
            'missing_values': self.df.isnull().sum().to_dict(),
            'summary_statistics': self.df.describe(include='all', datetime_is_numeric=True).to_dict()
        }
        return analysis

    def generate_visualizations(self):
        """Create visualizations based on dataset characteristics."""
        plt.figure(figsize=(12, 6))

        # Correlation heatmap for numeric columns
        numeric_columns = self.df.select_dtypes(include=['float64', 'int64']).columns
        if not numeric_columns.empty:
            plt.subplot(1, 2, 1)
            correlation_matrix = self.df[numeric_columns].corr()
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5)
            plt.title('Correlation Heatmap')

        # Distribution plot of the first numeric column
        if len(numeric_columns) > 0:
            plt.subplot(1, 2, 2)
            sns.histplot(self.df[numeric_columns[0]], kde=True)
            plt.title(f'Distribution of {numeric_columns[0]}')

        plt.tight_layout()
        plt.savefig('data_analysis.png', dpi=300)
        plt.close()

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(2))
    def get_llm_insights(self, analysis_context):
        """Get concise insights from the LLM."""
        response = self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data science expert analyzing a dataset."},
                {"role": "user", "content": f"Here is the summary of my dataset analysis: {analysis_context}.\n"
                                              "Please provide insights, potential patterns, and recommendations."}
            ]
        )
        return response.choices[0].message.content

    def generate_markdown_report(self, llm_insights):
        """Generate a Markdown report with results."""
        with open('README.md', 'w') as f:
            f.write("# Data Analysis Report\n\n")
            f.write("## Dataset Overview\n")
            f.write(f"- **Total Rows**: {len(self.df)}\n")
            f.write(f"- **Total Columns**: {len(self.df.columns)}\n")
            f.write(f"- **Column Types**: {dict(self.df.dtypes)}\n\n")

            f.write("## LLM Insights\n")
            f.write(f"{llm_insights}\n\n")

            f.write("## Visualizations\n")
            f.write("![Data Analysis Visualization](data_analysis.png)\n")

    def run_analysis(self):
        """Main analysis workflow."""
        print("Performing basic analysis...")
        basic_analysis = self.basic_analysis()
        summarized_analysis = {
            'total_rows': basic_analysis['total_rows'],
            'total_columns': basic_analysis['total_columns'],
            'missing_values': {k: v for k, v in basic_analysis['missing_values'].items() if v > 0},
            'key_statistics': {k: basic_analysis['summary_statistics'].get(k) for k in basic_analysis['summary_statistics']}
        }

        print("Requesting insights from the LLM...")
        llm_insights = self.get_llm_insights(str(summarized_analysis))

        print("Generating visualizations...")
        self.generate_visualizations()

        print("Creating Markdown report...")
        self.generate_markdown_report(llm_insights)


def main(dataset_path):
    assistant = DataAnalysisAssistant(dataset_path)
    assistant.run_analysis()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset_path>")
        sys.exit(1)

    main(sys.argv[1])