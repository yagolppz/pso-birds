"""Estado compartido de la bandada y registro del vuelo."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .particle import Vector


@dataclass(slots=True)
class FlightSnapshot:
    """Foto de un vuelo para estudiar como mejora la bandada."""

    flight_number: int
    treasure_position: Vector
    treasure_crumbs: float
    average_crumbs: float
    evaluation_seconds: float
    update_seconds: float
    overhead_seconds: float
    particle_positions: list[Vector] | None = None


@dataclass(slots=True)
class SwarmHistory:
    """Cuaderno de viaje de la bandada."""

    snapshots: list[FlightSnapshot] = field(default_factory=list)

    def remember(
        self,
        flight_number: int,
        treasure_position: Vector,
        treasure_crumbs: float,
        average_crumbs: float,
        evaluation_seconds: float,
        update_seconds: float,
        overhead_seconds: float,
        particle_positions: list[Vector] | None = None,
    ) -> None:
        self.snapshots.append(
            FlightSnapshot(
                flight_number=flight_number,
                treasure_position=list(treasure_position),
                treasure_crumbs=treasure_crumbs,
                average_crumbs=average_crumbs,
                evaluation_seconds=evaluation_seconds,
                update_seconds=update_seconds,
                overhead_seconds=overhead_seconds,
                particle_positions=(
                    [list(position) for position in particle_positions]
                    if particle_positions is not None
                    else None
                ),
            )
        )

    def as_records(self, include_particle_positions: bool = False) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        for snapshot in self.snapshots:
            record = asdict(snapshot)
            if not include_particle_positions:
                record.pop("particle_positions", None)
            records.append(record)
        return records


@dataclass(slots=True)
class FlockTreasure:
    """Mejor sitio del grupo, es decir, donde hay mas migas."""

    position: Vector
    crumbs: float
