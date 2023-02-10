from __future__ import annotations

from typing import Any
from typing_extensions import Protocol, TypedDict


class OnConflict(TypedDict, total=False):
    constraint: str | None
    index_elements: Any | None
    index_where: Any | None
    set_: set[str] | None
    where: Any | None


class PydanticP(Protocol):
    @classmethod
    def parse_obj(cls, obj):
        ...

    def dict(self, **kwargs) -> dict[str, Any]:
        ...
