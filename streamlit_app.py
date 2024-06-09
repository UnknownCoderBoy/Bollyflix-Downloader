import streamlit as st
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re

# Cloudflare Unblocking
from zenrows import ZenRowsClient


def scrape_articles(search_query):
    url = f"https://bollyflix.city/search/{search_query.replace(' ', '+')}"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    articles = soup.find_all("article")

    articles_list = [
        (
            article.find("a").get("title"),
            article.find("a").get("href"),
            article.find("img").get("src"),
        )
        for article in articles
    ]

    return articles_list


def article_quality(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    # Assuming you have already parsed the HTML content and have a BeautifulSoup object named soup
    div = soup.find("div", class_="thecontent clearfix")
    links_data = []

    if div:
        h5_tags = div.find_all("h5")

        for h5_tag in h5_tags:
            p_tag = h5_tag.find_next_sibling("p")

            if p_tag:
                links = p_tag.find_all("a", class_="dl")
                for link in links:
                    if "google drive".lower() in link.text.lower():
                        title = h5_tag.text
                        href = link.get("href")
                        links_data.append((title, href))

    return links_data


def get_drive_bot_urls(url):
    urls = []
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)

    # Extract 'id' and 'do' values
    id_value = query_params.get("id", [None])[0]
    do_value = query_params.get("do", [None])[0]

    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    soup = BeautifulSoup(response.content, "html.parser")
    buttons = soup.find_all("button", attrs={"onclick": True})

    if id_value and do_value:
        for btn in buttons:
            onclick_attr = btn.get("onclick")
            parts = onclick_attr.split(",")
            baseUrl = parts[0].split("'")[-2]
            print(f"Extracted URL: {baseUrl}")
            download_url = f"{baseUrl}?id={id_value}&do={do_value}"
            urls.append(download_url)
    else:
        print("ID or do parameter not found in the URL query.")

    return urls


def get_stream_url(url):
    session = requests.Session()
    response = session.get(url)
    response.raise_for_status()  # Check if the request was successful

    cookies = session.cookies.get_dict()
    soup = BeautifulSoup(response.content, "html.parser")
    script_tags = soup.find_all("script")

    token = None
    id = None
    for script_tag in script_tags:
        script_content = script_tag.string
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
    else:
        raise ValueError("Token or ID not found in the script tags.")

    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}"
    data = {"token": token}
    response = requests.post(f"{base_url}?id={id}", data=data, cookies=cookies)
    response.raise_for_status()
    return response.json()


def get_zenrows_key():
    jsonbin_url = "https://api.jsonbin.io/v3/b/66655a1de41b4d34e400ad84"
    jsonbin_headers = {
        "X-Master-Key": "$2a$10$Oge8KnqXh7O5yj25pv8dheB3OifTS1ZBdcXDzZdj3WsYvQqBKQEIq"
    }

    req = requests.get(jsonbin_url, json=None, headers=jsonbin_headers)
    data = req.json()
    return data["record"]["zenrows_api"]


def get_stream_link(url):
    st.session_state.show_download = False
    st.session_state.show_stream = True
    st.session_state.url = url


def get_quality(url, title):
    st.session_state.show_articles = False
    st.session_state.show_download = True
    st.session_state.title = title
    st.session_state.url = url


st.set_page_config(page_title="BollyFlix Downloader", page_icon=":movie_camera:")


st.markdown(
    """<style>
    .language-url {
        color: #4997ed;
    },
</style>""",
    unsafe_allow_html=True,
)


# Initialize session state
if "show_articles" not in st.session_state:
    st.session_state.show_articles = True

if "show_download" not in st.session_state:
    st.session_state.show_download = False

if "show_stream" not in st.session_state:
    st.session_state.show_stream = False

if "title" not in st.session_state:
    st.session_state.title = ""

if "url" not in st.session_state:
    st.session_state.url = ""

# Main app
if st.session_state.show_articles:

    search_query = st.text_input("Search Movie")

    if search_query:
        articles_list = scrape_articles(search_query)

        if articles_list:
            col1, col2, col3 = st.columns(3)
            columns = [col1, col2, col3]

            for idx, (title, link, img) in enumerate(articles_list):
                with columns[idx % 3]:
                    st.image(img, width=200)
                    st.write(title)
                    st.button(
                        "Download", key=idx, on_click=get_quality, args=(link, title)
                    )
        else:
            st.write("No articles found.")

if st.session_state.show_download:
    st.write(st.session_state.title)
    quality = article_quality(st.session_state.url)

    for idx, (title, url) in enumerate(quality):
        st.button(title, key=idx, on_click=get_stream_link, args=(url,))

if st.session_state.show_stream:
    st.write(st.session_state.title)
    try:
        gdflix_url = None

        with st.spinner("Generating GDFlix Link ..."):
            url = "https://bollyflix-downloader.onrender.com/GetMovieStreamLink"
            data = {
                "MovieLink": st.session_state.url,
            }
            response = requests.post(url, json=data, stream=True)

            if response.ok:
                # Iterate over the response content in chunks
                response_json = response.json()
                gdflix_url = response_json["url"]
                st.write(f"GDFlix Url: {gdflix_url}")

            else:
                st.toast(f"Error: {response.status_code} - {response.reason}")

        drive_bot_link = None

        with st.spinner("Generating Drive Bot Link..."):

            zenrows_api = get_zenrows_key()

            client = ZenRowsClient(zenrows_api)
            params = {"js_render": "true"}
            response = client.get(gdflix_url, params=params)

            if not response.ok:
                raise Exception(f"Zenrows Api Key")

            soup = BeautifulSoup(response.content, "html.parser")

            for link in soup.find_all("a"):
                if "drivebot" in link.get("href"):
                    drive_bot_link = link.get("href")
                    break

        if drive_bot_link:
            with st.spinner("Generating Stream URL..."):
                url_list = get_drive_bot_urls(drive_bot_link)

                if url_list:
                    for url in url_list:
                        try:
                            stream_url = get_stream_url(url)
                            if stream_url:
                                st.markdown("Stream URL")
                                st.code(stream_url["url"], language="url")
                                st.balloons()
                                break
                        except Exception as e:
                            st.toast(f"Error with URL {url}: {str(e)}")
                            continue
                else:
                    st.toast("No URLs found")
        else:
            st.toast("No Drive Bot URL found")

    except Exception as e:
        st.toast(f"Error: {str(e)}")
