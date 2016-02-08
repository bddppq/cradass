import scrapy
from investopedia.items import TermItem
import string
import os
from urlparse import urlparse, parse_qs, ParseResult, urlunparse
from urllib import urlencode


class TermSpider(scrapy.Spider):
    name = 'investopedia-terms'
    start_urls = ['http://www.investopedia.com/dictionary']

    def parse(self, response):
        for term_list_href in response.css('div.alphabet').xpath('./*/li/a[contains(@href, "/terms/")]/@href').extract():
            url = response.urljoin(term_list_href)
            yield scrapy.Request(url, callback=self.parse_term_list_first)

    def parse_term_list_first(self, response):
        # use the "last page" button to figure out the total number
        # of pages
        last_page_btn = response.css('li.pager-last>a.btn::attr(href)')
        if not last_page_btn:
            # Only one page, no last page button. Current page is exactly that
            # single page.
            yield scrapy.Request(response.url, self.parse_term_list, dont_filter=True)
        else:
            last_page_url = response.urljoin(last_page_btn.extract()[0])
            parts = urlparse(last_page_url)
            queries = parse_qs(parts.query)
            page_count = int(queries['page'][0])
            for page_index in range(1, page_count + 1):
                # https://docs.python.org/2/library/urlparse.html
                new_queries = urlencode(dict(queries, page=str(page_index)))
                url = urlunparse(ParseResult(
                    parts.scheme, parts.netloc, parts.path,
                    parts.params, new_queries, parts.fragment
                ))
                yield scrapy.Request(url, self.parse_term_list)

    def parse_term_list(self, response):
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
        explanation = os.linesep.join(
            p.strip() for p in content.css('p').extract())

        yield TermItem(name=name, url=response.url, explanation=explanation)
