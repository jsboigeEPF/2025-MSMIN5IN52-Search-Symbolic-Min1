"""Data definitions and preloaded Job-Shop instances."""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple


@dataclass(frozen=True)
class OperationSpec:
    """Specification of an operation before assigning an identifier."""

    machine: str
    duration: int


@dataclass(frozen=True)
class Operation:
    job_id: str
    op_id: int
    machine: str
    duration: int
    label: str


@dataclass(frozen=True)
class MaintenanceWindow:
    machine: str
    start: int
    duration: int
    label: str = "Maintenance"


@dataclass(frozen=True)
class Job:
    job_id: str
    operations: List[Operation]


@dataclass(frozen=True)
class JobShopInstance:
    name: str
    jobs: List[Job]
    machines: List[str]
    description: str
    maintenance: List[MaintenanceWindow] = field(default_factory=list)


def _make_instance(
    name: str,
    job_sequences: Dict[str, List[Tuple[str, int] | Tuple[str, int, str]]],
    description: str,
    maintenance: List[MaintenanceWindow] | None = None,
) -> JobShopInstance:
    """Expand a dictionary of operation sequences into a full instance."""
    jobs: List[Job] = []
    machine_set = set()
    for job_id, ops in job_sequences.items():
        operations: List[Operation] = []
        for idx, op in enumerate(ops):
            if len(op) == 3:
                machine, duration, label = op  # type: ignore[misc]
            else:
                machine, duration = op  # type: ignore[misc]
                label = f"Etape {idx + 1}"
            operations.append(
                Operation(
                    job_id=job_id,
                    op_id=idx,
                    machine=machine,
                    duration=duration,
                    label=label,
                )
            )
        jobs.append(Job(job_id=job_id, operations=operations))
        for op in ops:
            machine_set.add(op[0])

    machines = sorted(machine_set)
    return JobShopInstance(
        name=name, jobs=jobs, machines=machines, description=description, maintenance=maintenance or []
    )


def get_instances() -> Dict[str, JobShopInstance]:
    """Provide a dictionary of named, ready-to-use instances."""
    fulfillment = _make_instance(
        name="preparation_commandes",
        job_sequences={
            "Commande e-commerce #A12": [
                ("Station de picking", 3, "Picking rayon"),
                ("Cellule d'emballage", 4, "Emballage carton"),
                ("Imprimante etiquette", 2, "Etiquetage + scan"),
            ],
            "Commande retail #B07": [
                ("Station de picking", 4, "Picking palettes"),
                ("Imprimante etiquette", 1, "Impression BL"),
                ("Cellule d'emballage", 3, "Filmage + scellage"),
            ],
            "Commande express #C21": [
                ("Imprimante etiquette", 2, "Etiquettes prioritaires"),
                ("Station de picking", 2, "Picking rapide"),
                ("Cellule d'emballage", 3, "Mise en caisse"),
            ],
        },
        description="Flux realiste: picking, emballage, etiquetage pour 3 commandes simultanees.",
    )

    fulfillment_maintenance = _make_instance(
        name="preparation_commandes_maintenance",
        job_sequences={
            "Commande e-commerce #A12": [
                ("Station de picking", 3, "Picking rayon"),
                ("Cellule d'emballage", 4, "Emballage carton"),
                ("Imprimante etiquette", 2, "Etiquetage + scan"),
            ],
            "Commande retail #B07": [
                ("Station de picking", 4, "Picking palettes"),
                ("Imprimante etiquette", 1, "Impression BL"),
                ("Cellule d'emballage", 3, "Filmage + scellage"),
            ],
            "Commande express #C21": [
                ("Imprimante etiquette", 2, "Etiquettes prioritaires"),
                ("Station de picking", 2, "Picking rapide"),
                ("Cellule d'emballage", 3, "Mise en caisse"),
            ],
        },
        maintenance=[
            MaintenanceWindow("Cellule d'emballage", start=2, duration=3, label="Maintenance filmage"),
            MaintenanceWindow("Imprimante etiquette", start=6, duration=2, label="Recharge papier"),
        ],
        description="Scenarion avec maintenance planifiee: station d'emballage et imprimante indisponibles sur des fenetres.",
    )

    fulfillment_rush = _make_instance(
        name="preparation_commandes_rush",
        job_sequences={
            "Commande e-commerce #A12": [
                ("Station de picking", 3, "Picking rayon"),
                ("Cellule d'emballage", 4, "Emballage carton"),
                ("Imprimante etiquette", 2, "Etiquetage + scan"),
            ],
            "Commande retail #B07": [
                ("Station de picking", 4, "Picking palettes"),
                ("Imprimante etiquette", 1, "Impression BL"),
                ("Cellule d'emballage", 3, "Filmage + scellage"),
            ],
            "Commande express #C21": [
                ("Imprimante etiquette", 2, "Etiquettes prioritaires"),
                ("Station de picking", 2, "Picking rapide"),
                ("Cellule d'emballage", 3, "Mise en caisse"),
            ],
            "Commande flash #R99": [
                ("Imprimante etiquette", 1, "Etiquette prioritaire"),
                ("Station de picking", 2, "Picking urgence"),
                ("Cellule d'emballage", 2, "Emballage express"),
            ],
        },
        description="Scenario avec commande flash R99 a insérer en urgence dans le flux.",
    )

    didactic = _make_instance(
        name="didactic_3x3",
        job_sequences={
            "Job A": [("M1", 3), ("M2", 2), ("M3", 2)],
            "Job B": [("M2", 2), ("M3", 1), ("M1", 4)],
            "Job C": [("M3", 4), ("M1", 3), ("M2", 1)],
        },
        description="Instance pedagogique: 3 jobs, 3 machines, ordres entrelaces.",
    )

    alternating = _make_instance(
        name="alternating_3x3",
        job_sequences={
            "Job X": [("M1", 2), ("M3", 5), ("M2", 3)],
            "Job Y": [("M2", 4), ("M1", 1), ("M3", 4)],
            "Job Z": [("M3", 3), ("M2", 2), ("M1", 6)],
        },
        description="Instance alternative pour comparer l'effet des ordres machines.",
    )

    return {
        fulfillment.name: fulfillment,
        fulfillment_maintenance.name: fulfillment_maintenance,
        fulfillment_rush.name: fulfillment_rush,
        didactic.name: didactic,
        alternating.name: alternating,
    }


def instance_horizon(instance: JobShopInstance) -> int:
    """Upper bound on the schedule horizon (sum of all processing times)."""
    op_sum = sum(op.duration for job in instance.jobs for op in job.operations)
    maint_sum = sum(m.duration for m in instance.maintenance)
    maint_far_end = max((m.start + m.duration for m in instance.maintenance), default=0)
    return max(op_sum + maint_sum, maint_far_end)
