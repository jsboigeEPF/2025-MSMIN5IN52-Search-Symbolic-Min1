"""CP-SAT model for the Job-Shop Scheduling problem."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Tuple

from ortools.sat.python import cp_model

from data import JobShopInstance, Operation, MaintenanceWindow, instance_horizon

# Configure logging
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class TaskVars:
    """Bundle for the CP-SAT variables associated to one operation."""

    operation: Operation
    start: cp_model.IntVar
    end: cp_model.IntVar
    interval: cp_model.IntervalVar


@dataclass(frozen=True)
class ModelData:
    """Structure returned after model construction."""

    model: cp_model.CpModel
    task_vars: Dict[Tuple[str, int], TaskVars]
    makespan: cp_model.IntVar
    horizon: int


def _safe_name(raw: str) -> str:
    """Sanitize identifiers for OR-Tools variable naming."""
    return raw.replace(" ", "_").replace("-", "_").lower()


def build_cp_model(instance: JobShopInstance) -> ModelData:
    """Create the CP-SAT model with precedence and machine constraints.
    
    Constructs a constraint programming model with:
    - Interval variables for each operation
    - Precedence constraints within jobs
    - No-overlap constraints per machine
    - Maintenance window constraints
    - Makespan minimization objective
    
    Args:
        instance: The job shop instance to model
        
    Returns:
        ModelData: Bundle containing the model, variables, and horizon
        
    Raises:
        ValueError: If instance contains invalid data
    """
    logger.info(f"Building CP-SAT model for instance '{instance.name}'")
    model = cp_model.CpModel()
    horizon = instance_horizon(instance)
    task_vars: Dict[Tuple[str, int], TaskVars] = {}
    machine_to_intervals: Dict[str, list] = {machine: [] for machine in instance.machines}

    for job in instance.jobs:
        safe_job = _safe_name(job.job_id)
        for op in job.operations:
            start = model.NewIntVar(0, horizon, f"start_{safe_job}_{op.op_id}")
            end = model.NewIntVar(0, horizon, f"end_{safe_job}_{op.op_id}")
            interval = model.NewIntervalVar(
                start, op.duration, end, f"interval_{safe_job}_{op.op_id}"
            )
            vars_bundle = TaskVars(operation=op, start=start, end=end, interval=interval)
            task_vars[(op.job_id, op.op_id)] = vars_bundle
            machine_to_intervals[op.machine].append(interval)

    for job in instance.jobs:
        for first, second in zip(job.operations, job.operations[1:]):
            model.Add(task_vars[(first.job_id, first.op_id)].end <= task_vars[(second.job_id, second.op_id)].start)

    # Maintenance windows: add fixed intervals to the corresponding machines (before NoOverlap).
    for maint in instance.maintenance or []:
        start = model.NewIntVar(maint.start, maint.start, f"maint_start_{_safe_name(maint.label)}")
        end = model.NewIntVar(
            maint.start + maint.duration,
            maint.start + maint.duration,
            f"maint_end_{_safe_name(maint.label)}",
        )
        interval = model.NewIntervalVar(start, maint.duration, end, f"maint_{_safe_name(maint.label)}")
        machine_to_intervals[maint.machine].append(interval)

    for machine, intervals in machine_to_intervals.items():
        model.AddNoOverlap(intervals)

    makespan = model.NewIntVar(0, horizon, "makespan")
    for job in instance.jobs:
        last_op = job.operations[-1]
        model.Add(task_vars[(last_op.job_id, last_op.op_id)].end <= makespan)

    model.Minimize(makespan)
    return ModelData(model=model, task_vars=task_vars, makespan=makespan, horizon=horizon)
