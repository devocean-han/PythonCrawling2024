url = 'https://www.thenorthface.com/en-us/mens/mens-footwear/mens-trail-run-c213281/mens-vectiv-infinite-2-futurelight-shoes-pNF0A8195?color=0ZP'

'''
North Face(노스페이스) 추출자들을 모아놓은 모듈. 
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''

import json
from pprint import pprint
import logging
from bs4 import BeautifulSoup as bs

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('NorthFace.Extractors')
SITE_OFFICIAL = 'NorthFace'

