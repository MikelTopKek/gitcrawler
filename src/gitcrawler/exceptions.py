class CrawlerException(Exception):
    pass


class ParsingException(CrawlerException):
    pass


class ProxyException(CrawlerException):
    pass
