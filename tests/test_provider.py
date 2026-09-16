from unittest.mock import MagicMock, patch
from src.domain.models import ProviderStatus
from src.domain.parser import parse_natural_query
from src.providers.mercadolivre import MercadoLivreProvider

def test_403_is_explicitly_unavailable():
    response=MagicMock(status_code=403, ok=False)
    with patch("src.providers.mercadolivre.requests.get", return_value=response):
        result=MercadoLivreProvider().search(parse_natural_query("Samsung Galaxy S25 256GB"))
    assert result.status == ProviderStatus.UNAVAILABLE
    assert result.offers == []

def test_success_maps_real_offer():
    response=MagicMock(status_code=200, ok=True)
    response.json.return_value={"results":[{"id":"MLB123","title":"Samsung Galaxy S25 256GB 5G Preto","price":3799.0,"permalink":"https://produto.mercadolivre.com.br/MLB-123","thumbnail":"https://http2.mlstatic.com/D_123-I.jpg","condition":"new","shipping":{"free_shipping":True}}]}
    with patch("src.providers.mercadolivre.requests.get", return_value=response):
        result=MercadoLivreProvider().search(parse_natural_query("Samsung Galaxy S25 256GB até 4000"))
    assert result.status == ProviderStatus.AVAILABLE
    assert len(result.offers) == 1
    assert result.offers[0].store == "Mercado Livre"
    assert result.offers[0].price == 3799.0
    assert result.offers[0].image_url is not None
