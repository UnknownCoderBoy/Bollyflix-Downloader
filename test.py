import re
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse, parse_qs

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()), options=options
)


def page_loading(driver, url="", by=By.ID, value=""):
    page_wait = WebDriverWait(driver, 10)  # Wait for up to 10 seconds
    if url != "":
        driver.get(url)
    if value != "":
        page_wait.until(EC.presence_of_all_elements_located((by, value)))
    print(f"{driver.title} Page Loaded")


def switch_to_new_window(driver, original_window):
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            new_window = window_handle
        else:
            driver.close()

    driver.switch_to.window(new_window)


def close_new_tab(driver, original_window):
    for window_handle in driver.window_handles:
        if window_handle != original_window:
            driver.switch_to.window(window_handle)
            driver.close()

    driver.switch_to.window(original_window)


def get_urls(url, buttons=[]):
    urls = []
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Extract 'id' and 'do' values
    id_value = query_params.get("id", [None])[0]
    do_value = query_params.get("do", [None])[0]

    if id_value and do_value:
        for btn in buttons:
            onclick_attr = btn.get_attribute("onclick")
            parts = onclick_attr.split(",")
            baseUrl = parts[0].split("'")[-2]
            print(f"Extracted URL: {baseUrl}")
            download_url = f"{baseUrl}?id={id_value}&do={do_value}"
            urls.append(download_url)
    else:
        print("ID or do parameter not found in the URL query.")

    return urls


def drive_bot_server(driver, url):

    page_loading(driver, url, By.CLASS_NAME, "card-body")

    script_tags = driver.find_elements(By.TAG_NAME, "script")

    token = None
    id = None
    for script_tag in script_tags:
        script_content = script_tag.get_attribute("innerHTML")
        if script_content:
            token_match = re.search(r"append\('token', '([^']*)'", script_content)
            id_match = re.search(r"id=([^&']*)", script_content)
            if token_match and id_match:
                token = token_match.group(1)
                id = id_match.group(1)
                break

    if token and id:
        print("Token:", token)
        print("ID:", id)

    js_code = """
    var formData = new FormData();
    var url = "";
    formData.append('token', '{token}');
    var urlData = fetch('/download?id={id}', { method: 'POST', body: formData })
        .then(response => response.json()).then(data => {
          if (data.url) { url = data.url; return url;}});
    var data = urlData.then((data) => {
        return data;
      });
    return data;
    """

    js_code = js_code.replace("{token}", token).replace("{id}", id)

    stream_link = driver.execute_script(js_code)

    return stream_link


page_loading(driver, "https://bollyflix.city/search/hot+blooded+2022")

articles = driver.find_elements(By.TAG_NAME, "article")
articles_list = [
    (
        article.find_element(By.TAG_NAME, "a").get_attribute("title"),
        article.find_element(By.TAG_NAME, "a").get_attribute("href"),
    )
    for article in articles
]

# Print the dictionary to verify
for title, _ in articles_list:
    print(f"Title: {title}")


page_loading(driver, articles_list[0][1])

div = driver.find_element(By.CLASS_NAME, "thecontent.clearfix")
links_data = []

if div:
    h5_tags = div.find_elements(By.TAG_NAME, "h5")

    for h5_tag in h5_tags:
        p_tag = h5_tag.find_element(By.XPATH, "./following-sibling::p[1]")

        if p_tag:
            links = p_tag.find_elements(By.CLASS_NAME, "dl")
            for link in links:
                if "google drive".lower() in link.text.lower():
                    href = link.get_attribute("href")
                    title = h5_tag.text
                    links_data.append((title, href))

for title, _ in links_data:
    print(title)


page_loading(driver, links_data[0][1], By.ID, "lite-human-verif-button")
driver.execute_script("document.getElementById('lite-human-verif-button').click();")

print("Verified")

original_window = driver.current_window_handle

page_loading(driver, "", By.ID, "lite-start-sora-button")

driver.execute_script("document.getElementById('lite-end-sora-button').click();")
print("Download button Clicked")

# GDFlix Page

switch_to_new_window(driver, original_window)

page_loading(driver, "", By.CLASS_NAME, "card-body")

download_links = driver.find_elements(By.TAG_NAME, "a")

for link in download_links:
    if "drivebot" in link.get_attribute("href"):
        drive_bot_link = link.get_attribute("href")
        break

# DriveBot Page

page_loading(driver, drive_bot_link, By.XPATH, "//button[@onclick]")

parse_url = driver.current_url

download_btns = driver.find_elements(By.XPATH, "//button[@onclick]")

url_list = get_urls(parse_url, download_btns)

stream_url = drive_bot_server(driver, url_list[0])

print(stream_url)

driver.quit()
