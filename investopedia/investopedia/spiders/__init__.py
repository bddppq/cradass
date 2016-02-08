import scrapy
from investopedia.items import TermItem
import string
import os


class TermSpider(scrapy.Spider):
    name = 'investopedia-terms'
    start_urls = ['http://www.investopedia.com/dictionary']

    def parse(self, response):
        for term_list_href in response.css('div.alphabet').xpath('./*/li/a[contains(@href, "/terms/")]/@href').extract():
            url = response.urljoin(term_list_href)
            yield scrapy.Request(url, callback=self.parse_term_list)

    def parse_term_list(self, response):
        # TODO: turns out there are multiple pages of terms starting with one alphabet
        for term_href in response.css('.big-item-title h3.item-title>a::attr(href)').extract():
            url = response.urljoin(term_href)
            yield scrapy.Request(url, callback=self.parse_term_item)

    def parse_term_item(self, response):
        # extract name
        name = response.css('.layout-title>h1').xpath('text()').extract()
        assert len(name) == 1
        name = name[0].strip()

        # extract explanation
        content = response.css('.content-box')
        assert len(content) == 1
        explanation = os.linesep.join(p.strip() for p in content.css('p').xpath('text()').extract())

        yield TermItem(name=name, url=response.url, explanation=explanation)
