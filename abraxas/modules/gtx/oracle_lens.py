from typing import Dict, List


def derive_game_theory_lens(signal_packet: Dict) -> Dict:
    motifs: List[str] = []
    signals = " ".join(str(value) for value in signal_packet.values()).lower()

    if "coordination" in signals:
        motifs.append("coordination")
    if "defect" in signals or "betray" in signals:
        motifs.append("defection_spiral")
    if "signal" in signals or "screen" in signals:
        motifs.append("signaling")
    if "commit" in signals or "credible" in signals:
        motifs.append("commitment_device")

    if not motifs:
        return {"status": "not_computable", "reason": "no game-theory motifs detected"}

    return {
        "status": "ok",
        "motifs": sorted(set(motifs)),
        "summary": "game-theory lens derived from signal packet",
    }
