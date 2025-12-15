# tests/test_phonetics.py
from abraxas.linguistic.phonetics import soundex, phonetic_key

def test_soundex_stability():
    assert soundex("Robert") == soundex("Rupert")
    assert soundex("Ashcraft") == soundex("Ashcroft")

def test_phonetic_key_phrase():
    assert phonetic_key("Aphex Twin")
    assert phonetic_key("Apex Twin")
