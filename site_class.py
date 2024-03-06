'''
'사이트 통솔자'는 
사이트 전체를 아우르는 하나의 통합 설계도를 구조로 가진다.
또한 Context의 역할을 하며, 외부 버튼은 set_site('브랜드명') 하나뿐으로
브랜드명을 단위로 문맥(Context)을 바꾸는 역할이다. 즉 브랜드명을 하나
입력받으면 그 사이트에 알맞은 추출자들을 전략으로 설정하는 작업을 
내부에서 수행한다. 
사이트(브랜드)마다 동원되는 추출자 개수가 다를 수 있으며 추출자가 없거나
반환되는 값이 없기도 한 경우에도 안전하게 처리하기 위해 다음과 같이 한다: 
	1. 기본 5개 추출자(상품명, 가격, 사이즈옵션, 이미지, 상세설명)는
		추출에 문제가 생길 경우 빈 리스트나 문자열을 디폴트 반환값으로
		설정해둔다.
	2. 사이트에 따라 사용되기도 하고 안 되기도 하는 추출자는
		분기할 수 있는 옵션을 만들어, 특정 추출자가 존재한다면 데이터를
		추출하는 작업을 추가한다. 특정 추출자가 존재한다는 것을 특정
		데이터가 추출 가능하다는 것과 동일한 의미로 사용하므로, 처음 
		추출자 전략 설정 작업에서 필요한 추가 추출자를 모두 연결하는
		것이 중요하다. 

'사이트 통솔자(반스)'를 생성하고 나면 다음과 같은 메시지 전송이 가능하다:
정제된 사이트명 반환('사이트명')
사이트 설정('사이트명')
데이터 전체 추출(soup, size_type)
구글 시트용으로 한 줄 데이터 반환(size_type)
get_selenium_wait_selectors(): 셀레니움을 위한 '기다림 selectors[]'가 설정돼있는 경우 반환
'''

import os 
# from dotenv import load_dotenv
# import json
# import re

# TODO: 각 extractors 임포트 삭제하기
# import Vans_extractors as V
# import Zappos_extractors as Z
# import Lacoste_extractors as L
# import Adidas_extractors as A
from strategy_factory import StrategyFactory
from extractors.extractors_interface import Translator
from namer import Namer
from images import IMAGES


''' '추출자'를 이용하는 모든 메서드에서, 다음과 같은 순서로 에러를 고려한다: 
	연결된 Extractor가 None일 수도, 
	추출하려는 선택자가 없을 수도, 
	에러는 안 났지만 추출 결과가 없을 수도.
'''
''' 예외 처리는 모두 __get() 메서드에서. self.속성 설정은 __set() 메서드에서 깔끔하게 '''
''' 예외 처리를 여기 SiteClass에서 하고 있으므로 '추출자'들에서는 하지 않도록 한다 '''

# load_dotenv()
# html_images_str = os.getenv("IMAGES")
# html_images_str = re.sub(r'#.*?\n', '', html_images_str) # 주석 문자열 제거
# html_images_dict = json.loads(html_images_str)


