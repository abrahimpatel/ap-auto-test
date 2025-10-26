#!/usr/bin/env python3
import argparse
import os
import pandas as pd
import plotly.graph_objects as go
import plotly.subplots as sp
from jinja2 import Template
import json
import traceback

class JMeterReportGenerator:
    def __init__(self, input_file, output_dir="."):
        self.input_file = input_file
        self.output_dir = output_dir
        self.output_dir = output_dir
        self.df = None
        self.create_output_dir()

    def create_output_dir(self):
        """Create output directory if it doesn't exist"""
        try:
            # Convert relative path to absolute path if necessary
            self.output_dir = os.path.abspath(self.output_dir)
            print(f"\nCreating output directory: {self.output_dir}")
            
            # If output_dir is a file path with .html extension, extract the directory
            if self.output_dir.endswith('.html'):
                self.output_dir = os.path.dirname(self.output_dir)
                
            if not os.path.exists(self.output_dir):
                os.makedirs(self.output_dir)
                print(f"Created directory: {self.output_dir}")
            else:
                print(f"Directory already exists: {self.output_dir}")
        except Exception as e:
            print(f"Error creating output directory: {str(e)}")
#add in the 
    def read_csv(self):
        """Read JMeter CSV file into pandas DataFrame"""
        try:
            # Read CSV file and print its structure
            print(f"Attempting to read CSV file: {self.input_file}")
            self.df = pd.read_csv(self.input_file)
            print("\nCSV Columns found:", self.df.columns.tolist())
            print("\nFirst few rows of data:")
            print(self.df.head(2))
            
            # Verify required columns exist
            required_columns = ['timeStamp', 'elapsed', 'success', 'responseCode']
            missing_columns = [col for col in required_columns if col not in self.df.columns]
            if missing_columns:
                print(f"\nError: Missing required columns: {', '.join(missing_columns)}")
                print(f"Available columns are: {', '.join(self.df.columns)}")
                return False
            
            # Convert timestamp to datetime
            try:
                print("\nConverting timestamp column...")
                self.df['timeStamp'] = pd.to_datetime(self.df['timeStamp'], unit='ms')
            except Exception as e:
                print(f"Error converting timestamp: {str(e)}")
                print("Sample timestamp values:", self.df['timeStamp'].head())
                return False
            
            # Convert elapsed to numeric and from milliseconds to seconds
            try:
                print("\nConverting elapsed time to seconds...")
                self.df['elapsed'] = pd.to_numeric(self.df['elapsed'], errors='coerce')
                print("Sample elapsed times (ms):", self.df['elapsed'].head())
                # Check for any NaN values after conversion
                if self.df['elapsed'].isna().any():
                    print("Warning: Some response times could not be converted to numbers")
                    print("Rows with invalid elapsed times:", 
                          self.df[self.df['elapsed'].isna()].index.tolist())
                self.df['elapsed'] = self.df['elapsed'] / 1000.0
                print("Sample elapsed times (s):", self.df['elapsed'].head())
            except Exception as e:
                print(f"Error converting response times: {str(e)}")
                return False
            
            # Ensure success column is boolean
            try:
                print("\nConverting success column to boolean...")
                self.df['success'] = self.df['success'].astype(bool)
            except Exception as e:
                print(f"Error converting success column: {str(e)}")
                print("Sample success values:", self.df['success'].head())
                return False
            
            print("\nCSV file processed successfully!")
            return True
        except Exception as e:
            print(f"\nError processing CSV data: {str(e)}")
            return False

        except Exception as e:
            print(f"\nError reading CSV file: {str(e)}")
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
            yaxis_title='Response Time (s)',
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
        try:
            def safe_round(value):
                try:
                    return round(float(value), 2)
                except:
                    return 0.0

            stats = {
                'Total Requests': len(self.df),
                'Average Response Time (s)': safe_round(self.df['elapsed'].mean()),
                'Median Response Time (s)': safe_round(self.df['elapsed'].median()),
                'Min Response Time (s)': safe_round(self.df['elapsed'].min()),
                'Max Response Time (s)': safe_round(self.df['elapsed'].max()),
                'Success Rate (%)': safe_round(self.df['success'].mean() * 100),
                '90th Percentile (s)': safe_round(self.df['elapsed'].quantile(0.90)),
                '95th Percentile (s)': safe_round(self.df['elapsed'].quantile(0.95)),
                '99th Percentile (s)': safe_round(self.df['elapsed'].quantile(0.99))
            }
            return stats
        except Exception as e:
            print(f"Error calculating statistics: {str(e)}")
            return {
                'Total Requests': len(self.df),
                'Error': 'Unable to calculate complete statistics'
            }

    def process_csv_data(self):
        """Process the CSV data and calculate statistics"""
        try:
            print(f"\nReading CSV file: {self.input_file}...")
            self.df = pd.read_csv(self.input_file)
            
            # Convert timestamp to datetime
            print("Converting timestamp column...")
            self.df['timeStamp'] = pd.to_datetime(self.df['timeStamp'], unit='ms')
            
            # Convert elapsed time to seconds
            print("Converting elapsed time to seconds...")
            self.df['elapsed'] = pd.to_numeric(self.df['elapsed']) / 1000.0
            # Ensure success column is boolean
            try:
                print("Converting success column to boolean...")
                self.df['success'] = self.df['success'].astype(bool)
            except Exception as e:
                print(f"Error converting success column: {str(e)}")
                print("Sample success values:", self.df['success'].head())
                return False

            print("\nCSV file processed successfully!")
            return True
        except Exception as e:
            print(f"\nError processing CSV data: {str(e)}")
            return False

    def generate_html_report(self):
        """Generate HTML report with graphs and statistics"""
        try:
            print("\nGenerating HTML report...")
            
            # Generate graphs
            print("Generating response time graph...")
            response_time_graph = self.generate_response_time_graph()
            response_time_div = response_time_graph.to_html(full_html=False)
            
            print("Generating throughput graph...")
            throughput_graph = self.generate_throughput_graph()
            throughput_div = throughput_graph.to_html(full_html=False)
            
            print("Generating error distribution graph...")
            error_dist_graph = self.generate_error_distribution()
            error_dist_div = error_dist_graph.to_html(full_html=False)
            
            # Calculate statistics
            print("Calculating statistics...")
            stats = self.calculate_statistics()
            print("Statistics calculated:", stats)

            # Create stats HTML
            stats_divs = []
            for key, value in stats.items():
                stats_divs.append(f'<div class="stat-box"><div class="stat-value">{value}</div><div class="stat-label">{key}</div></div>')
            stats_html = '\n'.join(stats_divs)

            # Create HTML content
            print("Creating HTML content...")
            # Create HTML content
            # Build HTML content programmatically to avoid syntax issues
            style = (
                'body{font-family:Arial,sans-serif;margin:20px}'
                '.container{max-width:1200px;margin:0 auto}'
                '.stats-container{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:20px;margin-bottom:30px}'
                '.stat-box{background:#f5f5f5;padding:15px;border-radius:5px;text-align:center}'
                '.stat-value{font-size:24px;font-weight:bold}'
                '.stat-label{font-size:14px;color:#666}'
            )
            
            html_content = ''.join([
                '<!DOCTYPE html>',
                '<html>',
                '<head>',
                '<title>JMeter Test Results</title>',
                '<style>',
                style,
                '</style>',
                '</head>',
                '<body>',
                '<div class="container">',
                '<h1>JMeter Test Results Report</h1>',
                '<div class="stats-container">',
                stats_html,
                '</div>',
                '<h2>Response Time Graph</h2>',
                response_time_div,
                '<h2>Throughput Graph</h2>',
                throughput_div,
                '<h2>Response Code Distribution</h2>',
                error_dist_div,
                '</div>',
                '</body>',
                '</html>'
            ])
            
            # Write the HTML content to the output file
            output_path = os.path.join(self.output_dir, "jmeter_report.html")
            print(f"Writing HTML report to {output_path}...")
            os.makedirs(self.output_dir, exist_ok=True)
            with open(output_path, "w") as f:
                f.write(html_content)

            # (HTML already generated and written above; skipping Jinja rendering)
            print(f"Report generated successfully at: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"Error generating report: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            raise

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
