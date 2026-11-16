import pytest
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


@pytest.fixture
def browser():
    options = Options()
    options.add_argument("--start-maximized")

    driver = webdriver.Chrome(options=options)

    yield driver

    driver.quit()


def test_homepage_loads(browser):
    browser.get("http://127.0.0.1:5000")

    assert browser.title != ""
    assert "Maison Fleur" in browser.find_element(
        "tag name", "body"
    ).text


def test_catalog_loads(browser):
    browser.get("http://127.0.0.1:5000/catalog")

    assert browser.current_url.endswith("/catalog")
    assert browser.find_element("tag name", "body").text.strip() != ""


def test_login_page_loads(browser):
    browser.get("http://127.0.0.1:5000/login")

    assert browser.current_url.endswith("/login")
    assert browser.find_element("name", "email").is_displayed()
    assert browser.find_element("name", "password").is_displayed()        