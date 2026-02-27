import requests
import re

url = "https://github.com/trending/python"
response = requests.get(url)

repositories = re.findall(r'<article class="Box-row".*?>.*?<\/article>', response.text, re.DOTALL)

for repository in repositories[:5]:
    name_match = re.search(r'<h1>.*?<\/h1>', repository)
    if name_match:
        name = re.sub(r'<.*?>', '', name_match.group(0)).strip()
    else:
        name = "Not found"

    stars_match = re.search(r'<a class="d-inline-block".*?>.*?<\/a>', repository)
    if stars_match:
        stars = re.sub(r'<.*?>', '', stars_match.group(0)).strip()
    else:
        stars = "Not found"

    url_match = re.search(r'<h1>.*?<a href="(.*?)".*?>', repository)
    if url_match:
        url = 'https://github.com' + url_match.group(1)
    else:
        url = "Not found"

    print(f"Name: {name}, Stars: {stars}, URL: {url}")

# Execution output:
# Name: Not found, Stars: , URL: Not found
# Name: Not found, Stars: , URL: Not found
# Name: Not found, Stars: , URL: Not found
# Name: Not found, Stars: , URL: Not found
# Name: Not found, Stars: , URL: Not found