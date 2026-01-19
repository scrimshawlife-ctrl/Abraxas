"""Neon-Genie integration example.

Demonstrates invoking the Neon-Genie adapter through the ABX-Runes interface
and handling the external overlay being unavailable.
"""

from __future__ import annotations

from abraxas.aal.neon_genie_adapter import generate_symbolic_v0


def main() -> None:
    result = generate_symbolic_v0(
        prompt="Generate a symbolic representation of convergence",
        context={"term": "convergence", "motif": "lattice", "mode": "symbolic"},
        config={"max_length": 512},
        seed=17,
    )

    if result["not_computable"] is not None:
        print(f"Neon-Genie unavailable: {result['not_computable']['reason']}")
        return

    print("Generated output:")
    print(result["generated_output"])
    print("Provenance:")
    print(result["provenance"])


if __name__ == "__main__":
    main()
