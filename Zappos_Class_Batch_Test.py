# ==========================================
'''
pip3.9 install requests
pip3.9 install gspread
pip3.9 install deep-translator
pip3.9 install beautifulsoup4
pip3.9 install requests-ip-rotator
pip3.9 install python-dotenv
'''
# ==========================================
#-*-coding: utf-8-*-
from bs4 import BeautifulSoup as bs
import requests
import pickle
from deep_translator import GoogleTranslator
import gspread
import random
import os
from requests_ip_rotator import ApiGateway, EXTRA_REGIONS, ALL_REGIONS
from dotenv import load_dotenv
import logging
import time

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 사용
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ERROR_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('ERROR_LOG_FILE')) # TODO: 최종 로그 저장 위치 바꾸기
IP_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('IP_LOG_FILE'))

class ZapposSoupTest(bs):
	'''
	주어진 URL의 색상 하나에 대한 html 상세설명을 작성함
	ex) <p>색상: Navy 2</p><img><img><img>
	'''
	def __init__(self, url, isTesting, size_type, ip_rotator):
		'''
		url: 스크래핑할 페이지 url
		isTesting: False면 응답 객체를 파일로 저장하지 않음
		size_type: 1(한국 사이즈로 변환 필요), 2(영문 사이즈 그대로 사용 가능), 3(키즈 신발)
		ip_rotator: IP 우회 게이트웨이와 세션을 가지는 클래스. 이 세션을 통해 get() 요청을 보내면 IP가 우회된다.
		'''
		# 디폴트 샘플: isTesting=False, size_type=2
		self.url = url
		self.size_type = size_type # 1: 한국 사이즈로 변환 필요 / 2: 영문 사이즈 그대로 사용 / 3: 키즈 신발
		self.r = ip_rotator

		## (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
        # 사용자의 웹 브라우저의 식별자
		my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
                          'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
                          'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1',  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']
		
        # 클라이언트가 이해할 수 있는 컨텐츠 유형은 HTML, XHTML, XML, 이미지, 그리고 모든 다른 유형의 데이터임
		accept = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
		
		# 클라이언트가 이해할 수 있는 언어는 미국 영어와 영어임
		accept_language = 'en-US,en;q=0.5'
		
		# 웹사이트에 사용자의 행동을 추적하지 말라는 "Do Not Track(추적 금지)" 요청 헤더
		dnt = '1'
		
		# 네트워크 연결을 '유지'로 관리하기를 요청
		connection = 'keep-alive'
		
		# (클라이언트가)안전하지 않은 연결을 안전한 연결로 업그레이드하고자 함
		upgrade_insecure_requests = '1'
		
		## 구글 크롬 + 윈도우 사용자
		self.headers2 = {
            'User-Agent': my_user_agents[0],
            'Accept': accept,
            'Accept-Language': accept_language,
            'DNT': dnt,  # Do Not Track Request Header
            'Connection': connection,
            'Upgrade-Insecure-Requests': upgrade_insecure_requests
        }
        ## 모질라 파이어폭스 + 맥OS 사용자
		self.headers3 = {
            'User-Agent': my_user_agents[1],
            'Accept': accept,
            'Accept-Language': accept_language,
            'DNT': dnt,  # Do Not Track Request Header
            'Connection': connection,
            'Upgrade-Insecure-Requests': upgrade_insecure_requests
        }
        ## 사파리 + 아이폰 사용자
		self.headers4 = {
            'User-Agent': my_user_agents[2],
            'Accept': accept,
            'Accept-Language': accept_language,
            'DNT': dnt,  # Do Not Track Request Header
            'Connection': connection,
            'Upgrade-Insecure-Requests': upgrade_insecure_requests
		}
		## 랜덤 사용자
		self.headers0 = {
			'User-Agent': random.choice(my_user_agents),
            'Accept': accept,
            'Accept-Language': accept_language,
            'DNT': dnt,  # Do Not Track Request Header
            'Connection': connection,
            'Upgrade-Insecure-Requests': upgrade_insecure_requests
		}

		# (테스트용)(=수정 필요)
		# 1. HTTP 응답을 파일에 저장 및 불러오기
		## 1-1. HTTP 응답 객체 자체 저장
		def test_save_webpage_response(url, headers):
			# print('-------- ! HTTP 요청함 ----------------')
			# response = self.r.session.get(url, headers=headers)
			# print(f'response code: {response.status_code}')
			response = self.get_webpage_response(url, headers)
			if response.status_code == 200:
				# TODO: 파일을 처음에 저장할 게 아니라, 데이터를 파싱하고서 sku 값을 append_code자리에 넣도록 마지막에 저장하도록 하기.
				index = -10
				while url[index] == '/':
					index -= 1
				append_code = url[-1] + url[index]
				# cur_directory = os.getcwd()
				file_path = os.path.join(ROOT_DIR, f'res_GoogleSheetsTest_{append_code}.pickle')
				with open(file_path, 'wb') as f:
					pickle.dump(response, f)
					print('Successfully saved HTTP response----------')
				return response
		## 1-2. 저장된 HTTP 응답 pickle 파일을 객체로 불러오기 
		def test_load_webpage_response(url, headers):
			try:
				index = -10
				while url[index] == '/':
					index -= 1
				append_code = url[-1] + url[index]
				# cur_directory = os.getcwd()
				file_path = os.path.join(ROOT_DIR, '테스트 결과물 샘플', f'res_kids_shoes_{append_code}.pickle')				
				with open(file_path, 'rb') as f:
					response = pickle.load(f)
					if (response.status_code == 200):
						print('Successfully loaded HTTP response----------')
				return response
			except FileNotFoundError as e:
				return test_save_webpage_response(url, headers)
				# test_load_webpage_response(url, headers)
			except:
				print(f'알 수 없는 에러 발생: {e.response.status_code}')
				raise

		# 2. HTTP 응답 사용하고 버리기
		## 2-1. 
		def get_webpage_response(url, headers):
			print('-------- ! HTTP 요청함 ----------------')
			for n in range(3):
				try:
					response = self.r.session.get(url, headers=headers)
					# response = requests.get("https://example.com")
					response.raise_for_status()
					# print("Request successful!")
					# print(f'"response code": "{response.status_code}"')
					# print(f'"request object[header]": "{response.request.headers}"')
					# print(f'"response header": "{response.headers}"')
					# # 응답 데이터 크기를 확인합니다.
					# response_size = len(response.content)
					# print(f'"Response size": "{response_size} bytes"')
					return response
				except requests.exceptions.RequestException as e:
					if n == 2:
						print("3번 요청 실패, 프로그램을 종료합니다")
						raise
					print()
					print(e)
					print("에러 발생: HTTP 재요청중 ---------------")
					time.sleep(n*2)
					continue
				except:
					print(f'알 수 없는 에러 발생: {e.response.status_code}')
					raise

		## 2-2. response 객체를 soup으로 파싱
		# ex) new_soup = parse_response_to_soup(load_webpage_response())
		def test_parse_response_to_soup(response):
			if (response.status_code == 200):
				soup = bs(response.content, "html.parser")
				return soup
		
		# 'test중' 이면 HTTP 응답을 파일로 저장하고 불러와 실행,
		if (isTesting is True):
			self.response = test_load_webpage_response(self.url, self.headers0)
		# 'test중' 이 아니면 매번 HTTP 요청을 보내며 실행
		else:
			self.response = get_webpage_response(self.url, self.headers0)
		self.soup = test_parse_response_to_soup(self.response)

		# 1. 상품 타이틀 (브랜드명+색상+상품명+영문상품명)
		self.full_name = ''
		self.brand_name = ''
		self.brand_name_ko_no_space = ''
		self.product_name = ''
		self.full_title = '' # 1 상품명

		# 달러 판매가
		self.oriprice = '' # 2 판매가

		# 현재 색상에 대한 정보
		self.color_name = '' 
		# self.options_of_this_color = []
		# self.options_quantity = 51 # 일괄로 51개
		self.options_size = [] 
		self.options_quantities = [] 
		self.options_size_text = '' # 3-1 옵션값
		self.options_quantities_text = '' # 3-2 옵션 재고수량
		self.images_of_this_color = []
		self.title_image = '' # 4 대표이미지
		self.description_ko_lines = [] # (현 색상) 설명 문구 리스트
		self.html_of_this_color = '' # 5 상세설명
		self.brand_ko_official = '' # 6 브랜드, 제조사

		# (추가) 전체 색상을 모았을 때 저장할 정보
		self.colors_name = [] 
		self.options_complete = []
		self.options_quantities = []
		self.description_per_color = [] # (색상별 상세설명 [description_ko_lines[], description_ko_lines[], ...])
		self.color_ids = []
		self.html_per_color = []
		self.html_complete = ''

		# 전체 품목, 남여 사이즈 변환 목록 모음
		# ex) size_tables[shoes][mens] = {7.0: 250, ...}
		self.size_tables = {}


	def set_all_of_this_color(self):
		# 1. 상품 타이틀 (브랜드명+색상+상품명+영문상품명)
		self.set_full_title() # 1 상품명

		# 달러 판매가
		self.set_oriprice() # 2 판매가

		# 현재 색상에 대한 정보
		self.set_color_name() 
		self.set_options_size() # 3-1 옵션값
		self.set_options_size_text()
		self.set_options_quantities() # 3-2 옵션 재고수량
		self.set_options_quantities_text()
		self.set_images_of_this_color()
		self.set_title_image() # 4 대표이미지
		self.set_description_ko_lines() # (현 색상) 설명 문구 리스트
		self.set_html_of_this_color() # 5 상세설명
		self.set_brand_ko_official() # 6 브랜드, 제조사


	def test_print_of_this_color(self):
		self.set_all_of_this_color()
		print("---------------------------------------------------------" * 2)
		print()
		print('1. 상품명')
		print(self.full_title)
			
		print()
		print('2. 판매가')
		print(self.oriprice)

		print()
		print('3. 옵션값, 옵션 재고수량')
		print(self.options_size_text)
		print(self.options_quantities_text)

		print()
		print('4. 대표이미지')
		print(self.title_image)

		print()
		print('4.5. 원본 url (추가이미지 자리)')
		print(self.url)

		print()
		print('5. 상세설명 HTML')
		print(self.html_of_this_color)

		print()
		print('6. 브랜드, 제조사')
		print(self.brand_ko_official)


	# (추가) 전체 색상을 모았을 때 실행할 수 있는 세팅
	def set_all(self):
		# self.set_product_name()
		self.set_product_title()
		self.get_oriprice()
		
		self.set_html_complete()

	# (추가) 전체 색상을 모았을 때 실행할 테스트 프린트
	def test_print_all_colors(self):
		self.set_all()
		print("---------------------------------------------------------" * 2)
		print()
		print('상품명')
		print(self.product_title)
			
		print()
		print('판매가')
		print(self.oriprice)

		print()
		print('색상 + 사이즈 옵션값 일체')
		print(self.options_of_this_color)
		print('옵션 전체 재고 수량(옵션과 개수가 맞는지)')
		print(self.options_quantities)

		# print()
		# print('대표이미지')
		# print()

		print()
		print('상세설명')
		print(self.html_complete)

		# print()
		# print('(추가) 브랜드, 제조사')
		# print()

	# =================================================================
	
	# 1. 상품명 full_title
	# TODO: get에 맞게 self. 이 아닌 return으로 수정 후, set에서 몽땅 self.로 세팅하도록 수정하기
	def get_full_name(self):
		title_meta_tag = self.soup.select_one("meta[itemprop='name']")
		if (title_meta_tag):
			full_name = title_meta_tag.get('content')
			return full_name
		else: 
			print('No <meta itemprop="name"> tag found')
	
	def get_brand_name(self):
		brand_span_tag = self.soup.select_one('span[itemprop="brand"]')
		if brand_span_tag:
			brand_name = brand_span_tag.select_one('a[itemprop="url"]').get('aria-label').strip()
			return brand_name
	
	def get_product_name(self):
		'''full_name - brand_name'''
		full_name = self.get_full_name()
		brand_name = self.get_brand_name()
		product_name = full_name.replace(brand_name, '').strip()
		return product_name
		
	def set_full_title(self):
		'''브랜드+상품명+영문상품명+색상
			(현재는 색상 뺌)
		'''
		self.full_name = self.get_full_name()
		self.brand_name = self.get_brand_name()
		self.product_name = self.get_product_name()
		
		brand_name_ko = self.translate(self.brand_name)
		self.brand_name_ko_no_space = ''.join(brand_name_ko.split(' '))
		product_name_ko = self.translate(self.product_name)
		color_name = self.get_color_name()
		color_name_ko = self.translate(color_name)
		self.full_title = f'{self.brand_name_ko_no_space} {product_name_ko} {self.product_name}'

	def translate(self, text):
		if (len(text) > 5000):
			print('5000자를 넘어갑니다. 조치 필요...')
		deep_translator = GoogleTranslator(source="auto", target="ko")
		translated = deep_translator.translate(text[:5000])
		return translated
	
	# 2. 판매가 oriPrice
	def get_oriprice(self):
		''' ('할인중') 달러 가격'''
		price_span_tags = self.soup.select('span[itemprop="price"]')
		for span in price_span_tags:
			if 'content' in span.attrs:
				return span['aria-label']
		return 'No price was found'
	def set_oriprice(self):
		''' $ 표시를 뺀 달러 가격을 oriprice로 저장'''
		self.oriprice = self.get_oriprice().replace('$', '')

	# 1.1. 색상명
	def get_color_name(self):
		color_inputs = self.soup.select('input[name="colorSelect"]')
		for input in color_inputs:
			sibling_label = input.find_next_sibling()
			if sibling_label is not None:
				if sibling_label['aria-current'] == 'true':
					return input['data-color-name']
	def set_color_name(self):
		self.color_name = self.get_color_name()


	# 3-1. 옵션값
	def get_size_tags(self):
		''' 품절을 고려하지 않고 존재하는 모든 옵션을 가져옴 '''
		size_input_tags = self.soup.select('input[data-track-label="size"]')
		return size_input_tags
	def is_womens(self):
		''' "Women's Sizes" 라는 텍스트 요소가 있을 것이라고 가정 '''
		gender_legend_tag = self.soup.select_one('legend[id="sizingChooser"]')
		if 'women' in gender_legend_tag.text.lower() or'woman' in gender_legend_tag.text.lower():
			return True
		else:
			return False
	def is_toddler(self):
		''' "Infant Size" 혹은 "Toddler Size"라는 텍스트 요소가 있을 것이라고 가정 '''
		kids_age_legend_tag = self.soup.select_one('legend[id="sizingChooser"]')
		if 'infant' in kids_age_legend_tag.text.lower() or'toddler' in kids_age_legend_tag.text.lower():
			return True
		else:
			return False

	def trim_valid_size_tags(self, input_tags, is_womens):
		''' 남성 신발: 7.0(250mm) ~ 14.0(320mm)까지 유효.
			여성 신발: 5.0(220mm) ~ 11.0(280mm)까지 유효.
			유효 사이즈만 태그 그대로 반환
			(유효 사이즈를 벗어나는 옵션들은 4/15 계산의 분모, 분자에 모두 셈하지 않게 된다)
		'''
		valid_tags = []
		for input in input_tags:
			size = input['data-label']
			# TODO: 어째서 float(size)여야 검사를 통과하는지...
			if is_womens is True and float(size) in self.size_tables['shoes']['womens']:
				valid_tags.append(input)
			elif is_womens is False and float(size) in self.size_tables['shoes']['mens']:
				valid_tags.append(input)
		return valid_tags
	def trim_valid_kids_size_tags(self, input_tags, is_toddler):
		''' Toddler(Infant포함): 7.0(130mm) ~ 10.0(160mm)까지 유효.
			Little Kid: 		10.5(165mm) ~ 3.0(220mm)까지 모두 유효.
			Big Kid: 			3.5(225mm) ~ 6.0(250mm)까지 유효.
			즉 7.0 이상인 'toddler'와, 6.5 혹은 7.0이 아닌 'not toddler' 사이즈만 태그 그대로 반환
		'''
		# 만약 전체 사이즈를 대상으로 한다면 is_toddler('infant'나 'toddler'라는 글자가 있는가)로 1~7.0까지 갈라낼 수 있을 것.
		# 하지만 7.0 ~ 6.0으로 잘라야 하므로, is_toddler이고 7.0 이상이거나 not is_toddler이고 6.0 이하일 때만 유효 사이즈로 삼아야 한다 => 안된다. little에는 10.0같은 수도 있어야 하므로... 그냥 6.5와 7.0만 명시적으로 빼자
		valid_tags = []
		for input in input_tags:
			size = float(input['data-label'])
			if is_toddler is True and size >= 7.0: # infant & toddler
				valid_tags.append(input)
			elif is_toddler is False and size != 6.5 and size != 7.0:
				valid_tags.append(input)
		return valid_tags

	def trim_instock_size_tags(self, valid_size_tags):
		''' 사이즈 태그 리스트 중 '재고 있음'인 태그만 모아 반환 '''
		instock_tags = []
		for tag in valid_size_tags:
			if "out of stock" not in tag.attrs["aria-label"].lower():
				instock_tags.append(tag)
		return instock_tags
	def is_over_4_of_15_instock(self, valid_size_tags):
		''' 사이즈가 포함된 태그 리스트 중 '재고 있음'이 
			전체의 4/15 이상 되는지 유무를 반환 '''
		instock_tags = self.trim_instock_size_tags(valid_size_tags)
		return len(instock_tags) / len(valid_size_tags) >= (4 / 15)
	def extract_sizes_and_transform(self, instock_size_tags, is_womens):
		# TODO: 그냥 '여자/남자'뿐만 아니라 품목 종류도 반영할 수 있도록 해야함. => 매개변수로 품목(shoes, bags, ...)을 받도록 하면 될까?
		sizes_transformed = []
		for tag in instock_size_tags:
			size = float(tag['data-label'])
			if is_womens == True:
				sizes_transformed.append(self.size_tables['shoes']['womens'][size])
			else:
				sizes_transformed.append(self.size_tables['shoes']['mens'][size])
		return sizes_transformed
	def extract_kids_sizes_and_transform(self, instock_size_tags):
		# TODO: 후에 size_table에 겹치는 아동 신발 사이즈가 존재하게 될 경우 이 코드도 수정해야 함
		sizes_original = []
		sizes_transformed = []
		for tag in instock_size_tags:
			size = float(tag['data-label'])
			sizes_original.append(size)
			sizes_transformed.append(self.size_tables['shoes']['kids'][size])
		print(sizes_original)
		return sizes_transformed
	def extract_sizes(self, instock_size_tags):
		return [tag['data-label'] for tag in instock_size_tags]
	
	def set_options_size(self):
		''' 얻은 사이즈 중 재고가 4/15 % 이상인 상품만 거를 것
		... 이었지만 현재는 '재고 있음'만 한국 사이즈로 변환 후 options_size로 저장 
			'재고 있음'이 4/15 % 이상이면 살리기
		'''
		if self.size_type == 1: # 신발 타입
			# 사이즈 변환 전역 변수를 세팅하고, 사이즈 태그를 가져오고  너무 크거나 작은 사이즈는 쳐내고 또 품절 아닌 항목만 다시 뽑고 거기서 사이즈 데이터 자체를 가져와 변환한다.
			self.set_size_tables()
			raw_tags = self.get_size_tags()
			is_womens = self.is_womens()
			valid_tags = self.trim_valid_size_tags(raw_tags, is_womens)
			instock_tags = self.trim_instock_size_tags(valid_tags)
			result_sizes = self.extract_sizes_and_transform(instock_tags, is_womens)
			print()
			print(result_sizes)
			self.options_size = result_sizes
			print()
		elif self.size_type == 2: # 영문 사이즈 그대로 사용 타입
			# 사이즈 태그를 가져오고, 품절 아닌 항목만 뽑고 거기서 사이즈 데이터를 영문 그대로 가져온다.
			raw_tags = self.get_size_tags()
			instock_tags = self.trim_instock_size_tags(raw_tags)
			result_sizes = self.extract_sizes(instock_tags)
			print()
			print(result_sizes)
			print()
			self.options_size = result_sizes
		elif self.size_type == 3: # 키즈 신발 타입
			# 사이즈표 전역 변수를 세팅하고, 사이즈 태그를 가져오고, 유아7~큰아동6까지 범위 밖의 사이즈는 져내고, 거기서 품절 아닌 항목만 뽑아 변환한다
			self.set_size_tables()
			raw_tags = self.get_size_tags()
			is_toddler = self.is_toddler()
			valid_tags = self.trim_valid_kids_size_tags(raw_tags, is_toddler)
			instock_tags = self.trim_instock_size_tags(valid_tags)
			result_sizes = self.extract_kids_sizes_and_transform(instock_tags)
			print()
			print(result_sizes)
			self.options_size = result_sizes


	def set_options_size_text(self):
		self.options_size_text = ','.join(str(size) for size in self.options_size)

	# TODO: 품목별, 성별 사이즈 표 계속 추가하기
	def set_size_tables(self):
		''' 호출 후 size_tables에 데이터를 저장 '''
		shoe_mens_size = {
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
		self.size_tables['shoes'] = {}
		self.size_tables['shoes']['mens'] = shoe_mens_size
		self.size_tables['shoes']['womens'] = shoe_womens_size
		self.size_tables['shoes']['kids'] = shoe_kids_size
	
	# 3-2. 옵션 재고수량
	def set_options_quantities(self):
		''' 그냥 11, 22, 33, ...개로 일괄 설정하기 '''
		if len(self.options_size) <= 9:
			quantities = [int(str(i) + str(i)) for i in range(1, len(self.options_size) + 1)]
		else: 
			quantities = [50 for i in self.options_size]
		self.options_quantities = quantities
	def set_options_quantities_text(self):
		self.options_quantities_text = ','.join(str(size) for size in self.options_quantities)
	
	# 상품 이미지 url 추출
	def get_images_of_this_color(self):
		img_tags = self.soup.select_one('div[id="stage"]').select('img')
		src_list = []
		for img in img_tags:
			if 'srcset' in img.attrs:
				index = img['src'].find('AC_SR')
				refined_img = '%sAC_SR800,1500_.jpg' % img['src'][:index]
				src_list.append(refined_img)
		return src_list
	def set_images_of_this_color(self):
		self.images_of_this_color = self.get_images_of_this_color()
	# 4. 대표 이미지 설정
	def set_title_image(self):
		self.title_image = self.images_of_this_color[0]
	

	# 5. 상세설명 HTML 작성
	# (현 색상) 설명 문구 리스트 저장
	def get_description_tags(self):
		description_ul = self.soup.select_one('div[itemprop="description"]').select_one('ul')
		li_tags = description_ul.findChildren('li', recursive=False) # ul의 직계 자식 레벨의 li 태그들만 선택
		return li_tags
	def get_translated_description(self):
		description_li_tags = self.get_description_tags()
		translated = []
		for description in description_li_tags:
			if 'sku' in description.text.lower():
				continue
			translated.append(self.translate(description.text))
		return translated
	def set_description_ko_lines(self):
		self.description_ko_lines = self.get_translated_description()

	# 설명 문구 html 만들기 #fontstyle변경 여기서
	def make_description_tags(self):
		''' '설명 문구'당 p 태그 만들기 '''
		tag_string = ''
		for des in self.description_ko_lines:
			tag_string += f'''<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 150%;"><b>{des}</b></p>\n'''
		return tag_string
	
	# 이미지 html 만들기
	def make_img_tag(self, img_url):
		return f'<img src="{img_url}" alt="{self.brand_name_ko_no_space}">'
	def make_img_tags(self):
		''' 이미지당 img 태그 만들기 '''
		tag_string = ''
		for url in self.images_of_this_color:
			tag_string += self.make_img_tag(url) + '\n'
		return tag_string

	# 전체 html 만들기
	def make_html_of_this_color(self):
		ko_description_detail = self.make_description_tags()
		product_images = self.make_img_tags()
		# 상세페이지 순서
		html = f'''<center style="width: 80%; margin: 0 auto;">
	<img src="https://m.media-amazon.com/images/G/01/Zappos/Ralph-Lauren-May-2023/Ralph-Lauren-Mens-MGrid.jpg"width="400">

	{product_images}

	<div style="display: block;">
	<img src="https://www.zappos.com/boutiques/3130/poloralphlauren_header110122.gif">
	</div>
	{ko_description_detail}

        	
	<img src="https://shop-phinf.pstatic.net/20231228_296/1703718751132RIyXT_JPEG/sizechartlogo.jpg?type=w860">
	</center>
	'''
		return html
	
	def set_html_of_this_color(self):
		self.html_of_this_color = self.make_html_of_this_color()


	# 6. 브랜드, 제조사
	# TODO: brand_name을 띄어쓰기 없앤 버전으로 확정
	def set_brand_ko_official(self):
		self.brand_ko_official = self.brand_name_ko_no_space


	# 다른 ZapposSoupTest 인스턴스를 받아서 작업할 수 있나? 그러면 색상별로 나머지 2개를 받아서 complete_html을 만들 수 있을 텐데.
	
	# -------------------------------------

# TODO: requests를 상속해줘야 하는지?
# TODO: 한 인스턴스당 별개의 gateway가 열리는 게 맞는지? 
class IpRotator():
	def __init__(self, target_host):
		# target_host 샘플: "https://www.zappos.com"
		# AWS에서 게이트웨이 객체를 생성하고 초기화합니다.
		self.gateway = ApiGateway(target_host, access_key_id=ACCESS_KEY, access_key_secret=SECRET_KEY)
		self.gateway.start()

		# 세션에 게이트웨이를 할당합니다.
		self.session = requests.Session()
		self.session.mount(target_host, self.gateway)

		# # 요청을 보냅니다. (IP는 무작위로 설정됩니다.)
		# self.response = self.session.get(target_page_url, params={"theme": "light"})
		# print(f'IP 우회 완료: {self.response.status_code}')

	def shutdown_gateway(self):
		# 게이트웨이를 삭제합니다.
		self.gateway.shutdown()
	
	# 내 아이피 테스트
	def test_ip(self):
		response = self.session.get("https://api64.ipify.org/")
		# print(response.headers)
		print()
		print(f'request object[headers]: {response.request.headers}')
		print(f'response header: {response.headers}')
		print(f'response object history: {response.history}')
		# 응답 데이터 크기를 확인합니다.
		response_size = len(response.content)
		print(f'Response (content) size: {response_size} bytes')
		print(f'Response total size: {len(response)} bytes') # => 유효하지 않은 접근
		print(response.text)
		

class GoogleSheetsTest():
	def __init__(self, sheet_file_name='대량등록 시트 테스트'):
		self.sheet_file_name = sheet_file_name

		# 구글 시트 연동 관련
		self.google_client = '' # Google Sheets API를 사용하기 위한 인증
		self.sh = '' # 스프레드시트(문서) 열기
		self.worksheet = '' # 작업할 시트
		self.set_google_client()
		self.set_sh()
		self.set_worksheet(0)

		# ZapposClass 연동 관련
		self.url = ''
		self.urls = []
		self.z = ''

		# IP 우회 관련
		self.ip_rotator = ''
		self.gateway = ''
		self.session = ''

	# 구글 시트 연동
	def set_google_client(self):
		# cur_directory = os.getcwd()
		# print(cur_directory)
		file_path = os.path.join(ROOT_DIR, 'python-crawling-gspread-145332f402e3.json')
		gc = gspread.service_account(filename=file_path)
		self.google_client = gc
	def set_sh(self):
		while True:
			try:
				self.sh = self.google_client.open(self.sheet_file_name)
				break
			except:
				self.sheet_file_name = input('존재하지 않는 스프레드시트입니다. 다시 입력해주세요: ')
	def set_worksheet(self, sheet_index=0):
		self.worksheet = self.sh.get_worksheet(sheet_index)

	# URL 가져오기
	def get_url(self, target_cell):
		url = self.worksheet.acell(target_cell).value
		return url
	def set_url(self, target_cell):
		self.url = self.get_url(target_cell)
	# s13 ~ s61 셀 한번에 읽어들이기
	def get_urls(self, start_cell, batch_size):
		# 'S13:S61' 범위의 셀 값을 읽어들이기 = start_cell:start_cell+batch_size - 1
		end_cell = f'S{int(start_cell[1:]) + batch_size - 1}'
		cells = self.worksheet.range(f'{start_cell}:{end_cell}')
		valid_urls = []
		for cell in cells:
			if cell.value and self.is_url(cell.value):
				valid_urls.append(cell.value)
		return valid_urls
	def set_urls(self, start_cell, batch_size):
		# cells = self.get_urls(start_cell, batch_size)
		# self.urls = [cell.value for cell in cells]
		self.urls = self.get_urls(start_cell, batch_size)
	def is_url(self, text):
		''' 문자열이 유효한 url 형식인지 검사
		 	('http'로 시작하는지 검사함) '''
		return 'http' in text
	
	# IP 우회 Gateway 연결 및 제거
	def set_gateway_and_session(self):
		self.ip_rotator = IpRotator("https://www.zappos.com")
		self.gateway = self.ip_rotator.gateway
		self.session = self.ip_rotator.session
	def shutdown_gateway(self):
		self.ip_rotator.shutdown_gateway()		


	# ZapposClass와 연결
	## ZapposCalss를 url을 넣어서 초기화하고, set_all_of_this_color()을 호출하고, z.product_title 등의 속성값으로 필요값을 불러온다. 
	## TODO: URL까지 넣어서 z를 초기화하도록 하지 말고, 한 인스턴스를 만들어 계속 url을 바꿔가며 쓸 수 있도록 수정하기
	def set_ZapposClass(self, url, isTesting, size_type, ip_rotator):
		self.z = ZapposSoupTest(url, isTesting, size_type, ip_rotator)
	def initialize_and_get_Zappos_data(self):
		self.z.set_all_of_this_color()

	# 10번 행에 넣기
	# 한 줄 만들기
	def make_row_data(self):
		''' 1. 상품명: C
			2. 판매가: E
			3. J, L
			4. R, S
			5. T
			6. U, V
		'''
		# '상세설명'이 20번째 열에 위치해 있다고 가정
		# data = [''] * 19 + [description]
		data = ['','', self.z.full_title, '', self.z.oriprice, '', '', '', '', self.z.options_size_text, '', self.z.options_quantities_text, '', '', '', '', '', self.z.title_image, self.z.url, self.z.html_of_this_color, self.z.brand_ko_official, self.z.brand_ko_official]
		# data = ['','', self.z.full_title, '', self.z.oriprice, '', '', '', '', '', '', '', '', '', '', '', '', self.z.title_image, self.z.url, self.z.html_of_this_color, self.z.brand_ko_official, self.z.brand_ko_official] # '옵션값'이 안될 때
		return data
	
	def add_rows_test(self, target_start_row, row_number):
		row_number = 2
		data = []
		# self.worksheet.insert_rows([],target_start_row, row_number)
		for i in range(target_start_row, target_start_row + row_number):
			# print(f'A{i}:V{i}')
			data.append(self.make_row_data())
			# data.append(['',f'data{i}'])
			# self.worksheet.update(f'A{i}:V{i}', [data])
		# print(data)
		self.worksheet.insert_rows(data, target_start_row)
		print(f'{row_number}줄 업로드 완료')
	def test_add_rows(self): # => 성공!
		# self.set_url('S77')
		url1 = 'https://www.zappos.com/p/polo-ralph-lauren-riali-loafer-polo-tan-heavyweight-smooth-leather/product/9513063/color/912296'
		url = 'https://www.zappos.com/p/polo-ralph-lauren-dezi-v-moccasin-slipper-chestnut/product/9625395/color/278'
		self.set_ZapposClass(url)
		self.initialize_and_get_Zappos_data()
		# print('sizes: ', self.z.options_size)
		data = self.make_row_data()
		for column in data:
			print(column)
		# self.add_rows_test(69, 2)

	def add_rows(self, target_start_row, data):
		self.worksheet.insert_rows(data, target_start_row)
		print(f'{len(data)}줄 업로드 완료')
	def test_add_rows_with_multi_urls(self): # => 성공!
		self.set_urls('S13', 'S17')
		data = []
		for url in self.urls:
			self.set_ZapposClass(url)
			self.initialize_and_get_Zappos_data()
			data.append(self.make_row_data())
		self.add_rows(target_start_row=69, data=data)
	def test_add_rows_with_multi_urls_without_making_res_files(self): # => 성공..!
		self.set_urls('S41', 'S41')
		data = []
		count = 40
		for url in self.urls:
			count += 1
			print(f'doing {count}...')
			self.set_ZapposClass(url, False)
			self.initialize_and_get_Zappos_data()
			data.append(self.make_row_data())
		self.add_rows(target_start_row=96, data=data)

	# 프록세 테스트
	def test_proxies(self):
		url = 'https://www.zappos.com/p/polo-ralph-lauren-dezi-v-moccasin-slipper-chestnut/product/9625395/color/278'
		# self.set_ZapposClass(url)
		ipify_url = 'https://api.ipify.org'
		res = requests.get(ipify_url)
		print('My IP: ', res.text)


def main():
	"""Tests request with a URL"""

	# url = 'https://www.zappos.com/p/polo-ralph-lauren-kids-logo-cotton-jersey-tee-toddler-little-kids-deckwash-white-freshwater/product/9911173/color/1060691'
	# z = ZapposSoupTest(url, isTesting=True, size_type=2)
	# print(zappos.soup.prettify()[:500])
	# print(zappos.soup.select_one("main").prettify()[:50000])
	# z.test_print_of_this_color()

	# Google Sheets Test --------------------------
	# g = GoogleSheetsTest()
	# g.test_add_rows_with_multi_urls_without_making_res_files()
	# g.test_add_rows()
	# g.test_proxies()

	ip_rotator = None
	def one():
		global ip_rotator
		# 멈추지 않고 상호작용
		print('============= 프로그램 시작 =============')
		print('한 url씩 상호작용 모드를 선택하셨습니다.')
		print()
		# 우회 IP 만들기
		print('우회 ip 만드는 중...')
		print()
		ip_rotator = IpRotator("https://www.zappos.com")
		# ip_rotator = IpRotator("https://api64.ipify.org")
		print('연동 완료')

		# 구글 시트 연동하기
		sheet_file_name = input('작업하고자 하는 구글 스프레드시트 문서 제목을 정확히 입력해주세요("대량등록 매크로야 힘내"를 선택하려면 그냥 엔터): ')
		if not sheet_file_name.strip():
			sheet_file_name = "대량등록 매크로야 힘내"
		g = GoogleSheetsTest(sheet_file_name)

		''' 필요한 사용자 입력: 
		1. 상호작용 모드
		2. 스프레드시트 제목
		3. 시트 어디에서 url을 가져와야 하는지
		3. 상품 종류 (사이즈 변환에 필요)
			=> womens, mens, kids, 아무것도 없는 경우
			=> 한국 사이즈로 변환이 필요한/필요하지 않은 경우
			-> self.size_tables 초기화를 달리

		=> 한 url을 한 트랜잭션으로 삼아서, 중간에 에러가 난 url에서 예외를 받아서 '다시 시도해 볼거냐'는 사용자 입력을 받을 때까지 기다리게 하기. 
		'''
		''' 큰 흐름: 
		1. 구글 시트 클래스 "g" 생성(= 구글 시트 연동)
		2. '시트의 몇 번 행 작업중' 프린트 넣기
		2. 구글 시트에서 url 읽어들이기 (g.url로 저장하든가 말든가)
		3. g.로 자포스 클래스 "g.z" 생성 (url 필요)
			= 1) url로 soup 생성됨
		4. 자포스 클래스 all_set() 메소드 호출 (상품 종류 입력 필요)
			= 사이즈표 생성됨, ...
			=> url마다 공유할 수 있는 항목: 전체 사이즈 변환표, ...을 설정하기 전에 일단 노가다로 만들어보자.
		5. 한 줄 만들기
		6. 한 줄 넣기 add_rows()로
		7. '다음 줄의 url로 계속하시겠습니까?' 로 반복
		8. g는 안 닫아줘도 되나?
		'''
		url_cell = None
		uploaded_row = None
		while True:
			# 컬럼 S에 모든 url이 들어 있다고 가정, 셀 번호 입력받기:
			user_input = input('url이 적힌 행 번호를 "17"과 같이 입력해주세요(종료를 원할 시 "q", 다음 줄의 url로 자동 진행은 엔터): ')
			if user_input.lower() == 'q':
				print('q를 입력하여 프로그램을 종료합니다.')
				print('============= 프로그램 종료 =============')
				break
			elif not user_input.strip():
				if not url_cell:
					print('처음 url 행 번호는 지정해줘야 합니다.')
					continue
				url_cell = 'S' + str(int(url_cell[1:]) + 1)
			else:
				url_cell = 'S' + str(user_input)

			# url 하나 가져오기
			print(f'{url_cell} 작업중...')
			g.set_url(url_cell)
			print()

			# 상품 종류 입력받기
			product_type = input('어떤 종류의 상품입니까? 1.신발 2.한국 사이즈로 변환하지 않아도 되는 종류 3.키즈 신발 : ')

			# 자포스 클래스 생성
			g.set_ZapposClass(g.url, False, int(product_type), ip_rotator)
			g.initialize_and_get_Zappos_data()

			# 한 줄 만들고 넣기
			target_start_row = None
			while not target_start_row:
				user_input_row_num = input('업로드할 행 번호를 (원본 url과 겹치지 않도록 가급적 최하단 행 번호를) 입력해주세요(이전에 업로드하던 행 하단에 계속 업로드 하려면 엔터): ')
				## TODO: target_start_row 유효성 검사하기
				if not user_input_row_num.strip():
					if not uploaded_row:
						print('처음 업로드 행 번호는 지정해줘야 합니다.')
						continue
					uploaded_row += 1
					target_start_row = uploaded_row
				elif not user_input_row_num.isdigit():
					print('유효한 행 번호를 입력해주세요')
					continue
				else:
					target_start_row = int(user_input_row_num)
					uploaded_row = target_start_row

			g.add_rows(int(target_start_row), [g.make_row_data()])

			# 다음 줄의 url로 계속하시겠습니까?

		# IP gateway 종료
		ip_rotator.shutdown_gateway()

	def run_one():
		''' one()을 실행하고 finally로 꼭 gateway shutdown 시키고, 로그 기록 '''
		global ip_rotator
		# 로깅 기본 설정: 에러 메시지를 'error.log' 파일에 기록하도록 설정
		logging.basicConfig(filename=ERROR_LOG_FILE, level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		try: 
			one()
		except Exception as e:
			logging.error("An error occurred: %s", e)
			# [날짜-시간 로그레벨: 메시지] 형식으로 메세지 기록
			# ex) 2024-01-03 01:46:05,123 ERROR: An error occurred: [에러 메시지]
			# 실제ex) ERROR:root:An error occurred: 403 Client Error: Forbidden for url: https://6fdh7z1wld.execute-api.eu-west-2.amazonaws.com/ProxyStage/p/lauren-ralph-lauren-patchwork-pique-polo-shirt-mascarpone-cream/product/9913039/color/263644
			# 수정한 형식ex) 2024-01-03 11:39:59,210 - root - ERROR - An error occurred: invalid literal for int() with base 10: ''
		finally:
			if ip_rotator is not None:
				ip_rotator.shutdown_gateway()
		# IP_LOG_FILE에 ip 패턴 정보도 기록?
				
	def proxy_test(): # => 성공
		# import pandas as pd 
		src = 'https://api64.ipify.org'
		ip_rotator = IpRotator(src)
		ip_rotator.test_ip()
		ip_rotator.test_ip()
		ip_rotator.test_ip()
		# response = requests.get('https://free-proxy-list.net/') 
		# df = pd.read_html(response.text)[0] 

		ip_rotator.shutdown_gateway()
	# proxy_test()
		

	def batch(batch_size):
		global ip_rotator
		# 멈추지 않고 상호작용
		print('============= 프로그램 시작 =============')
		print('여러 url 한 번에 읽고 한 줄씩 업로드 모드(Batch 모드)를 선택하셨습니다.')
		print()
		# 우회 IP 만들기
		print('우회 ip 만드는 중...')
		print()
		ip_rotator = IpRotator("https://www.zappos.com")
		print('연동 완료')

		# 구글 시트 연동하기
		sheet_file_name = input('작업하고자 하는 구글 스프레드시트 문서 제목을 정확히 입력해주세요("대량등록 매크로야 힘내"를 선택하려면 그냥 엔터): ')
		if not sheet_file_name.strip():
			sheet_file_name = "대량등록 매크로야 힘내"
		g = GoogleSheetsTest(sheet_file_name)
				
		# 상품 종류 입력받기
		product_type = input('어떤 종류의 상품입니까? 1.신발 2.한국 사이즈로 변환하지 않아도 되는 종류 3.키즈 신발 (품목을 변경하려면 다시 시작하세요): ')
		
		url_cell = None
		target_row = None
		while True:
			# 컬럼 S에 모든 url이 들어 있다고 가정, 셀 번호 입력받기:
			user_input = input(f'url이 적힌 시작 행 번호를 "17"과 같이 입력해주세요(종료를 원할 시 "q", 다음 {batch_size}개의 url로 자동 진행은 엔터): ')
			if user_input.lower() == 'q':
				print('q를 입력하여 프로그램을 종료합니다.')
				print('============= 프로그램 종료 =============')
				break
			elif not user_input.strip():
				if not url_cell:
					print('처음 url 행 번호는 지정해줘야 합니다.')
					continue
				url_cell = 'S' + str(int(url_cell[1:]) + batch_size)
				# target_row = 
			else:
				url_cell = 'S' + str(user_input)

			# url N개 가져오기
			g.set_urls(url_cell, batch_size)
			print(f'\n{url_cell}부터 {batch_size}개를 읽어옵니다')
			print()

			# 업로드 시작 행 번호 입력받기
			while not target_row:
				user_input_row_num = input('업로드할 행 번호를 (원본 url과 겹치지 않도록 가급적 최하단 행 번호를) 입력해주세요: ')
				## TODO: target_row 유효성 검사하기(''나 그냥 엔터도 not isdigit()이라고 검사해주나?)
				if not user_input_row_num.isdigit(): 
					print('유효한 행 번호를 입력해주세요')
					continue
				else:
					target_row = int(user_input_row_num)

			# 10 내에서 1~10까지 반복하는 
			for i, url in enumerate(g.urls):
				print('\n-----------------------------')
				print(f'{i + 1}/{len(g.urls)} (S{str(int(url_cell[1:]) + i)}) 작업중...')

				# 자포스 클래스 생성
				g.set_ZapposClass(url, False, int(product_type), ip_rotator)
				g.initialize_and_get_Zappos_data()
	
				# 한 줄 한 줄 삽입하기
				g.add_rows(int(target_row), [g.make_row_data()])
				target_row += 1
			# 한 행 지정해 여러 줄 낑겨넣기
			# data = 
			# g.add_rows(int(target_row), [g.make_row_data()])

			# 다음 줄의 url로 계속하시겠습니까?

		# IP gateway 종료
		ip_rotator.shutdown_gateway()

	def run_batch(batch_size):
		''' batch()을 실행하고 finally로 꼭 gateway shutdown 시키고, 로그 기록 '''
		global ip_rotator
		# 로깅 기본 설정: 에러 메시지를 'error.log' 파일에 기록하도록 설정
		logging.basicConfig(filename=ERROR_LOG_FILE, level=logging.ERROR, format='[Batch]%(asctime)s - %(name)s - %(levelname)s - %(message)s')
		try: 
			batch(batch_size)
		except Exception as e:
			logging.error("An error occurred: %s", e)
			# [날짜-시간 로그레벨: 메시지] 형식으로 메세지 기록
			# ex) 2024-01-03 01:46:05,123 ERROR: An error occurred: [에러 메시지]
			# 실제ex) ERROR:root:An error occurred: 403 Client Error: Forbidden for url: https://6fdh7z1wld.execute-api.eu-west-2.amazonaws.com/ProxyStage/p/lauren-ralph-lauren-patchwork-pique-polo-shirt-mascarpone-cream/product/9913039/color/263644
			# 수정한 형식ex) 2024-01-03 11:39:59,210 - root - ERROR - An error occurred: invalid literal for int() with base 10: ''
		finally:
			if ip_rotator is not None:
				ip_rotator.shutdown_gateway()

	# run_one()
	run_batch(batch_size=2)

if __name__ == '__main__':
	main()