class SiteClass():
	def __init__(self) -> None:	
		self.strategy_names_all = [
			# 1. Product Name
			'product_name_strategy',
			'brand_name_strategy',
			# 2. Price
			'price_strategy',
			# 3. Size options
			'size_options_strategy',
			'size_type_strategy',
			'size_transform_strategy',
			# 'group_size_strategy',
			# 4. Images 
			'images_strategy',
			# 5. Descriptions
			'descriptions_strategy',
			# +6. Color
			'color_name_strategy',
			'color_urls_strategy',
			# +8. Metadata
			'metadata_strategy',
			# 9. Selenium Wait Selectors
			'selenium_wait_strategy',
			# 10. Direct Json Url Transformer
			'direct_json_url_transform_strategy',
		]		
		# 7. Translator
		self.translator = Translator()
		self.strategy_class_names_all = [
			# 1. Product Name
			'ProductNameExtractor',
			'BrandNameExtractor',
			# 2. Price
			'PriceExtractor',
			# 3. Size options
			'SizeOptionsExtractor',
			'SizeTypeExtractor',
			'SizeTransformer',
			# 'GroupSizeExtractor',
			# 4. Images 
			'ImagesExtractor',
			# 5. Descriptions
			'DescriptionsExtractor',
			# +6. Color
			'ColorNameExtractor',
			'ColorUrlsExtractor',
			# +8. Metadata
			'MetadataExtractor',
			# 9. Selenium Wait Selectors
			'SeleniumWaitSelectors',
			# 10. Direct Json Url Transformer
			'DirectJsonUrlTransformer',
		]		

	def set_site(self, site_official=None) -> None:
		while not site_official: # None 혹은 '': 사용자 인풋 받음
			# print(f'"{brand}"에 해당하는 브랜드를 찾을 수 없습니다')
			site = input('브랜드(사이트)명을 입력하세요: ')
			site_official = self.get_official_site_name(site)
		print(f'"{site_official}"를(을) 대상으로 추출을 진행합니다')
		self.site_official = site_official

		strategy_instances = StrategyFactory.create_strategies(site_official, self.strategy_class_names_all)
		for i, instance in enumerate(strategy_instances):
			setattr(self, self.strategy_names_all[i], instance)
		
		# 'json 직접 응답 가능'한 사이트인 경우, url 변환이 가능함을 플래그로 표시
		if self.direct_json_url_transform_strategy is not None:
			self.is_direct_json_extract_possible = True

		# TODO: 삭제 요망
		# if site_official == 'Vans':
		# 	self.product_name_strategy = V.VansProductNameExtractor()
		# 	self.price_strategy = V.VansPriceExtractor()
		# 	# self.color_name_strategy = V.VansColorNameExtractor()
		# 	# self.size_options_strategy = V.VansSizeOptionsExtractor()
		# 	# self.size_transform_strategy = V.VansSizeTransformer()
		# 	self.images_strategy = V.VansImagesExtractor()
		# 	self.descriptions_strategy = V.VansDescriptionsExtractor()
		# 	self.meta_data_strategy = V.VansMetaDataExtractor()
		# elif site_official == 'Zappos':
		# 	self.product_name_strategy = Z.ZapposProductNameExtractor()
		# 	self.brand_name_strategy = Z.ZapposBrandNameExtractor()
		# 	self.price_strategy = Z.ZapposPriceExtractor()
		# 	self.images_strategy = Z.ZapposImagesExtractor()
		# 	self.descriptions_strategy = Z.ZapposDescriptionsExtractor()
		# 	self.size_options_strategy = Z.ZapposSizeOptionsExtractor()
		# 	self.size_type_strategy = Z.ZapposSizeTypeExtractor()
		# 	self.size_transform_strategy = Z.ZapposSizeTransformer()
		# elif site_official == 'Fila':
		# 	pass
		# elif site_official == 'Lacoste':
		# 	# self.product_name_strategy = L.LacosteProductNameExtractor()
		# 	# self.price_strategy = L.LacostePriceExtractor()
		# 	# self.images_strategy = L.LacosteImagesExtractor()
		# 	# self.descriptions_strategy = L.LacosteDescriptionsExtractor()
		# 	# self.size_options_strategy = L.LacosteSizeOptionsExtractor()
		# 	# self.size_transform_strategy = L.LacosteSizeTransformer()
		# 	# self.direct_json_url_transform_strategy = L.LacosteDirectJsonUrlTransformer()

		# 	self.is_direct_json_extract_possible = True
		# 	# self.selenium_wait_strategy = L.LacosteSeleniumWaitSelectors()

		# 	strategy_instances = StrategyFactory.create_strategies(site_official, self.strategy_class_names_all)
		# 	for i, instance in enumerate(strategy_instances):
		# 		setattr(self, self.strategy_names_all[i], instance)

		# elif site_official == 'Adidas':
		# 	self.product_name_strategy = A.AdidasProductNameExtractor()
		# 	self.price_strategy = A.AdidasPriceExtractor()
		# 	self.images_strategy = A.AdidasImagesExtractor()
		# 	self.descriptions_strategy = A.AdidasDescriptionsExtractor()
		# 	self.size_options_strategy = A.AdidasSizeOptionsExtractor()
		# 	self.size_transform_strategy = A.AdidasSizeTransformer()
		# 	self.selenium_wait_strategy = A.AdidasSeleniumWaitSelectors()
		# elif site_official == 'North Face':
		# 	pass

	def get_official_site_name(self, site_name):
		'''"언더아머","Under Armour", "UnderArmour" 등의 한/영, 
		띄어쓰기 유무, 대/소문자 유무로 인해 다양한 인풋을 모아 
		하나의 공식 띄어쓰기 있는 영문 브랜드명으로 되돌림'''
		'''
		"Lauren Ralph Lauren", "Vans Kids" 같은 브랜드명이 
		막추출 될 때 모든 걸 key로 등록할 수는 없다. 딕셔너리가
		아니라 "'vans'가 포함된 인풋은 'Vans'로 반환"같은 메서드로
		만들어야 함
		'''
		return Namer.get_official_site_name(site_name)
	
	def set_all_data(self, soup, size_type) -> None:
		'''size_type이 3번 "키즈"인 경우 분기:
		대표이미지 PC에 저장 후 상품명, 가격, 상세페이지, PC 파일명 대표이미지만 넣은 row data를 반환
		그 외(1,2,4번)의 경우: 원래대로
		'''
		self.__set_full_title(soup)
		self.__set_price(soup)
		self.__set_size_options(soup, size_type)
		self.__set_size_quantity_options()
		self.__set_images(soup)
		self.__set_descriptions(soup)
		self.__set_color_name(soup)
		self.__set_html()


	def __set_full_title(self, soup):
		'''"한글브랜드 + 한글상품명 + 영문상품명" 조합의 상품 타이틀을 설정'''
		self.product_name = self.__get_product_name(soup)
		self.brand_name = self.__get_brand_name(soup)
		self.product_name_ko = self.translator.translate(self.product_name)
		self.brand_name_ko = ''.join(self.translator.translate(self.brand_name).split(' '))
		self.full_title = f'{self.brand_name_ko} {self.product_name_ko} {self.product_name}'
	def __get_product_name(self, soup):
		product_name = ''
		if self.product_name_strategy:
			try:
				product_name = self.product_name_strategy.get_product_name(soup)
			except:
				# error_logger.error('상품명을 찾지 못했습니다')				
				pass
		return product_name
	def __get_brand_name(self, soup):
		'''
		site_official과 brand_name의 차이:
		site_official: 정제된(official) 띄어쓰기 있는 영문 사이트명. ex) 자포스
		brand_name: 띄어쓰기 있는 추출한 그대로 영문 브랜드명 ex) 자포스에서 반스
		'''
		brand_name = '' 
		if self.site_official:
			brand_name = self.site_official
		if self.brand_name_strategy: # '자포스'같은 사이트라 브랜드 추출자가 설정된 경우
			try:
				brand_name = self.brand_name_strategy.get_brand_name(soup)
			except:
				# error_logger.error('브랜드명을 찾지 못했습니다')
				pass
		return brand_name

	def __set_price(self, soup):
		price = self.__get_price(soup)
		self.price = price.replace('$', '')
	def __get_price(self, soup):
		price = ''
		if self.price_strategy:
			try:
				price = self.price_strategy.get_price(soup)
			except:
				# error_logger.error('가격을 찾지 못했습니다')
				pass
		return price

	def __set_size_options(self, soup, size_type): # TODO: 사용자 입력 받는 size_type 인수 추가하기 
		self.size_options = self.__get_size_options(soup, size_type) 
	def __get_size_options(self, soup, size_type): 
		'''size_type: 1.남성 신발 2.여성 신발 3.키즈 신발 
			4.사이즈 변환하지 않아도 되는 옵션
			5.남성/여성을 자동 구분해서 변환하기(자포스,아식스)'''
		size_options = []
		if self.size_options_strategy:
			try:
				# 품절을 골라낸 size_options가 반환될 것임
				size_options = self.size_options_strategy.get_size_options(soup)
				# 사이즈 변환
				if size_type == 5:
					if self.size_type_strategy is None:
						print('현재 사이트는 사이즈 자동 구분이 불가능합니다. 남성 신발 사이즈로 변환을 진행합니다')
						size_type = 1
					else:
						size_type_text = self.size_type_strategy.get_size_type(soup)
						if  size_type_text == 'women':
							size_type = 2
						elif size_type_text in ['men', 'unisex']:
							size_type = 1
						elif size_type_text == 'kids':
							size_type = 3
						else: # size_type_text == ''
							# size_type_strategy는 있는데 적절한 사이즈 타입을 못찾은 경우
							print('적절한 사이즈 타입을 찾지 못했습니다. 남성 신발 사이즈로 변환을 진행합니다')
							size_type = 1
				if size_type != 4:
					size_options = self.__transform_size_options(size_options, size_type)
			except:
				# error_logger.error('사이즈 옵션을 찾지 못했습니다')
				pass
		return size_options
	def __transform_size_options(self, size_list, size_type):
		'''영문 사이즈 리스트를 받아 size_type에 맞게 '사이즈 변환자'의 
		메서드 호출, 반환'''
		if self.size_transform_strategy:
			try:
				if size_type == 1: # 성인 남성 신발
					size_list = self.size_transform_strategy.trans_shoes_mens(size_list)
				elif size_type == 2: # 성인 여성 신발
					size_list = self.size_transform_strategy.trans_shoes_womens(size_list)
				elif size_type == 3: # 아동 신발
					size_list = self.size_transform_strategy.trans_shoes_kids(size_list)
				else: 
					print('유효한 사이즈 옵션이 아닙니다')
			except Exception as e:
				# error_logger.error(f'사이즈 타입 {size_type}로의 사이즈 변환에 실패했습니다')
				# 사실 _extractor 레벨에서 에러발생 시 원본 사이즈 리스트를 반환하도록 하고 있기 때문에 이곳 site_class에서는 except에 걸릴 일이 없음
				print(e)
				pass
		return size_list

	def __set_size_quantity_options(self):
		'''11,22,33,...,99,10,11,...로 수량 설정'''
		quantities = []
		if self.size_options:
			quantities = [int(str(i) + str(i)) if i <= 9 else int(i) 
					for i in range(1, len(self.size_options) + 1)]
		self.size_quantity_options = quantities

	def __set_images(self, soup):
		'''타이틀 이미지와 이미지 목록을 설정'''
		self.images = self.__get_images(soup)
		title_image = ''
		if len(self.images) >= 1:
			title_image = self.images[0]
		self.title_image = title_image
	def __get_images(self, soup):
		images = []
		if self.images_strategy:
			try:
				images = self.images_strategy.get_images(soup)
			except:
				# error_logger.error('이미지를 찾지 못했습니다')
				pass
		return images

	def __set_descriptions(self, soup):
		'''[ [big,bold 설명], [기본 불렛형 설명] ] 형식으로 영문 상세설명을 설정
		첫번째 요소는 비어있을 수 있음'''
		descriptions = self.__get_descriptions(soup)
		self.descriptions = descriptions
	def __get_descriptions(self, soup):
		descriptions = []
		if self.descriptions_strategy:
			try:
				descriptions = self.descriptions_strategy.get_descriptions(soup)
			except:
				# error_logger.error('상세설명 문구를 찾지 못했습니다')
				pass
		return descriptions

	def __set_color_name(self, soup): # TODO: __set_color_urls()를 따로 만들어야 할까?
		'''색상명과 색상 url 목록을 설정
		찾지 못하면 각각 ''과 []로 설정됨'''
		self.color_name = self.__get_color_name(soup)
		self.color_urls = self.__get_color_urls(soup)
	def __get_color_name(self, soup): # TODO: '적절히' 한글로 변환해야 할 수도
		color_name = ''
		if self.color_name_strategy:
			try:
				color_name = self.color_name_strategy.get_color_name(soup)
			except:
				# error_logger.error('색상명을 찾지 못했습니다')
				print('색상명을 찾지 못했습니다')
				pass
		return color_name
	def __get_color_urls(self, soup):
		color_urls = []
		if self.color_urls_strategy:
			try:
				color_urls = self.color_urls_strategy.get_color_urls(soup)
			except:
				# error_logger.error('색상 url 목록을 찾지 못했습니다')
				print('색상 url 목록을 찾지 못했습니다')
				pass
		return color_urls

	def __set_html(self):
		self.html = self.__make_html()
	def __make_html(self):
		# .env에는 'site_official'과 일치하는 'brand_name'만 키로 들어 있으므로
		# 안전을 위해 날 것의 추출물일 brand_name을 get_official_site_name()에 넣어
		# 정제한다. (그래도 'Lauren Ralph Lauren'같은 경우는 'Polo Ralph Lauren'으로
		# 매칭되는 키-값 쌍이 없어 결국 default 이미지 세트가 쓰일 수 있음)
		brand_official = self.get_official_site_name(self.brand_name)
		static_images = IMAGES.get(brand_official)
		# 아예 유효하지 않은 브랜드명이면 디폴트 이미지를, 이미지를 적어넣지 않은 유효 브랜드명이면 자동으로 []를 호출해 아무 태그도 만들어 넣지 않음
		if static_images is None: 
			static_images = IMAGES.get('default', {})
		static_images_top = self.__make_static_img_tags(static_images.get('상', []), 'top')
		static_images_mid = self.__make_static_img_tags(static_images.get('중', []), 'mid')
		static_images_end = self.__make_static_img_tags(static_images.get('하', []), 'end')
		product_images = self.__make_product_img_tags()
		ko_title_descriptions = self.__make_ko_title_description_tags()
		ko_bullet_descriptions = self.__make_ko_bullet_description_tags()
		html = f'''<center style="width: 80%; margin: 0 auto;">
	{static_images_top}
	{product_images}
	<br/>
	<div style="display: block;">
		{static_images_mid}
	</div>
	<br/>
	{ko_title_descriptions}
	<br/>
	{ko_bullet_descriptions}	
	{static_images_end}
	</center>
	'''
		return html
	def __make_static_img_tags(self, images_list, position):
		'''position(상,중,하)에 해당하는 고정 이미지 tag 전체를 한 문자열로 반환'''
		tag_string = ''
		for url in images_list:
			if position == 'top':
				tag_string += self.__make_static_top_img_tag(url) + '\n\t'
			elif position == 'mid':
				tag_string += self.__make_static_mid_img_tag(url) + '\n\t\t'
			elif position == 'end':
				tag_string += self.__make_static_end_img_tag(url) + '\n\t'
		return tag_string
	def __make_static_top_img_tag(self, img_url): # TODO: 모든 이미지를 너비400px로 할 게 아니면 부모 수준에서 최대 크기 더 좁게 지정하고 <img>에서는 width를 뺴야함 
		'''url로 상단 고정 이미지 tag 하나를 만들어 문자열로 반환'''
		try:
			return f'<img src="{img_url}" width="400" style="max-width: 100%; height: auto;">'
		except:
			# error_logger.error(f'{img_url}을 이미지 태그로 변환에 실패했습니다')
			pass
			return ''
	def __make_static_mid_img_tag(self, img_url): 
		'''url로 중앙 고정 이미지 tag 하나를 만들어 문자열로 반환'''
		try:
			return f'<img src="{img_url}" style="max-width: 100%; height: auto;">'
		except:
			# error_logger.error(f'{img_url}을 이미지 태그로 변환에 실패했습니다')
			pass
			return ''
	def __make_static_end_img_tag(self, img_url):
		'''url로 하단 고정 이미지 tag 하나를 만들어 문자열로 반환'''
		try:
			return f'<img src="{img_url}" style="max-width: 100%; height: auto;">'
		except:
			# error_logger.error(f'{img_url}을 이미지 태그로 변환에 실패했습니다')
			pass
			return ''
	def __make_product_img_tags(self):
		'''상품 이미지 tag 전체를 한 문자열로 반환'''
		tag_string = ''
		for url in self.images:
			tag_string += self.__make_product_img_tag(url) + '\n'
		return tag_string
	def __make_product_img_tag(self, img_url):
		'''url로 상품 이미지 tag 하나를 만들어 문자열로 반환'''
		try:
			return f'<img src="{img_url}" alt="{self.brand_name_ko}" style="max-width: 100%; height: auto;">'
		except:
			# error_logger.error(f'{img_url}을 이미지 태그로 변환에 실패했습니다')
			pass
			return ''
	def __make_ko_title_description_tags(self):
		''''타이틀 설명 문구' p 태그들을 만들어 한 문자열로 반환
		(해당 설명 문구가 없으면 '' 반환)'''
		tag_string = ''
		for title in self.descriptions[0]:
			ko_title = self.translator.translate(title)
			tag_string += f'''<p style="font-size: 26px; font-family: 'Noto Sans'; line-height: 150%;"><b>{ko_title}</b></p>\n'''
		return tag_string
	def __make_ko_bullet_description_tags(self):
		''''불렛 설명 문구' p 태그들을 만들어 한 문자열로 반환
		(해당 설명 문구가 없으면 '' 반환)'''
		tag_string = ''
		for bullet in self.descriptions[1]:
			ko_bullet = self.translator.translate(bullet)
			tag_string += f'''<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>{ko_bullet}</b></p>\n'''
		return tag_string

	def get_sheet_formatted_row_data(self, size_type) -> list:
		'''size_type이 3번 "키즈"인 경우 분기:
		대표이미지 PC에 저장 후 상품명, 가격, 상세페이지, PC 파일명 대표이미지만 넣은 row data를 반환
		그 외(1,2,4,5번)의 경우: 원래대로. 
		'''
		if size_type == 3: # kids
			return self.__make_kids_row_data()
		return self.__make_row_data()
	def __make_kids_row_data(self): 
		'''
		1. 상품명: C
		2. 판매가: E
		4. 대표이미지(PC에 저장한 파일명): R
		5. 상세설명 HTML: T
		'''
		data = ['','', 
			self.full_title, '', 
			self.price, '', '', '', '', 
			'', '', '', '', '', '', '', '', 
			self.title_image, # 밖에서 title_image_file_name 로 교체,
			'', 
			self.html
		]
		return data
	def __make_row_data(self): # TODO: url은 여기서 넣을 수 없음
		'''
		1. 상품명: C
		2. 판매가: E
		3. 옵션값, 옵션재고수량: J, L
		4. 대표이미지(url), 추가이미지(->상품 원본 url): R, S
		5. 상세설명 HTML: T
		6. 브랜드, 제조사: U, V
		'''
		size_options_text = ','.join(str(size) for size in self.size_options)
		size_quantity_options_text = ','.join(str(size) for size in self.size_quantity_options)
		data = ['','', 
			self.full_title, '', 
			self.price, '', '', '', '', 
			size_options_text, '', size_quantity_options_text, '', '', '', '', '', 
			self.title_image, '',#self.url, 
			self.html, 
			self.brand_name_ko, self.brand_name_ko
		]
		return data
	
	def get_selenium_wait_selectors(self):
		''' 
		이 사이트의 selenium_wait_strategy가 설정되어 있을 경우 해당 selectors[]를,
		설정되어 있지 않은(None인) 경우 []을 반환
		'''
		selectors = []
		if self.selenium_wait_strategy:
			selectors = self.selenium_wait_strategy.get_selectors()
		return selectors

	def replace_to_direct_json_urls(self, urls):
		''' 
		이 사이트의 direct_json_url_transform_strategy가 설정되어 있을 경우
		원본 상품 페이지 url 목록을 '상품 메타데이터 json 직접 요청'이 
		가능한 url로 변환한 목록 반환,
		설정되어 있지 않은(변환 불가능한 사이트) 경우 기존 url 그대로 반환
		'''
		if self.direct_json_url_transform_strategy:
			try:
				urls = [self.direct_json_url_transform_strategy.transform_url(url)
					for url in urls]
			except Exception as e:
				# error_logger.error('json 직접 요청이 가능한 사이트이나 url 변환에 실패하였습니다. 원본 url로 우회 추출을 진행합니다')
				pass
		return urls


