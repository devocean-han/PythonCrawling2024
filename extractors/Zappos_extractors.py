''' 
Zappos(자포스) 추출자(Extractor)들을 모아놓은 모듈.
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''
import json
import logging
from pprint import pprint

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

SITE_OFFICIAL = 'Zappos'
logger = logging.getLogger(f'{SITE_OFFICIAL}.Extractors')


@export_strategy(SITE_OFFICIAL)
class ZapposProductNameExtractor(I.ProductNameExtractor):
	def __init__(self) -> None:
		self.full_name_selector = "meta[itemprop='name']"

	def get_product_name(self, soup) -> str:
		try:
			brand_name_exctractor = ZapposBrandNameExtractor()
			brand_name = brand_name_exctractor.get_brand_name(soup)
			full_name = soup.select_one(self.full_name_selector)['content']
			product_name = full_name.replace(brand_name, '').strip()
			return product_name
		except Exception as e:
			# logger.error(e)
			# print(e)
			return ''


@export_strategy(SITE_OFFICIAL)
class ZapposBrandNameExtractor(I.BrandNameExtractor):
	def __init__(self) -> None:
		self.brand_name_selector = 'span[itemprop="brand"] span[itemprop="name"]'
	
	def get_brand_name(self, soup) -> str:
		try:
			brand_name = soup.select_one(self.brand_name_selector).text.strip()
			return brand_name
		except Exception as e:
			# logger.error(e)
			# print(e)
			return ''


@export_strategy(SITE_OFFICIAL)
class ZapposPriceExtractor(I.PriceExtractor):
	def __init__(self) -> None:
		self.price_selectors = {
			"span": 'span[itemprop="price"]',
		}
	
	def get_price(self, soup) -> str:
		try:
			price_span_tags = soup.select(self.price_selectors['span'])
			for span in price_span_tags:
				if 'content' in span.attrs:
					return span['aria-label']
			return ''
		except Exception as e:
			# logger.error(e)
			return ''


@export_strategy(SITE_OFFICIAL)
class ZapposImagesExtractor(I.ImagesExtractor):
	def __init__(self) -> None:
		self.image_selectors = {
			'imgs': 'div#stage img',
		}
	def get_images(self, soup) -> list[str]:
		try:
			img_tags = soup.select(self.image_selectors['imgs'])
			src_list = []
			for img in img_tags:
				if 'srcset' in img.attrs:
					index = img['src'].find('AC_SR')
					refined_img = '%sAC_SR800,1500_.jpg' % img['src'][:index]
					src_list.append(refined_img)
			return src_list
		except Exception as e:
			# logger.error(e)
			return []


@export_strategy(SITE_OFFICIAL)
class ZapposDescriptionsExtractor(I.DescriptionsExtractor):
	def __init__(self) -> None:
		self.description_selectors = {
			'lis': 'div[itemprop="description"] ul li', # 실패
			'ul': 'div[itemprop="description"] ul',
		}
	def get_descriptions(self, soup) -> list[list[str]]:
		try:
			# li_tags = soup.select(self.description_selectors['lis'], recursive=False) # recursive가 먹히지 않음 실패
			description_ul = soup.select_one(self.description_selectors['ul'])
			li_tags = description_ul.findChildren('li', recursive=False)
			for li in li_tags:
				if 'sku' in li.text.lower():
					continue
			descriptions = [li.text.strip() for li in li_tags if 'sku' not in li.text.lower()]
			# 첫 번째 불렛을 타이틀 설명으로 분류
			title = descriptions[0]
			bullets = descriptions[1:]
			return [[title], bullets]
		except Exception as e:
			# logger.error(e)
			print(e)
			return [[],[]]
		

@export_strategy(SITE_OFFICIAL)
class ZapposSizeOptionsExtractor(I.SizeOptionsExtractor):
	def __init__(self) -> None:
		self.size_options_selectors = {
			'inputs': 'input[data-track-label="size"]',
		}
	def get_size_options(self, soup) -> list[str]:
		try:
			input_tags = soup.select(self.size_options_selectors['inputs'])
			instock_sizes = []
			for tag in input_tags:
				if "out of stock" not in tag.attrs["aria-label"].lower():
					instock_sizes.append(tag['data-label'])
			return instock_sizes
		except Exception as e:
			# logger.error(e)
			return []


@export_strategy(SITE_OFFICIAL)
class ZapposSizeTypeExtractor(I.SizeTypeExtractor):
	def __init__(self) -> None:
		self.size_type_selectors = {
			'legend': 'legend#sizingChooser',
		}
	def get_size_type(self, soup) -> str:
		try:
			size_type_text = soup.select_one(self.size_type_selectors['legend']).text.lower()
			if 'women' in size_type_text or 'woman' in size_type_text:
				return 'women'
			elif 'men' in size_type_text or 'man' in size_type_text:
				return 'men'
			# elif 'infant' in size_type_text or 'toddler' in size_type_text:
			# 	return 'toddlers'
			# elif 'big' in size_type_text or 'little' in size_type_text:
			# 	return 'kids'
			elif 'unisex' in size_type_text:
				return 'unisex'
			elif 'big' in size_type_text or 'little' in size_type_text or 'infant' in size_type_text or 'toddler' in size_type_text:
				return 'kids'
			else:
				return ''
		except Exception as e:
			# logger.error(e)
			return ''


@export_strategy(SITE_OFFICIAL)
class ZapposSizeTransformer(I.SizeTransformer):
	def __init__(self) -> None:
		super().__init__()

	def trans_shoes_mens(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['mens'][float(size)]) 
		    		for size in size_list 
					if float(size) in self.size_tables['shoes']['mens']]
		except Exception as e:
			# logger.error(e)
			return size_list
		
	def trans_shoes_womens(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['womens'][float(size)]) 
		    		for size in size_list 
					if float(size) in self.size_tables['shoes']['womens']]
		except Exception as e:
			# logger.error(e)
			return size_list
		
	def trans_shoes_kids(self, size_list) -> list[str]:
		try:
			return [str(self.size_tables['shoes']['kids'][float(size)]) 
		    		for size in size_list 
					if float(size) in self.size_tables['shoes']['kids']]
		except Exception as e:
			# logger.error(e)
			return size_list

