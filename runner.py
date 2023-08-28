from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from apteka import settings
from apteka.spiders.aptekaru import AptekaruSpider



if __name__ == '__main__':
    crawler_settings = Settings()
    crawler_settings.setmodule(settings)
    process = CrawlerProcess(settings=crawler_settings)
    process.crawl(AptekaruSpider)
    process.start()
