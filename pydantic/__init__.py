from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Dict, Iterable, List, get_args, get_origin, get_type_hints


class _Missing:
    pass


_MISSING = _Missing()


class ValidationError(Exception):
    """Minimal ValidationError shim for local BaseModel usage."""


class FieldInfo:
    def __init__(self, default: Any = _MISSING, default_factory: Callable[[], Any] | None = None, **metadata: Any):
        if default is not _MISSING and default_factory is not None:
            raise ValueError("Specify either default or default_factory, not both.")
        self.default = default
        self.default_factory = default_factory
        self.metadata = metadata


def Field(default: Any = _MISSING, *, default_factory: Callable[[], Any] | None = None, **metadata: Any) -> FieldInfo:
    """
    Lightweight stand-in for pydantic.Field.

    Only captures defaults and metadata required by the local BaseModel shim.
    """
    if default is Ellipsis:
        default = _MISSING
    return FieldInfo(default=default, default_factory=default_factory, **metadata)


class BaseModel:
    """
    Minimal stub of pydantic.BaseModel suitable for deterministic tests in this repository.
    """

    def __init__(self, **data: Any):
        annotations: Dict[str, Any] = get_type_hints(self.__class__)
        for name, _ in annotations.items():
            if name in data:
                value = data[name]
            else:
                attr = getattr(self.__class__, name, _MISSING)
                if isinstance(attr, FieldInfo):
                    if attr.default is not _MISSING:
                        value = attr.default
                    elif attr.default_factory is not None:
                        value = attr.default_factory()
                    else:
                        raise TypeError(f"Missing required field: {name}")
                elif attr is not _MISSING:
                    value = attr
                else:
                    raise TypeError(f"Missing required field: {name}")
            field_info = getattr(self.__class__, name, None)
            value = self._coerce_value(value, annotations.get(name), field_info)
            if isinstance(field_info, FieldInfo):
                self._validate_constraints(name, value, field_info)
            setattr(self, name, value)

        # Capture extra fields not declared in annotations
        for key, value in data.items():
            if key not in annotations:
                setattr(self, key, value)

    def model_dump(self) -> Dict[str, Any]:
        return {k: self._dump_value(v) for k, v in self._iter_model_fields()}

    def _iter_model_fields(self) -> Iterable[tuple[str, Any]]:
        annotations: Dict[str, Any] = getattr(self, "__annotations__", {})
        for name in annotations:
            if hasattr(self, name):
                yield name, getattr(self, name)
        for key, value in self.__dict__.items():
            if key not in annotations:
                yield key, value

    def _dump_value(self, value: Any) -> Any:
        if isinstance(value, BaseModel):
            return value.model_dump()
        if isinstance(value, list):
            return [self._dump_value(v) for v in value]
        if isinstance(value, dict):
            return {k: self._dump_value(v) for k, v in value.items()}
        return value

    def _coerce_value(self, value: Any, annotation: Any, field_info: Any) -> Any:
        origin = get_origin(annotation)
        args = get_args(annotation)
        if value is None:
            return None
        if annotation is datetime and isinstance(value, str):
            cleaned = value.replace("Z", "+00:00") if value.endswith("Z") else value
            try:
                return datetime.fromisoformat(cleaned)
            except Exception:
                try:
                    return datetime.fromisoformat(cleaned.replace(" ", "T"))
                except Exception:
                    return value
        if origin is list and isinstance(value, list):
            inner = args[0] if args else Any
            return [self._coerce_value(v, inner, None) for v in value]
        if origin is dict and isinstance(value, dict):
            val_type = args[1] if len(args) > 1 else Any
            return {k: self._coerce_value(v, val_type, None) for k, v in value.items()}
        if origin is tuple and isinstance(value, tuple):
            coerced: List[Any] = []
            inner_types = list(args) if args else [Any] * len(value)
            for idx, item in enumerate(value):
                inner = inner_types[min(idx, len(inner_types) - 1)] if inner_types else Any
                coerced.append(self._coerce_value(item, inner, None))
            return tuple(coerced)
        if origin is None and isinstance(value, dict) and isinstance(annotation, type) and issubclass(annotation, BaseModel):
            return annotation(**value)
        if origin is None and annotation is not None:
            try:
                if isinstance(annotation, type) and issubclass(annotation, BaseModel) and isinstance(value, BaseModel):
                    return value
            except Exception:
                pass
        if origin is Any:
            return value
        if origin is type(None):
            return None
        if origin is not None and annotation is not None:
            # Optional or Union types
            for ann in args:
                coerced = self._coerce_value(value, ann, None)
                if coerced is not None:
                    return coerced
        return value

    def _validate_constraints(self, name: str, value: Any, field_info: FieldInfo) -> None:
        ge = field_info.metadata.get("ge")
        le = field_info.metadata.get("le")
        if isinstance(value, (int, float)):
            if ge is not None and value < ge:
                raise ValueError(f"Field '{name}' must be >= {ge}")
            if le is not None and value > le:
                raise ValueError(f"Field '{name}' must be <= {le}")


class ValidationError(Exception):
    """
    Lightweight stand-in for pydantic.ValidationError.

    This repository uses a local pydantic shim for deterministic tests and to
    avoid a hard dependency in some environments.
    """


__all__ = ["BaseModel", "Field", "FieldInfo", "ValidationError"]
