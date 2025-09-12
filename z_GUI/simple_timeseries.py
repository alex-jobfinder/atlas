#!/usr/bin/env python3
"""
Simple Timeseries Plot - DearPyGUI
Minimal app to render timeseries plot for campaign performance data
"""

import dearpygui.dearpygui as dpg
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import io
from datetime import datetime
import sys
import os

class SimpleTimeseriesApp:
    def __init__(self, database_path: str = "ads.db"):
        self.database_path = database_path
        self.connection = None
        self.data = None

        # Initialize DearPyGUI
        dpg.create_context()

        # Create the main window
        self.create_main_window()

    def create_main_window(self):
        """Create the main application window."""
        with dpg.window(label="Simple Timeseries Plot", width=1000, height=700, tag="main_window"):

            # Title
            dpg.add_text("Campaign Performance Timeseries", color=[255, 255, 0])
            dpg.add_separator()

            # Control buttons
            with dpg.group(horizontal=True):
                dpg.add_button(label="Load Data", callback=self.load_data)
                dpg.add_button(label="Generate Plot", callback=self.generate_plot)
                dpg.add_button(label="Clear Plot", callback=self.clear_plot)

            dpg.add_spacer(height=10)

            # Status text
            dpg.add_text("Click 'Load Data' to load campaign performance data", tag="status_text")

            dpg.add_spacer(height=10)

            # Create texture registry for the plot
            with dpg.texture_registry():
                dpg.add_raw_texture(
                    width=900,
                    height=500,
                    default_value=[0.0] * (900 * 500 * 4),
                    format=dpg.mvFormat_Float_rgba,
                    tag="plot_texture"
                )

            # Display the plot image
            dpg.add_image("plot_texture", width=900, height=500, tag="plot_image")

            # Data info
            dpg.add_text("Data Info:", tag="data_info")

    def load_data(self):
        """Load data from the database."""
        try:
            # Connect to database
            self.connection = sqlite3.connect(self.database_path)
            dpg.set_value("status_text", "Connected to database")

            # Execute query
            query = "SELECT hour_ts, hour_unix_epoch, impressions FROM campaign_performance WHERE campaign_id = 1 ORDER BY hour_unix_epoch ASC"
            self.data = pd.read_sql_query(query, self.connection)

            dpg.set_value("status_text", f"Loaded {len(self.data)} data points")
            dpg.set_value("data_info", f"Data points: {len(self.data)}\nColumns: {list(self.data.columns)}")

            print(f"DEBUG: Loaded {len(self.data)} rows")
            print(f"DEBUG: Columns: {list(self.data.columns)}")
            print(f"DEBUG: First few rows:")
            print(self.data.head())

        except Exception as e:
            dpg.set_value("status_text", f"Error loading data: {str(e)}")
            print(f"DEBUG: Error loading data: {e}")
            self.data = None

    def generate_plot(self):
        """Generate the timeseries plot."""
        if self.data is None or len(self.data) == 0:
            dpg.set_value("status_text", "No data loaded. Click 'Load Data' first.")
            return

        try:
            dpg.set_value("status_text", "Generating plot...")

            # Create the plot
            fig, ax = plt.subplots(figsize=(12, 6))

            # Convert hour_ts to datetime
            x_data = pd.to_datetime(self.data['hour_ts'])
            y_data = self.data['impressions']

            # Plot the data
            ax.plot(x_data, y_data, color='blue', linewidth=2, marker='o', markersize=4)

            # Formatting
            ax.set_xlabel('Time')
            ax.set_ylabel('Impressions')
            ax.set_title('Campaign Performance - Impressions Over Time')
            ax.grid(True, alpha=0.3)

            # Format x-axis for dates
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H:%M'))
            ax.xaxis.set_major_locator(mdates.HourLocator(interval=6))
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

            plt.tight_layout()

            # Convert plot to texture
            self.plot_to_texture(fig)

            dpg.set_value("status_text", "Plot generated successfully!")

            plt.close(fig)

        except Exception as e:
            dpg.set_value("status_text", f"Error generating plot: {str(e)}")
            print(f"DEBUG: Error generating plot: {e}")

    def plot_to_texture(self, fig):
        """Convert matplotlib figure to DearPyGUI texture."""
        try:
            # Save plot to bytes
            buf = io.BytesIO()
            fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
            buf.seek(0)

            # Read image data
            import PIL.Image as Image
            img = Image.open(buf)
            img = img.convert('RGBA')

            # Resize to texture size
            img = img.resize((900, 500), Image.Resampling.LANCZOS)

            # Convert to numpy array
            img_array = np.array(img)

            # Normalize to 0-1 range
            img_array = img_array.astype(np.float32) / 255.0

            # Flatten for DearPyGUI
            img_data = img_array.flatten()

            # Update texture
            dpg.set_value("plot_texture", img_data)

            print("DEBUG: Plot converted to texture successfully")

        except Exception as e:
            print(f"DEBUG: Error converting plot to texture: {e}")

    def clear_plot(self):
        """Clear the plot display."""
        dpg.set_value("status_text", "Plot cleared")
        dpg.set_value("data_info", "Data Info:")
        # Clear texture
        dpg.set_value("plot_texture", [0.0] * (900 * 500 * 4))

    def run(self):
        """Run the application."""
        # Create viewport
        dpg.create_viewport(title="Simple Timeseries Plot", width=1000, height=700)
        dpg.setup_dearpygui()

        # Show viewport
        dpg.show_viewport()

        # Main render loop
        while dpg.is_dearpygui_running():
            dpg.render_dearpygui_frame()

        # Cleanup
        dpg.destroy_context()

def main():
    """Main function to run the application."""
    if len(sys.argv) > 1:
        database_path = sys.argv[1]
    else:
        database_path = "ads.db"

    if not os.path.exists(database_path):
        print(f"Database file '{database_path}' not found!")
        print("Usage: python simple_timeseries.py [database_path]")
        return

    app = SimpleTimeseriesApp(database_path)
    app.run()

if __name__ == "__main__":
    main()
