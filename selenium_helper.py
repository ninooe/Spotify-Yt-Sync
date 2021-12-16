
import selenium
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
import logging

########### todo Proper Exceptionhandeling in case of connection lost connection ############

def wait_for_element(locator: str, query: str, driver: selenium.webdriver, timeout: int = 30) -> Optional[WebElement]:
    """Let selenium driver wait for element

    Args:
        locator (str): locator present in this set selenium.webdriver.common.by
        query (str): description of element matching locator
        driver (webdriver): instance of selenium.webdriver
        timeout (int, optional): time to wait before timeout. Defaults to 30.

    Returns:
        selenium.webdriver.remote.webelement.WebElement / None
    """
    try:
        parentElement = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((locator, query))
            )
        return parentElement
    except Exception:
        logging.debug(f"{Exception} occured while waiting for element")
        return None
