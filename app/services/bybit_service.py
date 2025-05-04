import aiohttp
import asyncio
from loguru import logger

class BybitService:
    BASE_URL = "https://api.bybit.com"
    
    @staticmethod
    async def is_token_valid(symbol: str) -> bool:
        """Check if the given token symbol exists on Bybit."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{BybitService.BASE_URL}/v5/market/tickers"
                params = {"category": "spot", "symbol": f"{symbol}USDT"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                        return True
                    return False
        except Exception as e:
            logger.error(f"Error checking token validity for {symbol}: {e}")
            return False
    
    @staticmethod
    async def get_token_price(symbol: str) -> float:
        """Get the current price of a token on Bybit."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{BybitService.BASE_URL}/v5/market/tickers"
                params = {"category": "spot", "symbol": f"{symbol}USDT"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                        price = float(data["result"]["list"][0]["lastPrice"])
                        return price
                    
                    return None
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    @staticmethod
    async def get_all_tokens() -> list:
        """Get a list of all available tokens on Bybit."""
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{BybitService.BASE_URL}/v5/market/tickers"
                params = {"category": "spot"}
                
                async with session.get(url, params=params) as response:
                    data = await response.json()
                    
                    tokens = []
                    if data.get("retCode") == 0 and data.get("result", {}).get("list"):
                        for item in data["result"]["list"]:
                            if item["symbol"].endswith("USDT"):
                                symbol = item["symbol"].replace("USDT", "")
                                tokens.append(symbol)
                    
                    return tokens
        except Exception as e:
            logger.error(f"Error getting all tokens: {e}")
            return [] 