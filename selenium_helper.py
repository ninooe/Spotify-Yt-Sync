import logging
from typing import Callable, Optional, Type

from abc import ABC, abstractmethod

from selenium.webdriver.remote.webdriver import BaseWebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from selenium.common.exceptions import TimeoutException, WebDriverException

########### TODO Proper Exceptionhandeling in case of connection lost ############

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


# def error_reload_webdriver(driver: BaseWebDriver, driver_generator: Callable[[], BaseWebDriver]):
#     '''reloads the webdriver in case of error\n
#     decorator only to be used on methods of Selenium_helper class'''
#     def decorator(func):
#         def wrapper(*args, **kwargs):
#             for _ in range(args[0]):
#                 try:
#                     return func(*args, **kwargs)
#                 except TimeoutException as err:
#                     logging.error(f'reloading driver {err=}')
#                     driver = driver_generator
#         return wrapper
#     return decorator



class Selenium_helper(ABC):
    
    def __init__(self) -> None:
        self.driver = self.get_webdriver()


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
                logging.error(f'reloading driver {err=}')
                args[0].driver = args[0].get_webdriver()
                return func(*args, **kwargs)
        return wrapper
    