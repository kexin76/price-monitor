import requests
from bs4 import BeautifulSoup
import time
from selenium import webdriver
import os
from dotenv import load_dotenv

load_dotenv()
agolia_api_key = os.getenv("NT_API_KEY")
# This is for gundam planet, only filters through what is currently in stock
# Must loop through each page to get all products
gundamplanet_url = "https://www.gundamplanet.com/collections/gunpla/products.json?limit=250&filter.v.availability=1&page=1"

# This is for newtype (wesbite name), the backend api they're using to display their products
newtype_url = "https://U053ZPOKRJ-dsn.algolia.net/1/indexes/*/queries"
USAgundam_url = ""

newtype_headers = {
    "x-algolia-api-key": agolia_api_key,
    "x-algolia-application-id": "U053ZPOKRJ",
    "Content-Type": "application/json"
}
newtype_payload = {
    "requests":[
        {
            "indexName":"newtype",
            "params":"maxValuesPerFacet=50&query=&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&page=0&hitsPerPage=20&filters=published%3Atrue%20AND%20NOT%20tags%3Ahidden%20AND%20NOT%20vip%3Atrue%20AND%20type%3A%22Model%20Kit%22%20AND%20line%3Ahg&facets=%5B%22available%22%2C%22paintThinned%22%2C%22paintNonToxic%22%2C%22category%22%2C%22subCategory%22%2C%22vendor%22%2C%22brand%22%2C%22series%22%2C%22scale%22%2C%22paintLine%22%2C%22paintType%22%2C%22paintContainer%22%2C%22paintFinish%22%2C%22paintSolvent%22%5D&tagFilters=&facetFilters=%5B%5B%22available%3Atrue%22%5D%5D"
        },
        {
            "indexName":"newtype","params":"maxValuesPerFacet=50&query=&highlightPreTag=__ais-highlight__&highlightPostTag=__%2Fais-highlight__&page=0&hitsPerPage=1&filters=published%3Atrue%20AND%20NOT%20tags%3Ahidden%20AND%20NOT%20vip%3Atrue%20AND%20type%3A%22Model%20Kit%22%20AND%20line%3Ahg&attributesToRetrieve=%5B%5D&attributesToHighlight=%5B%5D&attributesToSnippet=%5B%5D&tagFilters=&analytics=false&clickAnalytics=false&facets=available"
        }
    ]
}


def main():
    res = requests.post(url=newtype_url, json=newtype_payload,headers=newtype_headers)
    # res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    print(soup)
    # driver.get("https://www.gundamplanet.com/collections/gunpla?sort_by=created-descending&filter.v.availability=1")
    # driver.get("https://newtype.us/t/model_kit?toggle[0]=available&sort=created_desc")
    # driver.get("https://www.usagundamstore.com/collections/hg-model-kits?view=products#/filter:ss_availability_filter:In$2520Stock")
    # driver.get("https://www.bigbadtoystore.com/Search?PageSize=100&Department=45790&itm_source=mega-menu&itm_medium=bbts-picks&itm_campaign=modelkits")
    time.sleep(60)
    # driver.quit()


if __name__ == '__main__':
    main()