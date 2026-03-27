import builtins
import gzip

from abraxas.storage.compress import decompress_bytes


def test_zstd_decompress_falls_back_to_gzip_frame(monkeypatch):
    original = b"deterministic-payload" * 4
    compressed = gzip.compress(original)

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "zstandard":
            raise ImportError("forced for test")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    recovered = decompress_bytes(compressed, "zstd")
    assert recovered == original
