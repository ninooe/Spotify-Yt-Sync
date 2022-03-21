import logging
from typing import Callable, Optional, Type

from abc import ABC, abstractmethod

from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import TimeoutException, WebDriverException


def wait_for_element(locator: str, query: str, driver: Type[BaseWebDriver], timeout: int = 30) -> Optional[WebElement]:
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


class Selenium_helper(ABC):


    def __init__(self) -> None:
        self.driver = self.get_webdriver()
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def get_webdriver(self) -> BaseWebDriver:
        '''returns configured WebDriver object'''
        pass


    def error_reload_webdriver(func):
        '''decorate function to reload webdriver and try again in case of selenium exception'''
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except (TimeoutException, WebDriverException) as err:
                args[0].logger.error(f'reloading driver {err=}')
                args[0].driver = args[0].get_webdriver()
                return func(*args, **kwargs)
        return wrapper
    