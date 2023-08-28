# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
import re
from collections import Counter

from apteka.settings import HOST_LINK


class AptekaPipeline:
    def process_item(self, item, spider):
        item['metadata']['__description'] = self.process_metadata(item)
        self.process_price_data(item)
        self.process_assets(item)
        item['metadata']['АРТИКУЛ'] = self.proces_get_art(item)

        del item['goods_offer_panel']
        print(f"{item['title']}\n \___> {item['url']}")
        return item

    def process_metadata(self, item):
        return re.sub("^\s+|\n|\t|\tB|\xa0|\r|\s+$", '', ' '.join(item['metadata']['__description']))

    def process_price_data(self, item):
        res = item.get('goods_offer_panel').css("span.ui-button__content::text").getall()
        if res[0] != 'Сообщить о поступлении':
            item['stock']['in_stock'] = True
            item['stock']['count'] = int(
                [el for el in item.get('goods_offer_panel').css("span.ui-link__text::text").get().split() if
                 el.isdigit()][0])
            item['price_data']['original'] = float(
                item.get('goods_offer_panel').css("span.ui-link__text > span::text").get().split()[1])

    def process_assets(self, item):
        counter = Counter(item['assets']['set_images'])
        main_image = [link for link, count in counter.items() if count > 1][0]
        item['assets']['set_images'].remove(main_image)
        item['assets']['main_image'] = f'{HOST_LINK}{main_image}'
        item['assets']['set_images'] = list(map(lambda x: f'{HOST_LINK}{x}', item['assets']['set_images']))

    def proces_get_art(self, item):
        if 'арт.' in item['title']:
            return item['title'].split()[-1]
        else:
            return item['url'].split('_')[-1]
