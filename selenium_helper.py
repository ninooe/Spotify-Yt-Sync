import logging
from typing import Optional, Type

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

########### TODO Proper Exceptionhandeling in case of connection lost ############

def wait_for_element(locator: str, query: str, driver: Type[WebDriver], timeout: int = 30) -> Optional[WebElement]:
    """Let selenium driver wait for element

    Args:
        locator (str): locator present in this set selenium.webdriver.common.by
        query (str): description of element matching locator
        driver (webdriver): instance of class inheriting from selenium.webdriver.remote.webdriber.WebDriver
        timeout (int, optional): time to wait before timeout. Defaults to 30.

    Returns:
        selenium.webdriver.remote.webelement.WebElement / None
    """
    try:
        parentElement = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((locator, query))
            )
        return parentElement
    except Exception as err:
        logging.debug(f"{err} occured while waiting for element")
        return None
