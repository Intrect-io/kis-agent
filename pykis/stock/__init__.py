from .api import StockAPI
from .condition import ConditionAPI

MarketAPI = StockAPI
StockMarketAPI = StockAPI

__all__ = ['StockAPI', 'ConditionAPI', 'MarketAPI', 'StockMarketAPI']
