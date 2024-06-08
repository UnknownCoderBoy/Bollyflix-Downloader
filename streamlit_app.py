import streamlit as st
import requests
from bs4 import BeautifulSoup


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


def get_stream_link(url):
    st.session_state.show_download = False
    st.session_state.show_stream = True
    st.session_state.url = url


def get_quality(url, title):
    st.session_state.show_articles = False
    st.session_state.show_download = True
    st.session_state.title = title
    st.session_state.url = url


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
    with st.status("Working ...", expanded=True) as status:
        url = "http://127.0.0.1:8000/GetMovieStreamLink"
        data = {
            "MovieLink": st.session_state.url,
        }
        response = requests.post(url, json=data, stream=True)
        if response.ok:
            # Iterate over the response content in chunks
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    # Process each chunk of data
                    st.write(chunk.decode("utf-8"))  # Decode the chunk if it's in bytes

            status.update(label="Download complete!", state="complete")
        else:
            # Handle errors
            print(f"Error: {response.status_code} - {response.reason}")
