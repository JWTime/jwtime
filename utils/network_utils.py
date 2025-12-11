# file: utils/network_utils.py

import aiohttp
import asyncio
import logging

async def check_internet_connection():
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("https://www.google.com", timeout=5) as response:
                return response.status == 200
    except Exception:
        return False

async def fetch_url(url, max_retries=3, timeout=10):
    """
    Scarica il contenuto di un URL con retry automatico in caso di errori di rete.
    
    Args:
        url: URL da scaricare
        max_retries: Numero massimo di tentativi (default: 3)
        timeout: Timeout in secondi per ogni richiesta (default: 10)
    
    Returns:
        str: Contenuto HTML se successo, None se fallimento dopo tutti i tentativi
    """
    backoff_delays = [0.5, 1.0, 2.0]  # Ritardi esponenziali tra i tentativi
    
    for attempt in range(max_retries):
        try:
            timeout_config = aiohttp.ClientTimeout(total=timeout)
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    content = await response.text()
                    
                    return content
                    
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            # Errori di rete/timeout: ritenta
            is_last_attempt = (attempt == max_retries - 1)
            
            if is_last_attempt:
                # Ultimo tentativo fallito
                logging.warning(f"[fetch_url] Fallito dopo {max_retries} tentativi per {url}: {type(e).__name__}: {str(e)}")
                return None
            else:
                # Ritenta dopo backoff
                delay = backoff_delays[min(attempt, len(backoff_delays) - 1)]
                await asyncio.sleep(delay)
                
        except Exception as e:
            # Altri errori: fallimento immediato (es. ValueError, KeyError, etc.)
            logging.error(f"[fetch_url] Errore non recuperabile per {url}: {type(e).__name__}: {str(e)}")
            return None
    
    return None