"""Solve a Job-Shop instance with OR-Tools CP-SAT."""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ortools.sat.python import cp_model

from data import JobShopInstance
from model import ModelData, build_cp_model


@dataclass(frozen=True)
class OperationSchedule:
    job_id: str
    op_id: int
    machine: str
    start: int
    end: int
    duration: int
    label: str = ""


@dataclass(frozen=True)
class SolutionResult:
    status: str
    makespan: Optional[int]
    operations: List[OperationSchedule]
    solver_statistics: Dict[str, float]


def _status_name(status: int) -> str:
    mapping = {
        cp_model.OPTIMAL: "OPTIMAL",
        cp_model.FEASIBLE: "FEASIBLE",
        cp_model.INFEASIBLE: "INFEASIBLE",
        cp_model.MODEL_INVALID: "MODEL_INVALID",
        cp_model.UNKNOWN: "UNKNOWN",
    }
    return mapping.get(status, "UNKNOWN")


def solve(
    instance: JobShopInstance,
    time_limit: Optional[float] = None,
    num_workers: int = 8,
) -> SolutionResult:
    """Build the model, launch CP-SAT, and collect a structured solution."""
    model_data: ModelData = build_cp_model(instance)
    solver = cp_model.CpSolver()
    if time_limit and time_limit > 0:
        solver.parameters.max_time_in_seconds = time_limit
    if num_workers and num_workers > 0:
        solver.parameters.num_search_workers = num_workers

    status = solver.Solve(model_data.model)
    status_label = _status_name(status)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return SolutionResult(
            status=status_label,
            makespan=None,
            operations=[],
            solver_statistics={
                "wall_time": solver.WallTime(),
                "conflicts": solver.NumConflicts(),
                "branches": solver.NumBranches(),
            },
        )

    operations: List[OperationSchedule] = []
    for key, vars_bundle in model_data.task_vars.items():
        start = solver.Value(vars_bundle.start)
        end = solver.Value(vars_bundle.end)
        op = vars_bundle.operation
        operations.append(
            OperationSchedule(
                job_id=op.job_id,
                op_id=op.op_id,
                machine=op.machine,
                start=start,
                end=end,
                duration=op.duration,
                label=getattr(op, "label", f"Op {op.op_id}"),
            )
        )

    operations.sort(key=lambda op: (op.machine, op.start))
    makespan_value = solver.Value(model_data.makespan)

    return SolutionResult(
        status=status_label,
        makespan=makespan_value,
        operations=operations,
        solver_statistics={
            "wall_time": solver.WallTime(),
            "best_bound": solver.BestObjectiveBound(),
            "conflicts": solver.NumConflicts(),
            "branches": solver.NumBranches(),
        },
    )
