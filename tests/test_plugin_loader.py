from abx.plugins import load_plugins, PluginRegistration


class DummySubparsers:
    def __init__(self) -> None:
        self.seen: list[str] = []


def test_plugin_loader_orders_by_name() -> None:
    subparsers = DummySubparsers()

    def make_loader(name: str):
        def loader():
            def register(sub):
                sub.seen.append(name)

            return register

        return loader

    registrations = [
        PluginRegistration(name="zeta", loader=make_loader("zeta")),
        PluginRegistration(name="alpha", loader=make_loader("alpha")),
    ]
    load_plugins(subparsers, registrations=registrations)
    assert subparsers.seen == ["alpha", "zeta"]
