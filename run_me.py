#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from jinja2 import Template
import json

class JMeterReportGenerator:
    def __init__(self, csv_file, output_dir):
        self.csv_file = csv_file
        self.output_dir = output_dir
        self.df = None
        self.create_output_dir()

    def create_output_dir(self):
        """Create output directory if it doesn't exist"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

    def read_csv(self):
        """Read JMeter CSV file into pandas DataFrame"""
        try:
            self.df = pd.read_csv(self.csv_file)
            # Convert timestamp to datetime
            self.df['timeStamp'] = pd.to_datetime(self.df['timeStamp'], unit='ms')
            return True
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
            return False

    def generate_response_time_graph(self):
        """Generate response time graph"""
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=self.df['timeStamp'],
            y=self.df['elapsed'],
            mode='lines+markers',
            name='Response Time'
        ))
        fig.update_layout(
            title='Response Time Over Time',
            xaxis_title='Time',
            yaxis_title='Response Time (ms)',
            template='plotly_white'
        )
        return fig

    def generate_throughput_graph(self):
        """Generate throughput graph (requests per second)"""
        throughput = self.df.groupby(pd.Timestamp.floor(self.df['timeStamp'], '1S')).size()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=throughput.index,
            y=throughput.values,
            mode='lines',
            name='Throughput'
        ))
        fig.update_layout(
            title='Throughput (Requests per Second)',
            xaxis_title='Time',
            yaxis_title='Requests/Second',
            template='plotly_white'
        )
        return fig

    def generate_error_distribution(self):
        """Generate error distribution pie chart"""
        error_dist = self.df['responseCode'].value_counts()
        fig = go.Figure(data=[go.Pie(
            labels=error_dist.index,
            values=error_dist.values,
            hole=.3
        )])
        fig.update_layout(
            title='Response Code Distribution'
        )
        return fig

    def calculate_statistics(self):
        """Calculate basic statistics"""
        stats = {
            'Total Requests': len(self.df),
            'Average Response Time': round(self.df['elapsed'].mean(), 2),
            'Median Response Time': round(self.df['elapsed'].median(), 2),
            'Min Response Time': round(self.df['elapsed'].min(), 2),
            'Max Response Time': round(self.df['elapsed'].max(), 2),
            'Success Rate': round((self.df['success'].mean() * 100), 2),
            '90th Percentile': round(self.df['elapsed'].quantile(0.90), 2),
            '95th Percentile': round(self.df['elapsed'].quantile(0.95), 2),
            '99th Percentile': round(self.df['elapsed'].quantile(0.99), 2)
        }
        return stats

    def generate_html_report(self):
        """Generate HTML report with graphs and statistics"""
        # Generate graphs
        response_time_graph = self.generate_response_time_graph()
        throughput_graph = self.generate_throughput_graph()
        error_dist_graph = self.generate_error_distribution()
        
        # Calculate statistics
        stats = self.calculate_statistics()

        # HTML template
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>JMeter Test Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .container { max-width: 1200px; margin: 0 auto; }
                .stats-container {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-box {
                    background: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    text-align: center;
                }
                .stat-value { font-size: 24px; font-weight: bold; }
                .stat-label { font-size: 14px; color: #666; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>JMeter Test Results Report</h1>
                
                <h2>Performance Statistics</h2>
                <div class="stats-container">
                    {% for key, value in stats.items() %}
                    <div class="stat-box">
                        <div class="stat-value">{{ value }}</div>
                        <div class="stat-label">{{ key }}</div>
                    </div>
                    {% endfor %}
                </div>

                <h2>Response Time Graph</h2>
                {{ response_time_div }}

                <h2>Throughput Graph</h2>
                {{ throughput_div }}

                <h2>Response Code Distribution</h2>
                {{ error_dist_div }}
            </div>
        </body>
        </html>
        """

        # Create template
        template = Template(html_template)

        # Generate HTML
        html_content = template.render(
            stats=stats,
            response_time_div=response_time_graph.to_html(full_html=False),
            throughput_div=throughput_graph.to_html(full_html=False),
            error_dist_div=error_dist_graph.to_html(full_html=False)
        )

        # Write HTML file
        report_path = os.path.join(self.output_dir, 'jmeter_report.html')
        with open(report_path, 'w') as f:
            f.write(html_content)
        
        return report_path

def main():
    parser = argparse.ArgumentParser(description='Generate HTML report from JMeter CSV results')
    parser.add_argument('csv_file', help='Path to JMeter CSV result file')
    parser.add_argument('output_dir', help='Directory to store the generated report')
    
    args = parser.parse_args()

    # Create report generator instance
    generator = JMeterReportGenerator(args.csv_file, args.output_dir)
    
    # Read CSV file
    if not generator.read_csv():
        return

    # Generate report
    try:
        report_path = generator.generate_html_report()
        print(f"Report generated successfully at: {report_path}")
    except Exception as e:
        print(f"Error generating report: {str(e)}")

if __name__ == '__main__':
    main()