'''
SiteClass를 테스트하기 위한 테스트 클래스 정의
'''
from pprint import pprint
from bs4 import BeautifulSoup as bs
import pytest 

from request_classes import RequestAndSaveToPickle

# 테스트 데이터 정의
urls = [
	'https://www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj',
	'https://www.zappos.com/p/vans-ultrarange-exo-se-marshmallow-multi/product/9929668/color/1035520',
	'https://www.zappos.com/p/lacoste-angular-jq-123-1-cma-black-grey/product/9917410/color/139',
]
site_names_unofficial = [
	'반스',
	'zappos',
	'자포스',
]
site_names_official = [
	'Vans',
	'Zappos',
	'Zappos',
]
brand_names = [
	'',
	'Vans',
	'Lacoste',
]
product_names = [
	'',
	'Ultrarange Exo Se',
	'Angular JQ 123 1 CMA',
]
full_titles = [
	'',
	'반스 울트라레인지 엑소 Se Ultrarange Exo Se',
	'라코스테 각도 JQ 123 1 CMA Angular JQ 123 1 CMA',
]
prices = [
	'',
	'99.95',
	'135.00',
]
size_types = [4,3,5,]
htmls = [
	'',
	'''<center style="width: 80%; margin: 0 auto;">
	<img src="https://m.media-amazon.com/images/G/01/Zappos/Ralph-Lauren-May-2023/Ralph-Lauren-Mens-MGrid.jpg" width="400" style="max-width: 100%; height: auto;">
\t
	<img src="https://m.media-amazon.com/images/I/71e9EqVGOqL._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">
<img src="https://m.media-amazon.com/images/I/61RMh62td1L._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">
<img src="https://m.media-amazon.com/images/I/71MuFDxHBwL._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">
<img src="https://m.media-amazon.com/images/I/61SYTt0+5XL._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">
<img src="https://m.media-amazon.com/images/I/61xJXbJvKlL._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">
<img src="https://m.media-amazon.com/images/I/61ejt-x3OgL._AC_SR800,1500_.jpg" alt="반스" style="max-width: 100%; height: auto;">

	<br/>
	<div style="display: block;">
		<img src="https://www.zappos.com/boutiques/3130/poloralphlauren_header110122.gif" style="max-width: 100%; height: auto;">
\t\t
	</div>
	<br/>
	<p style="font-size: 26px; font-family: 'Noto Sans'; line-height: 150%;"><b>준비성을 정의하는 신발인 Vans™ Ultrarange Exo Se로 예상치 못한 일을 시작해보세요. 어떤 여행에도 견딜 수 있도록 디자인된 이 놀라운 스페셜 에디션은 발가락과 측벽 지지대를 위한 EXO 스켈레톤, 안전한 뒤꿈치 잠금 장치, 개선된 고무 발가락을 자랑합니다. Ultracush® 라이트 미드솔은 깃털처럼 가벼운 편안함을 보장하여 불편함을 먼 추억으로 만들어줍니다. 업데이트된 급속 용접 디테일과 레이스업 잠금장치로 움직임이 더욱 진화했습니다.</b></p>

	<br/>
	<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>가죽 및 합성 갑피.</b></p>
<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>섬유 안감.</b></p>
<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>섬유 깔창.</b></p>
<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>합성 아웃솔.</b></p>
<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>제품 치수는 남성 8, 여성 9.5, 너비 B - 중간 사이즈를 사용하여 측정되었습니다. 사이즈에 따라 측정값이 다를 수 있으니 참고하세요.</b></p>
<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 120%;"><b>측정:

 무게: 10온스</b></p>
\t
	<img src="https://shop-phinf.pstatic.net/20231228_296/1703718751132RIyXT_JPEG/sizechartlogo.jpg?type=w860" style="max-width: 100%; height: auto;">
\t
	</center>
	''',
	'',
]
row_formatted_data = [
	[],
	['','',
	'반스 울트라레인지 엑소 Se Ultrarange Exo Se', '',
	'99.95',	'',	'',	'',	'',	'',	'',	'',	'',	'',	'',	'',	'',
	'https://m.media-amazon.com/images/I/71e9EqVGOqL._AC_SR800,1500_.jpg', '',
	htmls[1]],
	['','',
	'라코스테 각도 JQ 123 1 CMA Angular JQ 123 1 CMA', '',
	'135.00',	'',	'',	'',	'',	
	'250,255,260,265,270,275,280,285,290,295,300,310',	'',	
	'11,22,33,44,55,66,77,88,99,10,11,12',	'',	'',	'',	'',	'',
	'https://m.media-amazon.com/images/I/71u7JoIP+WL._AC_SR800,1500_.jpg', '',
	htmls[2], '라코스테', '라코스테'],
]
# each_test_data = list(zip(urls, site_names_unofficial, site_names_official, brand_names, product_names, full_titles, prices, htmls, row_formatted_data))
data_dict = {
	'urls': urls,
	'site_names_unofficial': site_names_unofficial,
	'site_names_official': site_names_official,
	'brand_names': brand_names,
	'product_names': product_names,
	'full_titles': full_titles,
	'prices': prices,
	'size_types': size_types,
	'htmls': htmls,
	'row_formatted_data': row_formatted_data,
}
# def pytest_generate_tests(metafunc):
# 	if 'url' in metafunc.fixturenames:
# 		metafunc.parametrize('url', ['',''])

