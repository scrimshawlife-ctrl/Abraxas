from abraxas.modules.gtx.cli import register as register_gtx


def register(subparsers) -> None:
    register_gtx(subparsers)
