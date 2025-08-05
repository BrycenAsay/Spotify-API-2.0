import requests
from bs4 import BeautifulSoup
from selenium import webdriver
import base64
from PIL import Image
import io

def return_rand_img():
    def get_image_srcs(_response):
        # Parse the HTML content with Beautiful Soup
        soup = BeautifulSoup(_response, 'html.parser')
        
        # Find all <img> tags
        img_tags = soup.find_all('img')
        
        # Extract the 'src' attribute from each <img> tag
        srcs = [img['src'] for img in img_tags if 'src' in img.attrs]
        
        return srcs

    def url_to_base64(image_url):
        # Fetch the image from the URL
        response = requests.get(image_url)
        
        if response.status_code == 200:
            # Open the image from the response content
            img = Image.open(io.BytesIO(response.content))
            
            # Create a BytesIO object to hold the image data
            buffered = io.BytesIO()
            # Save the image to the BytesIO object as JPEG
            img.save(buffered, format="JPEG")
            # Get the byte data from the BytesIO object
            img_bytes = buffered.getvalue()
            # Encode the byte data to base64
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')
            return img_base64
        else:
            raise Exception(f"Failed to fetch image from {image_url}: Status code {response.status_code}")

    # Set up the WebDriver (make sure to have the appropriate driver for your browser)
    driver = webdriver.Chrome()  # or webdriver.Firefox()

    url = 'https://picsum.photos/400'

    driver.get(url)
    html = driver.page_source

    return url_to_base64(get_image_srcs(html)[0])