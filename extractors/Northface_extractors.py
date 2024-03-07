url = 'https://www.thenorthface.com/en-us/mens/mens-footwear/mens-trail-run-c213281/mens-vectiv-infinite-2-futurelight-shoes-pNF0A8195?color=0ZP'

'''
North Face(노스페이스) 추출자들을 모아놓은 모듈. 
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''

import json
from pprint import pprint #TODO: 임시. 지울 것
import logging
from bs4 import BeautifulSoup as bs

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('North_Face.Extractors')
SITE_OFFICIAL = 'North Face'

@export_strategy(SITE_OFFICIAL)
class LacosteProductNameExtractor(I.ProductNameExtractor):
	def __init__(self) -> None:
		self.product_name_selectors = {
			'h1': 'article h1.font-large',
			'script': 'script[type="application/ld+json"]',
		}	
	def get_product_name(self, soup) -> str:
		try: #TODO: 'script' 선택자로는 안 해봤음
			if not isinstance(soup, bs): # Soup이 아니라 메타데이터 Dict이 주어진 경우 
				return soup['product']['name']
			script_tag = soup.select_one(self.product_name_selectors['script'])
			metadata = json.loads(script_tag.string)
			product_name = metadata['itemListElement'][-1]['item']['name']
			return product_name
		except Exception as e:
			logger.error(e)
			return ''
