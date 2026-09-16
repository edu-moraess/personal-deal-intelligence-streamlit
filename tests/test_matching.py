from src.domain.matching import match_offer, is_compatible
from src.domain.models import MatchLevel
from src.domain.parser import parse_natural_query

def test_storage_must_match():
    q=parse_natural_query("Samsung Galaxy S25 256GB")
    assert is_compatible(match_offer("Samsung Galaxy S25 256GB 5G", q))
    assert match_offer("Samsung Galaxy S25 128GB 5G", q) == MatchLevel.INVALID_MATCH

def test_s25_ultra_rejected_for_base_model():
    q=parse_natural_query("Samsung Galaxy S25 256GB")
    assert match_offer("Samsung Galaxy S25 Ultra 256GB", q) == MatchLevel.INVALID_MATCH

def test_gpu_ti_rejected():
    q=parse_natural_query("RTX 5070")
    assert is_compatible(match_offer("Placa de Vídeo RTX 5070 12GB", q))
    assert match_offer("Placa de Vídeo RTX 5070 Ti 16GB", q) == MatchLevel.INVALID_MATCH

def test_monitor_size_must_match():
    q=parse_natural_query('monitor 27 polegadas 165hz')
    assert is_compatible(match_offer('Monitor Gamer 27" 165Hz IPS', q))
    assert match_offer('Monitor Gamer 24" 165Hz IPS', q) == MatchLevel.INVALID_MATCH
