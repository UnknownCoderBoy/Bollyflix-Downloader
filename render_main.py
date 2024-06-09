from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import requests

options = Options()
options.add_argument("--headless")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")

driver = webdriver.Chrome(options=options)


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


class Links(BaseModel):
    MovieLink: str


class Keys(BaseModel):
    API: str
    Pass: str


app = FastAPI()


@app.post("/GetMovieStreamLink")
def get_movie_link(Model: Links):
    try:

        page_loading(driver, Model.MovieLink, By.ID, "lite-human-verif-button")
        driver.execute_script(
            "document.getElementById('lite-human-verif-button').click();"
        )

        print("Verified")

        original_window = driver.current_window_handle

        page_loading(driver, "", By.ID, "lite-start-sora-button")

        driver.execute_script(
            "document.getElementById('lite-end-sora-button').click();"
        )

        print("Download button Clicked")

        # GDFlix Page

        switch_to_new_window(driver, original_window)

        gdflix_url = driver.current_url

        print(f"GDFlix Url: {gdflix_url}")

        data = {"url": gdflix_url}

        # Return a JSONResponse with the Url
        return JSONResponse(content=jsonable_encoder(data), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/UpdateApiKey")
def update_api_key(Model: Keys):
    try:

        if Model.Pass != "Pass@123":
            data = {"message": "Incorrect password"}
            return JSONResponse(content=jsonable_encoder(data), status_code=401)

        jsonbin_url = "https://api.jsonbin.io/v3/b/66655a1de41b4d34e400ad84"
        jsonbin_headers = {
            "Content-Type": "application/json",
            "X-Master-Key": "$2a$10$Oge8KnqXh7O5yj25pv8dheB3OifTS1ZBdcXDzZdj3WsYvQqBKQEIq",
        }
        jsonbin_data = {"zenrows_api": Model.API}

        response = requests.put(jsonbin_url, json=jsonbin_data, headers=jsonbin_headers)

        print(response.json())

        data = {"message": "API key updated successfully"}

        return JSONResponse(content=jsonable_encoder(data), status_code=200)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
