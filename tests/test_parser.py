from src.domain.parser import parse_natural_query

def test_galaxy_s25_256gb():
    q=parse_natural_query("Samsung Galaxy S25 256GB até R$ 4.000")
    assert q.brand == "Samsung"
    assert q.storage == "256GB"
    assert q.max_price == 4000.0

def test_monitor_quote_size():
    q=parse_natural_query('monitor 27" 165Hz até 1500')
    assert q.size == "27"
    assert q.refresh_rate == "165"

def test_gpu_vram_not_storage():
    q=parse_natural_query("RTX 5070 12GB até 4000")
    assert q.gpu_model == "RTX 5070"
    assert q.storage is None

def test_notebook_storage_over_ram():
    q=parse_natural_query("Notebook Lenovo ThinkPad E14 16GB 512GB")
    assert q.storage == "512GB"
