from __future__  import print_function

import urllib3.contrib.pyopenssl
from pytradelib.utils import batch

urllib3.contrib.pyopenssl.inject_into_urllib3()

import requests
import grequests
from gevent import monkey
monkey.patch_all()

from pytradelib.logger import logger


class Downloader(object):
    def __init__(self, batch_size=100, sleep=None):
        self._batch_size = batch_size
        self._sleep = sleep

    @property
    def batch_size(self):
        return self._batch_size

    @batch_size.setter
    def batch_size(self, batch_size):
        self._batch_size = batch_size

    @property
    def sleep(self):
        return self._sleep

    @sleep.setter
    def sleep(self, sleep):
        self._sleep = sleep

    def download(self, urls):
        if isinstance(urls, str):
            return self._download(urls)
        return self._bulk_download(urls)

    def _download(self, url):
        logger.info('Download started: ' + url)
        try:
            r = requests.get(url)
            logger.info('Download completed: ' + url)
            if r.status_code == 200:
                return r.content
            r.raise_for_status()
        except requests.exceptions.Timeout as e:
            logger.error('Connection timed out: ' + e.__str__())
        except requests.exceptions.RequestException as e:
            logger.error('Error downloading: ' + e.__str__())
        return None

    def _bulk_download(self, urls):
        results = []
        for batched_urls in batch(urls, self.batch_size, self.sleep):
            for r in self.__bulk_download(batched_urls):
                print('finished downloading ' + r.url)
                results.append( (r.url, r.content) )
        return results

    def __bulk_download(self, urls, errors=None):
        errors = errors or []
        def exception_handler(req, ex):
            msg = 'Failed to download ' + req.url
            if isinstance(ex, requests.exceptions.Timeout):
                msg = 'Connection timed out: %(ex)s (%(url)s)' % {'ex': ex.__str__(), 'url': req.url}
            elif isinstance(ex, requests.exceptions.RequestException):
                msg = 'Error downloading: %(ex)s (%(url)s)' % {'ex': ex, 'url': req.url}
            errors.append(req.url)
            logger.error(msg)
        return grequests.map((grequests.get(url) for url in urls), exception_handler=exception_handler)