"""Visualization utilities (Plotly + Streamlit-friendly)."""

import logging
from pathlib import Path
from typing import Optional, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from solver import SolutionResult
from data import MaintenanceWindow

# Configure logging
logger = logging.getLogger(__name__)

# Visualization constants
DEFAULT_GANTT_HEIGHT = 520
DEFAULT_OUTPUT_PATH = "output/gantt.png"
MAINTENANCE_COLOR = "#94a3b8"
MAKESPAN_LINE_COLOR = "firebrick"
MARKER_LINE_WIDTH = 0.6
COLOR_PALETTE = px.colors.qualitative.Set2 + px.colors.qualitative.Set3


def operations_dataframe(
    solution: SolutionResult, maintenance: Optional[List[MaintenanceWindow]] = None
) -> pd.DataFrame:
    """Convert solution into a pandas DataFrame for visualization.
    
    Args:
        solution: The solver result containing scheduled operations
        maintenance: Optional list of maintenance windows to include
        
    Returns:
        pd.DataFrame: Table with columns for job, machine, start, end, duration, etc.
    """
    if not solution.operations and not maintenance:
        logger.warning("No operations or maintenance to display")
        return pd.DataFrame()
    records = [
        {
            "job": op.job_id,
            "operation": op.op_id,
            "etape": getattr(op, "label", f"Op {op.op_id}"),
            "machine": op.machine,
            "start": op.start,
            "end": op.end,
            "duration": op.duration,
            "label": f"{op.job_id} • {getattr(op, 'label', f'Op {op.op_id}')}",
            "type": "operation",
        }
        for op in solution.operations
    ]
    for maint in maintenance or []:
        records.append(
            {
                "job": "Maintenance",
                "operation": "-",
                "etape": maint.label,
                "machine": maint.machine,
                "start": maint.start,
                "end": maint.start + maint.duration,
                "duration": maint.duration,
                "label": f"Maintenance • {maint.label}",
                "type": "maintenance",
            }
        )
    df = pd.DataFrame.from_records(records)
    if not df.empty:
        df.sort_values(["machine", "start"], inplace=True)
    return df


def gantt_figure(
    solution: SolutionResult, 
    maintenance: Optional[List[MaintenanceWindow]] = None, 
    x_max: Optional[int] = None
) -> Optional[go.Figure]:
    """Create a Plotly Gantt chart for the schedule.
    
    Args:
        solution: The solver result to visualize
        maintenance: Optional maintenance windows to display
        x_max: Maximum x-axis value (for zoom control)
        
    Returns:
        Plotly Figure object or None if no data to display
    """
    try:
        df = operations_dataframe(solution, maintenance=maintenance)
        if df.empty:
            logger.warning("No data to plot in Gantt chart")
            return None

        color_map = {"Maintenance": MAINTENANCE_COLOR}
        fig = px.timeline(
            df,
            x_start="start",
            x_end="end",
            y="machine",
            color="job",
            text="label",
            hover_data={
                "job": True,
                "operation": True,
                "etape": True,
                "machine": True,
                "duration": True,
                "start": True,
                "end": True,
            },
            color_discrete_sequence=COLOR_PALETTE,
            color_discrete_map=color_map,
            category_orders={"type": ["maintenance", "operation"]},
        )
        fig.update_yaxes(title_text="Ressource", autorange="reversed")
        fig.update_xaxes(title_text="Temps (unites)", type="linear", tick0=0, dtick=1)
        fig.update_traces(marker_line_color="black", marker_line_width=MARKER_LINE_WIDTH)

        if solution.makespan is not None:
            fig.add_vline(
                x=solution.makespan,
                line_width=2,
                line_dash="dot",
                line_color=MAKESPAN_LINE_COLOR,
                annotation_text=f"Makespan = {solution.makespan}",
                annotation_position="top right",
            )

        if x_max is not None:
            fig.update_xaxes(range=[0, x_max])

        fig.update_layout(
            legend_title_text="Job",
            hoverlabel_align="left",
            margin=dict(l=40, r=40, t=60, b=40),
        )
        fig.update_traces(text=None)
        return fig
    except Exception as e:
        logger.error(f"Error creating Gantt figure: {e}")
        return None


def save_figure(fig: go.Figure, path: str = DEFAULT_OUTPUT_PATH) -> Path:
    """Export the Plotly figure to PNG using Kaleido.
    
    Args:
        fig: The Plotly figure to export
        path: Output file path (default: output/gantt.png)
        
    Returns:
        Path: The destination path where the figure was saved
        
    Raises:
        IOError: If the figure cannot be saved
    """
    try:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        fig.write_image(str(destination))
        logger.info(f"Saved Gantt chart to {destination}")
        return destination
    except Exception as e:
        logger.error(f"Failed to save figure to {path}: {e}")
        raise IOError(f"Could not save figure: {e}") from e
