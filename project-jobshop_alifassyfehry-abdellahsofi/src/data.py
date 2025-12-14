"""Data definitions and preloaded Job-Shop scenarios."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Union

OperationTuple = Union[Tuple[str, int], Tuple[str, int, str]]
JobSequences = Dict[str, List[OperationTuple]]


@dataclass(frozen=True)
class OperationSpec:
    machine: str
    duration: int


@dataclass(frozen=True)
class Operation:
    job_id: str
    op_id: int
    machine: str
    duration: int
    label: str
    setup_time: int = 0


@dataclass(frozen=True)
class MaintenanceWindow:
    machine: str
    start: int
    duration: int
    label: str = "Maintenance"
    is_recurring: bool = False
    recurrence_interval: Optional[int] = None


@dataclass(frozen=True)
class Job:
    job_id: str
    operations: List[Operation]
    priority: int = 3
    deadline: Optional[int] = None
    release_time: int = 0


@dataclass(frozen=True)
class JobShopInstance:
    name: str
    jobs: List[Job]
    machines: List[str]
    description: str
    maintenance: List[MaintenanceWindow] = field(default_factory=list)
    created_at: Optional[str] = None
    is_custom: bool = False


def _make_instance(
    name: str,
    job_sequences: JobSequences,
    description: str,
    maintenance: Optional[List[MaintenanceWindow]] = None,
) -> JobShopInstance:
    if not job_sequences:
        raise ValueError("job_sequences cannot be empty")
    jobs: List[Job] = []
    machine_set = set()
    for job_id, ops in job_sequences.items():
        operations: List[Operation] = []
        for idx, op in enumerate(ops):
            if len(op) == 3:
                machine, duration, label = op  # type: ignore[misc]
            elif len(op) == 2:
                machine, duration = op  # type: ignore[misc]
                label = f"Etape {idx + 1}"
            else:
                raise ValueError(f"Invalid operation format in job {job_id}: {op}")
            if duration <= 0:
                raise ValueError(f"Duration must be positive for {job_id} operation {idx}")
            operations.append(
                Operation(
                    job_id=job_id,
                    op_id=idx,
                    machine=machine,
                    duration=duration,
                    label=label,
                )
            )
            machine_set.add(machine)
        jobs.append(Job(job_id=job_id, operations=operations))

    machines = sorted(machine_set)
    return JobShopInstance(
        name=name,
        jobs=jobs,
        machines=machines,
        description=description,
        maintenance=maintenance or [],
    )


def _build_rush(total: int, express: int = 20, click_collect: int = 30) -> JobSequences:
    jobs: JobSequences = {}
    for i in range(1, express + 1):
        jobs[f"Express #{i:03d}"] = [
            ("Reception", 1, "Reception express"),
            ("Tri prioritaire", 1, "Tri express"),
            ("Picking zone B", 2, "Picking express"),
            ("Controle qualite", 1, "QC express"),
            ("Etiquetage", 1, "Etiquette express"),
            ("Tri tournee", 1, "Affectation rapide"),
            ("Chargement quai", 1, "Chargement prioritaire"),
        ]
    for i in range(1, click_collect + 1):
        jobs[f"ClickCollect #{i:03d}"] = [
            ("Reception", 1, "Reception commande"),
            ("Tri standard", 1, "Tri C&C"),
            ("Picking zone B", 2, "Picking rapide"),
            ("Kitting", 2, "Assemblage commande"),
            ("Controle qualite", 1, "QC C&C"),
            ("Etiquetage", 1, "Etiquette retrait"),
            ("Zone retrait", 1, "Depot casier"),
        ]
    store_count = max(total - express - click_collect, 0)
    for i in range(1, store_count + 1):
        jobs[f"Magasin #{i:03d}"] = [
            ("Reception", 2, "Reception palette"),
            ("Tri standard", 2, "Tri magasin"),
            ("Picking zone A", 3, "Picking volumineux"),
            ("Kitting", 3, "Assemblage palette"),
            ("Controle qualite", 2, "QC complet"),
            ("Etiquetage", 1, "Etiquette magasin"),
            ("Filmage palette", 2, "Filmage"),
            ("Tri tournee", 2, "Affectation tournee"),
            ("Chargement quai", 2, "Chargement camion"),
        ]
    return jobs


def get_instances() -> Dict[str, JobShopInstance]:
    """Provide a dictionary of named, ready-to-use scenarios."""

    def base_steps(include_flash: bool = False) -> JobSequences:
        steps: JobSequences = {
            "Commande retail #R01": [
                ("Reception", 2, "Reception palette"),
                ("Tri standard", 2, "Tri zone magasin"),
                ("Picking zone A", 3, "Picking rayon sec"),
                ("Kitting", 2, "Assemblage lot"),
                ("Controle qualite", 2, "QC visuel"),
                ("Etiquetage", 1, "Etiquette BL"),
                ("Emballage", 3, "Carton + calage"),
                ("Filmage palette", 2, "Film et cerclage"),
                ("Tri tournee", 2, "Affectation tournee"),
                ("Chargement quai", 2, "Chargement quai nord"),
            ],
            "Commande e-commerce #E12": [
                ("Reception", 1, "Scan colis"),
                ("Tri standard", 1, "Tri e-commerce"),
                ("Picking zone B", 3, "Picking petit colis"),
                ("Controle qualite", 1, "QC express"),
                ("Etiquetage", 1, "Etiquette transport"),
                ("Emballage", 2, "Carton e-commerce"),
                ("Tri tournee", 1, "Dispatch transporteurs"),
                ("Chargement quai", 2, "Chargement quai sud"),
            ],
            "Commande click&collect #C05": [
                ("Reception", 1, "Reception client"),
                ("Tri standard", 1, "Tri C&C"),
                ("Picking zone B", 2, "Picking rapide"),
                ("Kitting", 2, "Assemblage commande"),
                ("Controle qualite", 1, "QC C&C"),
                ("Etiquetage", 1, "Etiquette retrait"),
                ("Emballage", 2, "Sac ou carton"),
                ("Zone retrait", 1, "Depot casier"),
            ],
            "Commande magasin #M20": [
                ("Reception", 2, "Reception BL"),
                ("Tri standard", 2, "Tri multi-magasin"),
                ("Picking zone A", 4, "Picking volumineux"),
                ("Kitting", 3, "Assemblage palettes"),
                ("Controle qualite", 2, "QC complet"),
                ("Etiquetage", 1, "Etiquettes magasin"),
                ("Filmage palette", 3, "Filmage renforce"),
                ("Tri tournee", 2, "Dispatch tournees"),
                ("Chargement quai", 2, "Chargement quai central"),
            ],
        }
        if include_flash:
            steps["Commande flash #F01"] = [
                ("Reception", 1, "Reception prioritaire"),
                ("Tri prioritaire", 1, "Tri express"),
                ("Picking zone B", 2, "Picking urgence"),
                ("Controle qualite", 1, "QC express"),
                ("Etiquetage", 1, "Etiquette prioritaire"),
                ("Tri tournee", 1, "Dispatch express"),
                ("Chargement quai", 1, "Chargement prioritaire"),
            ]
        return steps

    scenario_normal = _make_instance(
        name="scenario_normal",
        job_sequences=base_steps(include_flash=True),
        description="Scenario normal: flux logistique nominal avec commandes retail/e-commerce/C&C et une commande flash integree.",
    )

    scenario_maintenance = _make_instance(
        name="scenario_maintenance",
        job_sequences=base_steps(include_flash=True),
        maintenance=[
            MaintenanceWindow("Emballage", start=4, duration=3, label="Maintenance scelleuse"),
            MaintenanceWindow("Etiquetage", start=8, duration=2, label="Recharge consommables"),
            MaintenanceWindow("Chargement quai", start=12, duration=3, label="Occupation quai"),
        ],
        description="Scenario normal avec maintenance planifiee (emballage, etiquetage, quai).",
    )

    scenario_rush_150 = _make_instance(
        name="scenario_rush_150",
        job_sequences=_build_rush(150),
        description="Scenario rush 150 commandes (20 express, 30 click&collect, 100 livraisons magasins).",
    )

    scenario_rush_300 = _make_instance(
        name="scenario_rush_300",
        job_sequences=_build_rush(300),
        description="Scenario rush 300 commandes (20 express, 30 click&collect, 250 livraisons magasins).",
    )

    scenario_rush_450 = _make_instance(
        name="scenario_rush_450",
        job_sequences=_build_rush(450),
        description="Scenario rush 450 commandes (20 express, 30 click&collect, 400 livraisons magasins).",
    )

    return {
        scenario_normal.name: scenario_normal,
        scenario_maintenance.name: scenario_maintenance,
        scenario_rush_150.name: scenario_rush_150,
        scenario_rush_300.name: scenario_rush_300,
        scenario_rush_450.name: scenario_rush_450,
    }


def instance_horizon(instance: JobShopInstance) -> int:
    op_sum = sum(op.duration for job in instance.jobs for op in job.operations)
    maint_sum = sum(m.duration for m in instance.maintenance)
    maint_far_end = max((m.start + m.duration for m in instance.maintenance), default=0)
    return max(op_sum + maint_sum, maint_far_end)