from abc import ABC, abstractmethod
from deep_translator import GoogleTranslator

class ProductNameExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.product_name_selector = ''
	# @abstractmethod
	def get_product_name(self, soup) -> str:
		'''영문 상품명 반환'''
		try: 
			product_name = soup.select_one(self.product_name_selector).text
			return product_name
		except:
			# logger.error(f'{soup}에서 상품명을 찾을 수 없었습니다')
			return ''

class ProductNameKoreanExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.product_name_selector = ''
	# @abstractmethod
	def get_product_name(self, soup) -> str:
		'''공식 한글 상품명 반환'''
		pass

class BrandNameExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.brand_name_selector = ''
	@abstractmethod
	def get_brand_name(self, soup) -> str:
		'''영문 브랜드명 반환'''
		try: 
			brand_name = soup.select_one(self.brand_name_selector).text
			return brand_name
		except:
			# logger.error(f'{soup}에서 상품명을 찾을 수 없었습니다')
			return ''
		
class PriceExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.discount_selectors = {}
		self.standard_selectors = {}
	@abstractmethod
	def get_price(self, soup) -> str:
		'''추출한 그대로의 가격 반환 ($ 표시가 있든 없든)'''
		pass


class SizeOptionsExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.size_options_selectors = {}
	@abstractmethod
	def get_size_options(self, soup) -> list[str]:
		'''품절이 아닌 사이즈 옵션 그대로 반환 (변환 전). 
		사이즈 타입을 신경쓰지 않음 (사이즈 타입을 인자로 받지 않음)
		사이즈 '5'를 '5.0'이 아닌 '5' 그대로 반환 (변환 시 float으로 바꿔 검색)'''
		pass

class SizeTypeExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.size_type_selectors = {}
	@abstractmethod
	def get_size_type(self, soup) -> str:
		'''사이즈 타입을 반환
		(men/women/unisex/kids/'' 중 하나)'''
		pass

class SizeTransformer(ABC):
	@abstractmethod
	def __init__(self) -> None:
		shoe_mens_size = {
			3.5: 215,
			4.0: 220,
			4.5: 225,
			5.0: 230,
			5.5: 235,
			6.0: 240,
			6.5: 245,
			7.0: 250,
			7.5: 255,
			8.0: 260,
			8.5: 265,
			9.0: 270,
			9.5: 275,
			10.0: 280,
			10.5: 285,
			11.0: 290,
			11.5: 295,
			12.0: 300,
			12.5: 305,
			13.0: 310,
			13.5: 315,
			14.0: 320,
			15.0: 330,
		}
		shoe_womens_size = {
			5.0: 220,
			5.5: 225,
			6.0: 230,
			6.5: 235,
			7.0: 240,
			7.5: 245,
			8.0: 250,
			8.5: 255,
			9.0: 260,
			9.5: 265,
			10.0: 270,
			10.5: 275,
			11.0: 280,
			11.5: 285,
			12.0: 290,
			12.5: 295,
			13.0: 300,
			13.5: 305,
			14.0: 310,
			15.0: 320,
			16.0: 330,
		}
		shoe_kids_size = { # 추후 toddler(infant포함): {}, little: {}, big: {}로 나누기
			# infants: 1,2,3
			# toddlers: 4, 5, 5.5, 6.0, 6.5 ... , 10.0
			# little kids: 10.5, 11.0, 11.5, ... 13.5, 1.0, 1.5, ... , 3.0
			# big kids: 3.5, 4.0, ... , 7.0
			7.0: 130,
			7.5: 135,
			8.0: 140,
			8.5: 145,
			9.0: 150,
			9.5: 155,
			10.0: 160,
			10.5: 165,
			11.0: 170,
			11.5: 175,
			12.0: 180,
			12.5: 185,
			13.0: 190,
			13.5: 195,
			1.0: 200,
			1.5: 205,
			2.0: 210,
			2.5: 215,
			3.0: 220,
			3.5: 225,
			4.0: 230,
			4.5: 235,
			5.0: 240,
			5.5: 245,
			6.0: 250, 
			# 6.5: 255,
			# 7.0: 260,
		}
		shoe_kids_size_with_K = { 
			'7K': 130,
			'7.5K': 135,
			'8K': 140,
			'8.5K': 145,
			'9K': 150,
			'9.5K': 155,
			'10K': 160,
			'10.5K': 165,
			'11K': 170,
			'11.5K': 175,
			'12K': 180,
			'12.5K': 185,
			'13K': 190,
			'13.5K': 195,
			'1': 200,
			'1.5': 205,
			'2': 210,
			'2.5': 215,
			'3': 220,
			'3.5': 225,
			'4': 230,
			'4.5': 235,
			'5': 240,
			'5.5': 245,
			'6': 250, 
			# 6.5: 255,
			# 7.0: 260,
		}
		shoe_kids_size_with_front_K = { 
			'K7': 130,
			'K7.5': 135,
			'K8': 140,
			'K8.5': 145,
			'K9': 150,
			'K9.5': 155,
			'K10': 160,
			'K10.5': 165,
			'K11': 170,
			'K11.5': 175,
			'K12': 180,
			'K12.5': 185,
			'K13': 190,
			'K13.5': 195,
			'1': 200,
			'1.5': 205,
			'2': 210,
			'2.5': 215,
			'3': 220,
			'3.5': 225,
			'4': 230,
			'4.5': 235,
			'5': 240,
			'5.5': 245,
			'6': 250, 
			# 6.5: 255,
			# 7.0: 260,
		}
		shoe_kids_size_complete = { # 1K ~ 13.5K, 1.0 ~ 7.0까지
			'1.0K': 70,
			'2.0K': 80,
			'3.0K': 90,
			'4.0K': 100,
			'5.0K': 110,
			'5.5K': 115,
			'6.0K': 120, 
			'6.5K': 125,
			'7.0K': 130,
			'7.5K': 135,
			'8.0K': 140,
			'8.5K': 145,
			'9.0K': 150,
			'9.5K': 155,
			'10.0K': 160,
			'10.5K': 165,
			'11.0K': 170,
			'11.5K': 175,
			'12.0K': 180,
			'12.5K': 185,
			'13.0K': 190,
			'13.5K': 195,
			'1.0': 200,
			'1.5': 205,
			'2.0': 210,
			'2.5': 215,
			'3.0': 220,
			'3.5': 225,
			'4.0': 230,
			'4.5': 235,
			'5.0': 240,
			'5.5': 245,
			'6.0': 250, 
			'6.5': 255,
			'7.0': 260,
		}
		size_tables = {}
		size_tables['shoes'] = {}
		size_tables['shoes']['mens'] = shoe_mens_size
		size_tables['shoes']['womens'] = shoe_womens_size
		size_tables['shoes']['kids'] = shoe_kids_size
		size_tables['shoes']['kids_with_k'] = shoe_kids_size_with_K
		size_tables['shoes']['kids_with_front_k'] = shoe_kids_size_with_front_K
		self.size_tables = size_tables
	@abstractmethod
	def trans_shoes_mens(self, size_list) -> list[str]:
		'''남성 신발 사이즈로 변환하여 반환 (str 사이즈 -> str 사이즈)
		(float(size)로 안전 변환 필요)
		(변환 실패시 원본 리스트 반환)'''
		pass
	@abstractmethod
	def trans_shoes_womens(self, size_list) -> list[str]:
		'''여성 신발 사이즈로 변환하여 반환 (str 사이즈 -> str 사이즈)
		(float(size)로 안전 변환 필요)
		(변환 실패시 원본 리스트 반환)'''
		pass
	@abstractmethod
	def trans_shoes_kids(self, size_list) -> list[str]:
		'''아동 신발 사이즈로 변환하여 반환 (str 사이즈 -> str 사이즈)
		['kids'] = 3.0 (float(size)로 안전 변환 필요)
		['kids_with_k'] = '13K', '1', '1.5' (문자열 그대로 키를 조회)
		(변환 실패시 원본 리스트 반환)'''
		pass

class ImagesExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.image_selectors = {}
	@abstractmethod
	def get_images(self, soup) -> list[str]:
		'''이미지 url 리스트를 반환 (사이즈 변환해서?)'''
		pass

class DescriptionImagesExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.description_images_selectors = {}
	@abstractmethod
	def get_description_images(self, soup) -> list[str]:
		'''	설명 이미지 url들을 한 리스트로 반환 '''
		pass

class DescriptionsExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.description_selectors = {}
		self.descriptions = []
	@abstractmethod
	def get_descriptions(self, soup) -> list[list[str], list[str]]:
		'''[ [타이틀 설명], [불렛형 설명] ] 형태로 영문 상세설명을 반환
		('타이틀 설명'은 비어있을 수 있음)'''
		pass

class ColorNameExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.color_name_selectors = {}
	@abstractmethod
	def get_color_name(self, soup) -> str:
		'''영문 색상명 반환'''
		pass

class ColorUrlsExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.color_urls_selectors = {}
	@abstractmethod
	def get_color_urls(self, soup) -> list[str]:
		'''현재 페이지에서 찾을 수 있는 모든 색상 url을 반환
		(현재 색상 제외)'''
		pass

class MetadataExtractor(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.meta_script_selectors = {}
	@abstractmethod
	def get_metadata(self, soup) -> dict[str]:
		''' '''
		pass

class SeleniumWaitSelectors(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.css_selectors_with_target_as_last_element = []
	@abstractmethod
	def get_selectors(self) -> list[str]:
		''' 셀레니움을 이용한 html 추출용 CSS selectors를 반환
		(n번의 기다림+클릭 후 마지막 요소를 '타겟 기다림 태그'로 가지는)
		'''
		pass

class DirectJsonUrlTransformer(ABC):
	@abstractmethod
	def __init__(self) -> None:
		self.direct_json_url_format = ''
	@abstractmethod
	def transform_url(self, url) -> str:
		''' 해당 url을 'json 직접 추출이 가능한 url'로 변환 후 반환 '''
		pass

# TODO: Metadata, ColorName, ColorUrls 등등 추가
# TODO: Translator는 어디에 추가?

class Translator():
	def __init__(self) -> None:
		self.deep_translator = GoogleTranslator(source="auto", target="ko")
		pass
	def translate(self, text) -> str:
		translated = self.deep_translator.translate(text[:5000])
		if (len(text) > 5000):
			for i in range(5000, len(text), 5000):
				translated += self.deep_translator.translate(text[i:i+5000])
		return translated
	def translate_list(self, text_list):
		# TODO: 각 요소가 5000자 넘어가는 경우 구현하기
		translated_list = [self.deep_translator.translate(text) for text in text_list]
		return translated_list
	
