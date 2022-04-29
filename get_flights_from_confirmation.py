from prefect.run_configs import DockerRun
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire.undetected_chromedriver import Chrome, ChromeOptions
import json
# import pendulum
from prefect import task, Flow, Parameter, Client
from prefect.storage import Module


@task(nout=1)
def get_flights_from_confirmation(confirmation_num, first_name, last_name):
    BASE_URL = "https://mobile.southwest.com"
    VIEW_RESERVATION_ENDPOINT = "/view-reservation"
    VIEW_RESERVATION_API_ENDPOINT = "/api/mobile-air-booking/v1/mobile-air-booking/page/view-reservation"
    VIEW_RESERVATION_URL = BASE_URL + VIEW_RESERVATION_ENDPOINT
    USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:96.0) Gecko/20100101 Firefox/99.0"

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

    WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.CLASS_NAME, "flight-time")))
    for request in driver.requests:
        if VIEW_RESERVATION_API_ENDPOINT in request.url:
            checkin_utc = json.loads(request.response.body)['viewReservationViewPage']['checkinCountdownTimeStamp']
            break
    # dt = pendulum.parse(checkin_utc)
    # checkdt.subtract(days=1)
    driver.quit()
    return checkin_utc


with Flow("get-flights-from-confirmation", storage=Module(__name__)) as f:
    confirmation_num = Parameter("confirmation-num", required=True)
    first_name = Parameter("first-name", required=True)
    last_name = Parameter("last-name", required=True)
    checkin_utc = get_flights_from_confirmation(confirmation_num, first_name, last_name)

    prefect_client = Client()
    prefect_client.create_flow_run(flow_id="4c584e7d-6d0d-445e-ac8e-ac1735959a92", parameters={'confirmation-num': confirmation_num,
                                                                        'first-name': first_name,
                                                                        'last-name': last_name}
                                   , scheduled_start_time=checkin_utc)
# Configure extra environment variables for this flow,
# and set a custom image
f.run_config = DockerRun(
    env={"SELENIUM_REMOTE_URL": "http://127.0.0.1:4444/wd/hub"},
    image="bfdnd/southwest-check-in:latest"
)
