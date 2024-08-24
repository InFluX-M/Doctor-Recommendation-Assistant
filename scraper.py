import requests as req
from bs4 import BeautifulSoup
from bs4.element import Tag
import re
# import pandas as pd


class Paziresh24:
    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Microsoft Edge";v="128"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Upgrade-Insecure-Requests": "1",
        }

    # //a[@class="plasmic_all__wY2Hq plasmic_a__BSjOJ PlasmicProductCard_link__iYnI7__L4ml6"]

    def get_page(self, page: int):
        response = req.get(f"https://www.paziresh24.com/s/?page={page}", headers=self.headers)
        soup = BeautifulSoup(response.content, "html.parser")
        doctors: list[Tag] = soup.find_all("div", {"class": "plasmic_all__wY2Hq plasmic_root_reset__Hz2Yu plasmic_plasmic_default_styles__sA4Gj plasmic_plasmic_mixins__M49At plasmic_plasmic_tokens__DKeCq plasmic_plasmic_tokens__kU4gq PlasmicProductCard_root__dfpAk __wab_instance PlasmicSearchResults_productCard__NkCp3"})
        for doctor in doctors:
            name = doctor.find("h2").text
            rate = float(doctor.find("span", {"class": "plasmic_all__wY2Hq plasmic_span__3nUDA PlasmicProductCard_span__zMlGi__XAw7_"}).text)
            number_of_rates = int(re.findall(r'\d+', doctor.find("span", {"class": "plasmic_all__wY2Hq plasmic_span__3nUDA PlasmicProductCard_span__qbAn4__qqO0T"}).text)[0])
            tags = [tag.text for tag in doctor.find_all("div", {"class": "plasmic_all__SAkWn PlasmicChip_text__h2gZ7 PlasmicChip_textcolor_green__3Z_Cy"})]
            address = doctor.find("span", {"class": "plasmic_all__wY2Hq plasmic_span__3nUDA PlasmicProductCard_cardAddressRow__YUuOn"}).text



if __name__ == "__main__":
    crawler = Paziresh24()
    crawler.get_page(1)
