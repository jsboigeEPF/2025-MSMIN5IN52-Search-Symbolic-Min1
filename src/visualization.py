"""Visualization utilities (Plotly + Streamlit-friendly)."""

from pathlib import Path
from typing import Optional, List

import pandas as pd
import plotly.express as px

from solver import SolutionResult
from data import MaintenanceWindow


def operations_dataframe(
    solution: SolutionResult, maintenance: Optional[List[MaintenanceWindow]] = None
) -> pd.DataFrame:
    """Turn the schedule into a table ready for plotting or inspection."""
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


def gantt_figure(solution: SolutionResult, maintenance: Optional[List[MaintenanceWindow]] = None, x_max: Optional[int] = None):
    """Return a Plotly timeline figure for the computed schedule."""
    df = operations_dataframe(solution, maintenance=maintenance)
    if df.empty:
        return None

    palette = px.colors.qualitative.Set2 + px.colors.qualitative.Set3
    color_map = {"Maintenance": "#94a3b8"}
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
        color_discrete_sequence=palette,
        color_discrete_map=color_map,
        category_orders={"type": ["maintenance", "operation"]},
    )
    fig.update_yaxes(title_text="Ressource", autorange="reversed")
    fig.update_xaxes(title_text="Temps (unites)", type="linear", tick0=0, dtick=1)
    fig.update_traces(marker_line_color="black", marker_line_width=0.6)

    if solution.makespan is not None:
        fig.add_vline(
            x=solution.makespan,
            line_width=2,
            line_dash="dot",
            line_color="firebrick",
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


def save_figure(fig, path: str = "output/gantt.png") -> Path:
    """Export the Plotly figure to PNG using Kaleido."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    fig.write_image(str(destination))
    return destination
