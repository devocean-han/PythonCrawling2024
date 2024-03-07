'''
Lacoste(라코스테) 추출자들을 모아놓은 모듈. 
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음

Lacoste는 특별히 Soup 객체가 아닌 순수 파이썬 Dict 객체를 받을 수 있음.
이 Dict은 사이트로부터 json으로 응답받은 메타데이터로,
만약 Soup이 아닌 Dict을 주입받은 경우 각 추출자는 그에 
해당하는 key로 뽑은 추출 데이터를 우선적으로 반환함
'''

import json
from pprint import pprint #TODO: 임시. 지울 것
import logging
from typing import Union 
from bs4 import BeautifulSoup as bs

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('Lacoste.Extractors')
SITE_OFFICIAL = 'Lacoste'

class LacosteMetadataExtractor(I.MetadataExtractor):
	def __init__(self) -> None:
		self.metadata_selectors = {
			'scripts': 'script[type="application/ld+json"]', # 3개
			'script_for_descriptions': 'script:-soup-contains("window.currentProduct")', # 6개 중 첫 번째를 사용
		}
	def get_metadata(self, soup: Union[bs, dict]):
		try:
			# 3개의 결과 중 2번째가 메타데이터. Vans(반스)와 구조가 같다. 사이즈 옵션이 동적으로 생성되는 것도 똑같음.
			script_tag = soup.select(self.metadata_selectors['scripts'])[1]
			metadata = json.loads(script_tag.string)
			product_name = metadata['name']
			title_description = metadata['description']
			brand = metadata['brand'] # 'Lacoste'
			sku = metadata['offers'][0]['sku'] # '196224231419' 같은 값 (url에 쓰이는 '46SMA0006'같은 값은 pid라고 구분)
			price = metadata['offers'][0]['price'] # '90.99'와 같이 '$' 없는 값
			return metadata
		except Exception as e:
			logger.error(e)
			return {}
	def get_metadata_for_descriptions(self, soup: Union[bs, dict]):
		try:
			script_tag = soup.select(self.metadata_selectors['script_for_descriptions'])[0]
			script_content = script_tag.string
			target_json = '='.join(script_content.split('window.')[2].split('=')[1:]).strip(';\n')
			# print(target_json)
			metadata = json.loads(target_json)
			# pprint(metadata)
			sku = metadata['color']['defaultId'] # '196224231402' 근데 이건 어느 색깔에서도 사용되지 않는 값이다 (그린='196224231419', 버건디='196224231662')
			pid_colorid = metadata['id'] # '46SMA0006-01U'
			product_name = metadata['name']
			title_desciptions = metadata['description']['descriptions'][0]['texts'] # 리스트로 반환
			bullet_desciptions = metadata['description']['descriptions'][0]['list']
			return metadata
		except Exception as e:
			logger.error(e)
			return {}


@export_strategy(SITE_OFFICIAL)
class LacosteProductNameExtractor(I.ProductNameExtractor):
	def __init__(self) -> None:
		self.product_name_selectors = {
			'h1': 'article h1.font-large',
			'script': 'script[type="application/ld+json"]',
		}	
	def get_product_name(self, soup: Union[bs, dict]) -> str:
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


@export_strategy(SITE_OFFICIAL)
class LacostePriceExtractor(I.PriceExtractor):
	def __init__(self) -> None:
		self.price_selectors = {
			'p': 'div.js-pdp-price.js-update-price-with-installments p',
		}
	def get_price(self, soup: Union[bs, dict]) -> str:
		try:
			if not isinstance(soup, bs): # Soup이 아니라 메타데이터 Dict이 주어진 경우 
				return soup['product']['pricing']['salesPrice']['format'] # ['value']는 소수점 없는 정수
			p_tag = soup.select_one(self.price_selectors['p']) # 할인p와 정가p 2개가 있지만 첫 번째 p를 선택
			price = p_tag.text.strip()
			return price
		except Exception as e:
			logger.error(e)
			return ''


@export_strategy(SITE_OFFICIAL)
class LacosteImagesExtractor(I.ImagesExtractor):
	def __init__(self) -> None:
		''' 여기 img 태그에서는 끝의 "impolicy=zoom"이 "imwidth=0000"보다 우선하여 적용됨 '''
		self.image_selectors = {
			'imgs': 'div.js-zoomable-group img',
		}
	def get_images(self, soup: Union[bs, dict]) -> list[str]:
		try:
			if not isinstance(soup, bs): # Soup이 아니라 메타데이터 Dict이 주어진 경우 
				images = soup['product']['gallery']['images']
				images = ['https:' + img['desktopUrl'] for img in images]
				return images
			img_tags = soup.select(self.image_selectors['imgs'])
			src_list = ['https:' + img['data-zoom-url'] for img in img_tags]
			return src_list
		except Exception as e:
			logger.error(e)
			return []


