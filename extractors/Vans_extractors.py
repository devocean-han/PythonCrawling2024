''' 
Vans(반스) 추출자(Extractor)들을 모아놓은 모듈.
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''
import json
import logging
from pprint import pprint

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

SITE_OFFICIAL = 'Vans'
logger = logging.getLogger(f'{SITE_OFFICIAL}.Extractors')


@export_strategy(SITE_OFFICIAL)
class VansMetaDataExtractor(I.MetadataExtractor):
	def __init__(self):
		self.meta_script_selectors = [
			'script[data-json-ld="product"]',
		]
	def get_metadata(self, soup):
		script_tag = soup.select_one(self.meta_script_selectors[0])
		metadata = json.loads(script_tag.string)
		# pprint(metadata)
		return metadata


@export_strategy(SITE_OFFICIAL)
class VansProductNameExtractor(I.ProductNameExtractor):
	def __init__(self) -> None:
		self.product_name_selector = 'h1.vf-heading__title'
	def get_product_name(self, soup) -> str:
		try:
			# metadata를 얻을 수 있는 경우:
			vans_metadata_extractor = VansMetaDataExtractor()
			metadata_dict = vans_metadata_extractor.get_metadata(soup)
			return metadata_dict.name	
		except:
			try: 
				product_name = soup.select_one(self.product_name_selector).text
				return product_name
			except:
				# logger.error(f'{soup} 에서 상품명을 찾을 수 없었습니다')
				return ''


@export_strategy(SITE_OFFICIAL)
class VansPriceExtractor(I.PriceExtractor):
	def __init__(self) -> None:
		self.discount_selector = 'ins.vf-price--sale'
		self.standard_selectors = [
			'div.vf-product-price',
			'div.vf-price.product__price',
		]
	def get_price(self, soup) -> str:
		try:
			# metadata를 얻을 수 있는 경우:
			vans_metadata_extractor = VansMetaDataExtractor()
			metadata_dict = vans_metadata_extractor.get_metadata(soup)
			return metadata_dict['offers']['price']	
		except : # KeyError:
			# TODO: 여기서부터 selector가 작동을 안 하는데 왜 그런지 모르겠음. 
			try: 
				discount_price_tag = soup.select_one(self.discount_selector)
				if discount_price_tag:
					return discount_price_tag.text.strip()
				return soup.select_one(self.standard_selectors[0]).text.strip()
			except:
				# logger.error(f'{soup} 에서 어떤 가격도 찾을 수 없었습니다')
				return ''


# @export_strategy(SITE_OFFICIAL)
class VansSizeOptionsExtractor(I.SizeOptionsExtractor): # 실패
	''' (실패) 반스는 사이즈 옵션을 동적으로 렌더링하고 있음. 따라서 
		초기 HTML로는 아래의 어떤 css selector로도 옵션 내용물 추출 불가'''
	def __init__(self):
		self.size_options_selectors = [
			'div.product-sizes__selector button',
			'div.product-sizes__options-swatch span',
			'',
		]
		self.size_out_of_stock_selector = 'button[aria-disabled="true"]'
		self.instock_size_options_selector = 'div.product-sizes__selector button.options-swatch__option:not(.disabled)'
	def get_size_options(self, soup):
		instock_size_options = soup.select(self.instock_size_options_selector)
		return instock_size_options


# @export_strategy(SITE_OFFICIAL)
class VansSizeTransformer(I.SizeTransformer): # 실패
	def __init__(self) -> None:
		super().__init__()

	def trans_shoes_mens(self, size_list):
		try:
			return [self.size_tables['shoes']['mens'][float(size)] for size in size_list if float(size) in self.size_tables['shoes']['mens']]
		except Exception as e:
			logger.error(e)
			return size_list
	def trans_shoes_womens(self, size_list):
		try:
			return [self.size_tables['shoes']['womens'][float(size)] for size in size_list if float(size) in self.size_tables['shoes']['womens']]
		except Exception as e:
			logger.error(e)
			return size_list
	def trans_shoes_kids(self, size_list):
		try:
			return [self.size_tables['shoes']['kids'][float(size)] for size in size_list if float(size) in self.size_tables['shoes']['kids']]
		except Exception as e:
			logger.error(e)
			return size_list


@export_strategy(SITE_OFFICIAL)
class VansImagesExtractor(I.ImagesExtractor): 
	def __init__(self) -> None:
		self.img_selectors = {
			'buttons': 'div.image-grid button[data-image-hr-src]'
		}
	def get_images(self, soup) -> list[str]:
		try:
			buttons = soup.select(self.img_selectors['buttons'])
			images = [button["data-image-hr-src"] for button in buttons]
			return images
		except:
			# logger.error(f'{soup}에서 상품 이미지를 찾지 못했습니다')
			return []
	def __transform_size(self, img_url_list) -> list[str]:
		''' 가로:세로 비율이 0.8:1.0 이 되도록 비율대로 줄인다
			(하지만 이미지 자체는 큰 사이즈로 두는 게 좋을 듯) '''
		target_width = 800
		height = int(target_width / 8 * 10)
		pass


@export_strategy(SITE_OFFICIAL)
class VansDescriptionsExtractor(I.DescriptionsExtractor):
	def __init__(self) -> None:
		self.description_selectors = {
			'div_outer': 'div#tab-panel-name-description-content',
			'div_inner': 'div.vf-product-details__description', 
		}
		self.descriptions = []
	def get_descriptions(self, soup) -> list[list[str]]:
		tag_list = self.__get_description_tag_list(soup)
		self.__set_long_and_bullet(tag_list)
		return self.descriptions
	def __get_description_tag_list(self, soup):
		description_tag = ''
		try:
			vans_metadata_extractor = VansMetaDataExtractor()
			metadata_dict = vans_metadata_extractor.get_metadata(soup)
			# html = json.dumps(metadata_dict['description'])
			raise # TODO: bs()가 "&lt;p&gt;" (=<p>)를 해독하지 못함
			description_tag = bs(metadata_dict['description'], "html.parser")
			print(description_tag)
			# 빈 태그로 겹겹이 감싸여 있으므로 텍스트 요소가 있는 태그만 추출
			all_tags = description_tag.find_all(True, recursive=False)
			tags_with_text = [tag for tag in all_tags if tag.string]
			return tags_with_text			
		except:
			# print('\n메타데이터에서 설명을 가져오지 못함\n')
			try: 
				description_tag = soup.select_one(self.description_selectors['div_inner'])
				# 빈 태그로 겹겹이 감싸여 있으므로 텍스트 요소가 있는 태그만 추출
				# 1) 자식이 아예 없는 경우: 최초 div 태그에 있는 text를 뽑아 bullet_descriptions에 넣음
				# 2) 자식이 있지만 <p> 와 <ul><li>로 정확히 나뉘지 않은 경우: 자연스럽게 모든 텍스트 태그가 bullet_descriptions로 들어가게 됨
				all_tags = description_tag.find_all(True, recursive=False)
				if len(all_tags) == 0:
					return [description_tag]
				tags_with_text = [tag for tag in all_tags if tag.string and tag.string.strip()]
				return tags_with_text			
			except:
				print('error occurred again')
				return []
		# finally:
		# 	# 빈 태그로 겹겹이 감싸여 있으므로 텍스트 요소가 있는 태그만 추출
		# 	all_tags = description_tag.find_all(True)
		# 	pprint(all_tags)
		# 	tags_with_text = [tag for tag in all_tags if tag.string]
		# 	return tags_with_text	
	def __set_long_and_bullet(self, tag_list):
		''' <p> 태그 2개는 장문형 설명, 나머지 <ul><li> 태그는 불렛 포인트형 '''
		long_descriptions = []
		bullet_descriptions = []
		for tag in tag_list:
			if tag.name == 'p':
				long_descriptions.append(tag.text.strip())
			else: # '<ul><li>' 혹은 <p>가 아닌 모든 태그
				bullet_descriptions.append(tag.text.strip())
		self.descriptions = [long_descriptions, bullet_descriptions]


@export_strategy(SITE_OFFICIAL)
class VansColorNameExtractor(I.ColorNameExtractor):
	def __init__(self) -> None:
		# 색상명 정보는 메타데이터 태그에 포함되지 않음
		self.color_name_selectors = {
			'h3': 'h3[data-id="colors-selector-on-static-pdp"]',
		}
	def f(self, soup):
		selector = 'div.product-colors[data-id="colors-selector-on-static-pdp"]'
		div_tag = soup.select_one(selector)
		children = div_tag.find_all(True, recursive=False)
		return children
	def get_color_name(self, soup) -> str:
		try:
			# "Color: Earth Tones Green Gables"와 같은 텍스트를 얻어옴
			color_name = soup.select_one(self.color_name_selectors['h3']).text
			if 'color:' in color_name.lower():
				color_name = color_name.split(':')[1].strip()
			return color_name
		except:
			# logger.error(f'{self.color_name_selectors["h3"]} 선택자로 색상명을 찾지 못했습니다')
			return ''


@export_strategy(SITE_OFFICIAL)
class VansColorUrlsExtractor(I.ColorUrlsExtractor):
	'''
	"https://www.vans.com/en-us/vn0a5krf8ee"과  
	"https://www.vans.com/en-us/shoes-c00081/old-skool-shoe-pvn0a5krf8ee"
	두 url이 같은 응답을 받음을 확인함(=색상id로 url 순회가 가능하다)
	'''
	def __init__(self) -> None:
		self.color_urls_selectors = {
			'parent_div': "div.color-swatch__wrapper[aria-label='Color']",
		}
	def get_color_urls(self, soup) -> list[str]:
		try:
			parent_div = soup.select_one(self.color_urls_selectors['parent_div'])
			print()
			buttons = parent_div.select('button')
			print(len(buttons))
			color_ids = []
			for button in buttons:
				color_id_name = button['aria-label']
				color_id = color_id_name.split(' - ')[0]
				color_ids.append(color_id)
			return self.__make_color_ids_to_urls(soup, color_ids)
		except Exception as e:
			# logger.error(f'색상 id 추출 중 문제가 발생했습니다')
			return []
	def __make_color_ids_to_urls(self, soup, color_ids):
		urls = ["https://www.vans.com/en-us/" + id.lower() for id in color_ids]
		return urls
	def __make_color_ids_to_half_exact_urls(self, soup, color_ids):
		try:
			vans_product_name_extractor = VansProductNameExtractor()
			product_name = vans_product_name_extractor.get_product_name(soup)
			product_name = '-'.join(product_name.lower().split(' '))
			urls = ["https://www.vans.com/en-us/" + product_name + "-p" + id.lower() for id in color_ids]
			return urls
		except:
			# logger.error(f'색상 url 추출 중 문제가 발생했습니다')
			return []