from prefect.run_configs import DockerRun
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions
import json
import time
# import pendulum
from prefect import task, Flow, Parameter
from prefect.storage import Module


@task()
def swa_checkin(confirmation_num, first_name, last_name):
    BASE_URL = "https://mobile.southwest.com"
    VIEW_RESERVATION_ENDPOINT = "/check-in"
    CHECKIN_ENDPOINT = "/api/mobile-air-operations/v1/mobile-air-operations/page/check-in"
    VIEW_RESERVATION_URL = BASE_URL + VIEW_RESERVATION_ENDPOINT
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:99.0) Gecko/20100101 Firefox/99.0"

    options = ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--user-agent=" + USER_AGENT)

    driver = Chrome(options=options)
    driver.get(VIEW_RESERVATION_URL)

    confirmation_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "recordLocator")))
    confirmation_element.send_keys(confirmation_num)  # A valid confirmation number isn't needed

    first_name_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "firstName")))
    first_name_element.send_keys(first_name)

    last_name_element = WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, "lastName")))
    last_name_element.send_keys(last_name)

    last_name_element.submit()

    for request in driver.requests:
        if CHECKIN_ENDPOINT in request.url:
            while not request.response:
                time.sleep(1)
            checkin_json = json.loads(request.response.body)['checkInViewReservationPage']['_links']['checkIn']
            checkin_header = str(request.response.headers)
            break
    url = f"/api/mobile-air-operations{checkin_json['href']}"
    js_script = f"""
    var callback = arguments[arguments.length - 1];
    fetch({url}, {{method: "POST", headers: {checkin_header}, body: {checkin_json['body']}}})
    .then(response => response.json())
    .then(data => callback(data['checkInConfirmationPage']));
    """
    checkin_result = driver.execute_async_script(js_script)

    driver.quit()
    return checkin_result


with Flow("swa-checkin", storage=Module("checkin")) as f:
    confirmation_num = Parameter("confirmation-num", required=True)
    first_name = Parameter("first-name", required=True)
    last_name = Parameter("last-name", required=True)
    checkin_result = swa_checkin(confirmation_num, first_name, last_name)


# Configure extra environment variables for this flow,
# and set a custom image
f.run_config = DockerRun(
    env={"SELENIUM_REMOTE_URL": "http://127.0.0.1:4444/wd/hub"},
    image="bfdnd/southwest-check-in:latest",
    host_config={
        'network_mode': 'host'
    }
)
