from datetime import datetime

import scrapy
from scrapy import Request
from scrapy.http import HtmlResponse
from itertools import islice

from apteka.items import AptekaItem
from apteka.settings import COOKIES, HOST_LINK, API_LINK


class AptekaruSpider(scrapy.Spider):
    name = "aptekaru"
    allowed_domains = ["apteka-ot-sklada.ru"]
    start_urls = ["https://apteka-ot-sklada.ru/api/catalog/search"]
    custom_settings = {'FEED_URI': "./apteka.json",
                       'FEED_FORMAT': 'json'}

    def parse(self, response: HtmlResponse):
        """ Главный каталог """
        main_catalog = self.get_data_dict(response)
        if main_catalog:
            for cat_name, cat_slug in islice(main_catalog.items(), 3):  # ограничение
                cat_url = f'{API_LINK}{cat_slug}'
                yield response.follow(url=cat_url,
                                      callback=self.parse_sub_cats)

    def parse_sub_cats(self, response: HtmlResponse):
        """ Категории одного элемента гл. каталога """

        sub_categories = self.get_data_dict(response)
        if sub_categories:
            for sub_cat_name, sub_cat_slug in islice(sub_categories.items(), 4):  # ограничение
                sub_cat_url = f'{API_LINK}{sub_cat_slug}'
                yield response.follow(url=sub_cat_url,
                                      callback=self.parse_sub_cat_section)

    def parse_sub_cat_section(self, response: HtmlResponse):
        """ Разделы категории """

        sub_cats_section = self.get_data_dict(response)
        if sub_cats_section:
            for cat_select_name, cat_select_slug in islice(sub_cats_section.items(), 3):  # ограничение
                select_products_url = f'{HOST_LINK}/catalog/{cat_select_slug}'
                yield response.follow(url=select_products_url,
                                      cookies=COOKIES,
                                      callback=self.parse_products,
                                      cb_kwargs=response.json().get('category'))

    def parse_products(self, response: HtmlResponse, **kwargs):
        """ Сбор href продуктов со страницы и переход на следующую """

        next_page = response.xpath("//a[@class='ui-pagination__link ui-pagination__link_direction']/@href").get()
        if next_page:
            yield response.follow(url=f"{HOST_LINK}{next_page}",
                                  cookies=COOKIES,
                                  callback=self.parse_products)

        products_list = response.xpath("//a[@class='goods-card__link']/@href").getall()
        for prod_link in products_list:
            yield response.follow(url=f"{HOST_LINK}{prod_link}",
                                  cookies=COOKIES,
                                  callback=self.parse_product,
                                  cb_kwargs=kwargs)

    @staticmethod
    def get_data_dict(response):
        """ Формирование словаря из ключа categories """
        _dict = {}
        if response.json().get('categories'):
            for el in response.json().get('categories'):
                _dict[el.get('name')] = el.get('slug')
        elif response.json().get('category').get('name') != 'Прочее':
            _dict[response.json().get('category').get('name')] = response.json().get('category').get('slug')
        return _dict

    @staticmethod
    def get_timestamp():
        return datetime.timestamp(datetime.now())

    def parse_product(self, response: HtmlResponse, **kwargs):
        """ Сбор информации с карточки продукта"""
        # main_category = kwargs.get('name')
        # sub_category = kwargs.get('parents')[0].get('name')
        timestamp = self.get_timestamp()
        RPC = 'отсутствует'
        url = response.url
        title = response.xpath("//h1[@class='text text_size_display-1 text_weight_bold']//text()").get()
        marketing_tags = list(map(lambda x: x.replace('\n', '').strip(), response.xpath(
            "//ul[@class='goods-tags__list goods-tags__list_direction_horizontal']//text()").getall()))
        brand = response.xpath("//span[@itemtype='legalName']/text()").get()
        section = [x for x in response.xpath("//ul[@class='ui-breadcrumbs__list']//text()").getall() if x != ' '][2:-1]
        price_data = {
            "current": 0.0,
            "original": 0.0,
            "sale_tag": ''
        }
        stock = {
            "in_stock": False,
            "count": 0,
        }
        assets = {
            "main_image": "",
            "set_images": response.xpath("//img[@class='goods-photo goods-gallery__picture']/@src").getall(),
            "view360": [],
            "video": []
        }
        metadata = {
            "__description": response.xpath("//div[@class='custom-html content-text']//text()").getall(),
            "АРТИКУЛ": "",
            "СТРАНА ПРОИЗВОДИТЕЛЬ": response.xpath("//span[@itemtype='location']/text()").get()
        }
        variants = 1
        goods_offer_panel = response.xpath("//div[@class='goods-offer-panel']")

        yield AptekaItem(
            timestamp=timestamp,
            RPC=RPC,
            url=url,
            title=title,
            marketing_tags=marketing_tags,
            brand=brand,
            section=section,
            price_data=price_data,
            stock=stock,
            assets=assets,
            metadata=metadata,
            variants=variants,
            goods_offer_panel=goods_offer_panel,
        )