# @pytest.mark.parametrize('url,site_name_unofficial,site_name_official,brand_name,product_name,full_title,price,html,row_data', each_test_data[1])
class TestSiteClass():
	test_set_index = 2

	@pytest.fixture(scope="class")
	def sc(self):
		sc = SiteClass()
		official_site_name = sc.get_official_site_name(data_dict['site_names_unofficial'][self.test_set_index])
		sc.set_site(official_site_name)
		requestor = RequestAndSaveToPickle(sc.site_official)
		response = requestor.load_webpage_response(data_dict['urls'][self.test_set_index])
		soup = bs(response.content, "html.parser")
		sc.set_all_data(soup, data_dict['size_types'][self.test_set_index])
		return sc

	def test_site_official(self, sc):
		assert sc.site_official == data_dict['site_names_official'][self.test_set_index]

	def test_brand_name(self, sc):
		assert sc.brand_name == data_dict['brand_names'][self.test_set_index]
		
	def test_full_title(self, sc):
		assert sc.full_title == data_dict['full_titles'][self.test_set_index]
		
	def test_product_name_success(self, sc):
		assert sc.product_name == data_dict['product_names'][self.test_set_index]
		
	def test_price(self, sc):
		assert sc.price == data_dict['prices'][self.test_set_index]

	def test_html(self, sc):
		print(self, sc.html)
		assert sc.html == data_dict['htmls'][self.test_set_index]
		# assert '1977' in sc.html 
		
	def test_row_formatted_data(self, sc):
		row_data = sc.get_sheet_formatted_row_data(data_dict['size_types'][self.test_set_index])
		print(row_data)
		assert row_data == data_dict['row_formatted_data'][self.test_set_index]
		# assert row_data[-1] == sc.brand_name_ko

