"""Shadow Structural Metrics (SSM) - Cambridge Analytica Derived Metrics.

CRITICAL: This module can ONLY be accessed via ABX-Runes interface (ϟ₇).
Direct access is forbidden by design to enforce no-influence guarantees.

Version: 1.0.0
SEED Framework Compliant
LOCKED: 2025-12-29
"""

__version__ = "1.0.0"


class AccessDeniedError(Exception):
    """Raised when attempting direct access to Shadow Structural Metrics.

    Shadow Structural Metrics are observe-only metrics that must maintain
    strict isolation from the rest of the system. All access MUST go through
    the ABX-Runes interface (ϟ₇) to ensure:

    1. No-influence guarantee (SSM never affects other metrics)
    2. SEED provenance tracking
    3. Audit logging
    4. Isolation proof generation
    """

    pass


def __getattr__(name: str):
    """Block all direct attribute access to enforce ABX-Runes-only coupling.

    This prevents any direct imports or function calls to Shadow Structural
    Metrics. All access must go through the ϟ₇ rune operator.

    Args:
        name: Attribute name being accessed

    Raises:
        AccessDeniedError: Always raised for compute functions
        AttributeError: For unknown attributes

    Examples:
        >>> from abraxas.shadow_metrics import compute_sei
        AccessDeniedError: Shadow Structural Metrics can only be accessed via ABX-Runes...

        >>> from abraxas.shadow_metrics.core import SSMEngine
        AccessDeniedError: Shadow Structural Metrics can only be accessed via ABX-Runes...
    """
    # Allow version access
    if name == "__version__":
        return __version__

    # Block compute functions
    if name.startswith("compute_") or name in ["SEI", "CLIP", "NOR", "PTS", "SCG", "FVC"]:
        raise AccessDeniedError(
            "Shadow Structural Metrics can only be accessed via ABX-Runes interface (ϟ₇). "
            "Direct access is forbidden by design to maintain no-influence guarantees. "
            "See docs/specs/shadow_structural_metrics.md for details."
        )

    # Block internal modules (but allow them to be imported internally)
    if name in ["core", "sei", "clip", "nor", "pts", "scg", "fvc", "isolation", "provenance"]:
        raise AccessDeniedError(
            f"Direct access to '{name}' module is forbidden. "
            "Shadow Structural Metrics can only be accessed via ABX-Runes interface (ϟ₇). "
            "See docs/specs/shadow_structural_metrics.md for details."
        )

    # Unknown attribute
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Internal access point for ABX-Runes ONLY
# This is the ONLY way to access SSM functionality
def _internal_rune_access():
    """Internal access point for ABX-Runes ϟ₇ operator ONLY.

    DO NOT call this function directly. It is only meant to be called by
    the ϟ₇ rune operator with proper isolation and audit logging.

    Returns:
        SSMEngine: The Shadow Structural Metrics computation engine

    Raises:
        RuntimeError: If called without proper rune context
    """
    import inspect

    # Verify this is being called from rune operator
    frame = inspect.currentframe()
    if frame and frame.f_back:
        caller_file = frame.f_back.f_code.co_filename
        if "runes/operators/sso.py" not in caller_file:
            raise RuntimeError(
                "Shadow Structural Metrics internal access can ONLY be called "
                "from ABX-Runes ϟ₇ (SSO) operator. "
                f"Unauthorized caller: {caller_file}"
            )

    # Import and return engine (deferred import to prevent direct access)
    from abraxas.shadow_metrics.core import SSMEngine

    return SSMEngine()