@export_strategy(SITE_OFFICIAL)
class LacosteDescriptionsExtractor(I.DescriptionsExtractor):
	def __init__(self) -> None:
		self.description_selectors = {
			'title_div': 'div.js-pdp-description-reload > div > div:last-of-type', # 2개의 div(sku용, 타이틀 문구용) 중 '마지막 div가 타이틀 문구'라는 가정이 변함이 덜할 것 같아 선택
			'bullet_lis': 'div.js-pdp-description-reload li', 
		}
	def get_descriptions(self, soup: Union[bs, dict]) -> list[list[str]]:
		try:
			if not isinstance(soup, bs): # Soup이 아니라 메타데이터 Dict이 주어진 경우 
				titles = soup['product']['description']['descriptions'][0]['texts']
				bullets = soup['product']['description']['descriptions'][0]['list']
				return [titles, bullets]
			title = soup.select_one(self.description_selectors['title_div']).text.strip()
			bullet_li_tags = soup.select(self.description_selectors['bullet_lis'])
			bullets = [li.text.strip() for li in bullet_li_tags]
			return [[title], bullets]
		except Exception as e:
			logger.error(e)
			return [[],[]]
		

# 사이즈: 셀레니움으로만 추출 가능 -> 
@export_strategy(SITE_OFFICIAL)
class LacosteSizeOptionsExtractor(I.SizeOptionsExtractor): # 라코스테 사이즈 옴션도 추출 불가, 중단
	def __init__(self) -> None:
		self.size_options_selectors = {
			'buttons': 'div.js-quick-view-scroll li button:not(.is-disabled)', # 품절 아닌 <button>만 선택
			'lis': 'div.js-quick-view-scroll li', # 실패
			'div1': 'div.js-quick-view-scroll', # 실패
			'div': 'div.popin-content-container', # 실패
			'script': 'script:-soup-contains("window.currentProduct")', # 실패
		}
	def get_size_options(self, soup: Union[bs, dict]) -> list[str]:
		''' 품절 아닌 사이즈 옵션 그대로 반환 '''
		try: 
			if not isinstance(soup, bs): # Soup이 아니라 메타데이터 Dict이 주어진 경우 
				sizes = soup['product']['variations']['size']['list']
				sizes = [size['label'] for size in sizes if size['unavailable'] == False]
				return sizes
			instock_button_tags = soup.select(self.size_options_selectors['script'])
			pprint(instock_button_tags)
			instock_sizes = [script.string for script in instock_button_tags if 'instock' in script.string]
			# instock_sizes = [button.text.strip() for button in instock_button_tags]
			print(len(instock_button_tags))
			# pprint(instock_sizes)
			return instock_sizes
		except Exception as e:
			logger.error(e)
			# raise
			return []
	

@export_strategy(SITE_OFFICIAL)
class LacosteSizeTransformer(I.SizeTransformer):
	def __init__(self) -> None:
		super().__init__()
	
	def trans_shoes_mens(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['mens'][float(size)]) 
					for size in size_list
					if float(size) in self.size_tables['shoes']['mens']]
		except Exception as e:
			logger.error(e, exc_info=True)
			return size_list
	def trans_shoes_womens(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['womens'][float(size)]) 
					for size in size_list
					if float(size) in self.size_tables['shoes']['womens']]
		except Exception as e:
			logger.error(e, exc_info=True)
			return size_list
	def trans_shoes_kids(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['kids'][float(size)]) 
					for size in size_list
					if float(size) in self.size_tables['shoes']['kids']]
		except Exception as e:
			logger.error(e, exc_info=True)
			return size_list


# 하단의 DirectJsonUrl 전략이 가능하므로 Selenior 전략은 활성화하지 않음
class LacosteSeleniumWaitSelectors(I.SeleniumWaitSelectors):
	def __init__(self) -> None:
		''' 라코스테는 2번의 클릭 기다림 후 사이즈 버튼 태그를 최종 기다림 '타겟 태그 요소'로 가짐 '''
		self.css_selectors_with_target_as_last_element = ["button.js-geolocation-stay.reverse-link", "button.js-pdp-select-size", "ul.grid-template-5 button"]

	def get_selectors(self) -> list[str]:
		return self.css_selectors_with_target_as_last_element


@export_strategy(SITE_OFFICIAL)
class LacosteDirectJsonUrlTransformer(I.DirectJsonUrlTransformer):
	def __init__(self) -> None:
		self.original_product_page_url_format = "https://www.lacoste.com/us/lacoste/men/clothing/button-down-shirts/men-s-reversible-cotton-flannel-shirt/CH0194-51.html?color=GBY"
		product_id_sample = 'CH0194-51'
		color_id_sample = 'GBY'
		self.direct_json_url_format = f"https://www.lacoste.com/on/demandware.store/Sites-FlagShip-Site/en_US/Product-PartialsData?pid={product_id_sample}&color={color_id_sample}&full=true"
	
	def transform_url(self, url) -> str:
		pid_and_cid = url.split('/')[-1]
		product_id = pid_and_cid.split('?')[0].replace('.html', '')
		color_id = pid_and_cid.split('?')[1].replace('color=', '')
		return f"https://www.lacoste.com/on/demandware.store/Sites-FlagShip-Site/en_US/Product-PartialsData?pid={product_id}&color={color_id}&full=true"


# __all__ = [
# 	'LacosteProductNameExtractor',
# 	'LacostePriceExtractor',
# 	'LacosteMetadataExtractor',
# 	'LacosteImagesExtractor',
# 	'LacosteDescriptionsExtractor',
# 	'LacosteSizeOptionsExtractor',
# 	'LacosteSizeTransformer',
# ]