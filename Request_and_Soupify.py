# ==========================================
'''
pip3.9 install requests
pip3.9 install beautifulsoup4
'''
# ==========================================
#-*-coding: utf-8-*-
from bs4 import BeautifulSoup as bs
import requests
import pickle
from deep_translator import GoogleTranslator
import random
import time
import os
from dotenv import load_dotenv
from Zappos_Class_Batch_Test import IpRotator
import logging

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 사용
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ERROR_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('ERROR_LOG_FILE')) # TODO: 최종 로그 저장 위치 바꾸기
IP_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('IP_LOG_FILE'))

class RequestAndSoupifyTest(bs):
	'''
	주어진 URL 페이지를 HTTP 요청해와 soup으로 변형
	(크롤링 가능성을 테스트해보기 위한 기본 클래스)
	'''
	def __init__(self, url, isTesting, ip_rotator=None):
		'''
		url: 스크래핑할 페이지 url
		isTesting: False면 응답 객체를 파일로 저장하지 않음
		'''
		# 디폴트 샘플: ip_rotator=None
		self.url = url
		self.ip_rotator = ip_rotator

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
		## header2 기반 언더아머 전용 헤더
		self.headersUnderArmour = {
			'User-Agent': my_user_agents[0],
            'Accept': accept,
            'Accept-Language': accept_language,
            'DNT': dnt,  # Do Not Track Request Header
            'Connection': connection,
            'Upgrade-Insecure-Requests': upgrade_insecure_requests,
			'Sec-Fetch-User': '?1',
			'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
			'Sec-Ch-Ua-Mobile': '?0',
			'Sec-Ch-Ua-Platform': '"Windows"',
			'Sec-Fetch-Dest': 'document',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-Site': 'same-origin',
			'Cookie': 'ua-geo-data=KR; ua-target-result=/?valid=1&version_account=ms&version_cart=ms&version_checkout=ms&version_clp=ms&version_home=ms&version_pdp=ms&version_plp=ms&version_search=ms; at_check=true; AMCVS_A9733BC75245B1A30A490D4D%40AdobeOrg=1; notice_behavior=implied,eu; s_fid=7C7568B7FD29BD81-3D8A0773EFDA54C4; newVisitorCookie=second; utag_main=v_id:018cd41604f40010fae9cc04215d0506f002206700978$_sn:1$_se:2$_ss:0$_st:1704367093999$ses_id:1704365262073%3Bexp-session$_pn:2%3Bexp-session; AMCV_A9733BC75245B1A30A490D4D%40AdobeOrg=1585540135%7CMCMID%7C13075981143247442353154781213889489271%7CMCOPTOUT-1704372494s%7CNONE%7CvVersion%7C4.4.0; mbox=session#6890e4b31870437098f12aa082014326#1704367156|PC#6890e4b31870437098f12aa082014326.32_0#1767610096; BVImplmain_site=2471; s_sq=underarmourtealiumdev%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.underarmour.com%25252Fen-us%25252Fp%25252Fcurry_brand_shoes_and_gear%25252Funisex_curry_11_dub_nation_basketball_shoes%25252F3026615.html%25253Fdwvar_3026615_size%25253D11%2525252F12.5%252526dwvar_3026615_color%25253D100%2526link%253DList%252520of%252520Product%252520Images%252520Close%252520Dialog%252520Scroll%252520to%252520product%252520image%2525201%252520Scroll%252520to%252520product%252520image%2525202%252520Scroll%252520to%252520product%252520image%2525203%252520Scroll%252520to%252520prod%2526region%253Dmain%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.underarmour.com%25252Fen-us%25252Fp%25252Fcurry_brand_shoes_and_gear%25252Funisex_curry_11_dub_nation_basketball_shoes%25252F3026615.html%25253Fdwvar_3026615_size%25253D11%2525252F12.5%252526dwvar_3026615_color%25253D100%2526oid%253Dfunctionrg%252528%252529%25257B%25257D%2526oidt%253D2%2526ot%253DDIALOG; _dd_s=rum=2&id=d687491e-13c1-474c-87ec-28c59de16e6a&created=1704369862258&expire=1704371105286'
		}

		# (테스트용)(=수정 필요)
		# 1. HTTP 응답을 파일에 저장 및 불러오기
		## 1-1. HTTP 응답 객체 자체 저장
		def test_save_webpage_response(url, headers, ip_rotator):
			# print('-------- ! HTTP 요청함 ----------------')
			# response = self.r.session.get(url, headers=headers)
			# print(f'response code: {response.status_code}')
			response = get_webpage_response(url, headers, ip_rotator)
			if response.status_code == 200:
				# TODO: 파일을 처음에 저장할 게 아니라, 데이터를 파싱하고서 sku 값을 append_code자리에 넣도록 마지막에 저장하도록 하기.
				index = -10
				while url[index] == '/':
					index -= 1
				append_code = url[-1] + url[index]
				# cur_directory = os.getcwd()
				file_path = os.path.join(ROOT_DIR, '테스트 결과물 샘플', f'res_Nike_myPC_{append_code}.pickle')
				with open(file_path, 'wb') as f:
					pickle.dump(response, f)
					print('Successfully saved HTTP response----------')
				return response
		## 1-2. 저장된 HTTP 응답 pickle 파일을 객체로 불러오기 
		def test_load_webpage_response(url, headers, ip_rotator):
			try:
				index = -10
				while url[index] == '/':
					index -= 1
				append_code = url[-1] + url[index]
				# cur_directory = os.getcwd()
				file_path = os.path.join(ROOT_DIR, '테스트 결과물 샘플', f'res_Nike_myPC_{append_code}.pickle')				
				with open(file_path, 'rb') as f:
					response = pickle.load(f)
					if (response.status_code == 200):
						print('Successfully loaded HTTP response----------')
				return response
			except FileNotFoundError:
				return test_save_webpage_response(url, headers, ip_rotator)
				# test_load_webpage_response(url, headers)
		# 2. HTTP 응답 사용하고 버리기
		## 2-1. IP rotator(IP 우회)를 통한 요청:
		def get_webpage_response(url, headers, ip_rotator):
			print('-------- ! HTTP 요청함 ----------------')
			for n in range(3):
				try:
					if ip_rotator is not None:
						response = ip_rotator.session.get(url, headers=headers)
					else: 
						response = requests.get(url, headers=headers)
					response.raise_for_status()
					print("Request successful!")
					
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
				finally:
					print(f'"response code": "{response.status_code}"')
					print(f'"request object[header]": "{response.request.headers}"')
					print(f'"response header": "{response.headers}"')
					# 응답 데이터 크기를 확인합니다.
					response_size = len(response.content)
					print(f'"Response size": "{response_size} bytes"')
					print()
		# ## 2-2. 현재 IP로 요청:
		# def get_webpage_response(url, headers):
		# 	print('-------- ! HTTP 요청함 ----------------')
		# 	for n in range(3):
		# 		try:
		# 			response = requests.get(url, headers=headers)
		# 			# response = requests.get("https://example.com")
		# 			response.raise_for_status()
		# 			# print("Request successful!")
		# 			# print(f'"response code": "{response.status_code}"')
		# 			# print(f'"request object[header]": "{response.request.headers}"')
		# 			# print(f'"response header": "{response.headers}"')
		# 			# # 응답 데이터 크기를 확인합니다.
		# 			# response_size = len(response.content)
		# 			# print(f'"Response size": "{response_size} bytes"')
		# 			return response
		# 		except requests.exceptions.RequestException as e:
		# 			if n == 2:
		# 				print("3번 요청 실패, 프로그램을 종료합니다")
		# 				raise
		# 			print()
		# 			print(e)
		# 			print("에러 발생: HTTP 재요청중 ---------------")
		# 			time.sleep(n*2)
		# 			continue
		# 		except:
		# 			print(f'알 수 없는 에러 발생: {e.response.status_code}')
		# 			raise

		## 2-3. response 객체를 soup으로 파싱
		# ex) new_soup = parse_response_to_soup(load_webpage_response())
		def test_parse_response_to_soup(response):
			if (response.status_code == 200):
				soup = bs(response.content, "html.parser")
				return soup
		
		# 'test중' 이면 HTTP 응답을 파일로 저장하고 불러와 실행,
		if (isTesting is True):
			self.response = test_load_webpage_response(self.url, self.headers4, self.ip_rotator)
		# 'test중' 이 아니면 매번 HTTP 요청을 보내며 실행
		else:
			self.response = get_webpage_response(self.url, self.headers0, self.ip_rotator)
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
	def trim_valid_size_tags(self, input_tags, is_womens):
		''' 남성 신발: 7.0(250mm) ~ 14.0(320mm)까지 유효.
			여성 신발: 5.0(220mm) ~ 11.0(280mm)까지 유효.
			유효 사이즈만 한국 사이즈로 변환하여 반환
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
			print()
			print('raw_tags: ', len(raw_tags))
			is_womens = self.is_womens()
			print()
			print('is_womens: ', is_womens)
			valid_tags = self.trim_valid_size_tags(raw_tags, is_womens)
			print()
			print('valid_tags: ', len(valid_tags))
			instock_tags = self.trim_instock_size_tags(valid_tags)
			print()
			print('instock_tags: ', len(instock_tags))
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
		self.size_tables['shoes'] = {}
		self.size_tables['shoes']['mens'] = shoe_mens_size
		self.size_tables['shoes']['womens'] = shoe_womens_size
	
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
	# (실패)나이키 이미지 추출
	def get_Nike_images(self):
		img_tags = self.soup.select_one('div[id="pdp-6-up"]').select('img')
		src_list = [img['src'] for img in img_tags]
		all_img_tags = self.soup.select('img')
		return all_img_tags
	# (실패)언더아머 이미지 추출 - 아예 418에러 뜸. postman 크롬 확장도구 사용 검토중
	def get_UnderArmour_images(self):
		img_tags = self.soup.select_one('dialog[aria-labelledby="images-modal-title"]').select('img')
		src_list = [img['src'] for img in img_tags]
		all_img_tags = self.soup.select('img')
		return all_img_tags
	def set_images_of_this_color(self):
		# self.images_of_this_color = self.get_images_of_this_color()
		self.images_of_this_color = self.get_Nike_images()
		# self.images_of_this_color = self.get_UnderArmour_images()
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

def main():
	"""Tests request with a URL"""

	# # Nike test
	url = 'https://www.nike.com/t/pegasus-40-uswnt-mens-road-running-shoes-BWM0x2/FN0096-401'
	# rs = RequestAndSoupifyTest(url, isTesting=True)
	# print(rs.soup.select_one("div[id='pdp-6-up']").prettify()[:50000])
	# rs.set_images_of_this_color()
	# for src in rs.images_of_this_color:
	# 	print(src)
		
	# (성공)UnderArmour test with IP Rotator
	# url = 'https://www.underarmour.com/en-us/p/curry_brand_shoes_and_gear/unisex_curry_11_dub_nation_basketball_shoes/3026615.html?dwvar_3026615_size=11%2F12.5&dwvar_3026615_color=100'
	# 로깅 기본 설정: 에러 메시지를 'error.log' 파일에 기록하도록 설정
	logging.basicConfig(filename=ERROR_LOG_FILE, level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	# ip_rotator = IpRotator("https://www.nike.com")
	ip_rotator = None
	# try: 
	# 	rs = RequestAndSoupifyTest(url, isTesting=True, ip_rotator=ip_rotator)
	# 	# print(rs.soup.select_one('dialog[aria-labelledby="images-modal-title"]').prettify()[:50000])
	# 	# print(rs.soup.select('script[id=""]').prettify()[:50000])
	# 	rs.set_images_of_this_color()
	# 	print('-----')
	# 	for src in rs.images_of_this_color:
	# 		print()
	# 		print(src)
	# except Exception as e:
	# 	logging.error("An error occurred: %s", e)
	# finally:
	# 	if ip_rotator is not None:
	# 		ip_rotator.shutdown_gateway()

	# (실패)Nike 테스트 with requests_html
	from requests_html import HTMLSession
	try: 
		session = HTMLSession()
		response = session.get(url)
		response.html.render(sleep=4) # 웹 페이지를 렌더링
		response.html.page.setViewport({'width': 300, 'height': 600}) # 브라우저의 가로 길이를 800, 세로 길이를 600으로 설정
		response.html.render(sleep=4) # 웹 페이지를 렌더링
		# print(response.html.find('.slider').html) # 렌더링된 HTML 소스 코드 출력
		all_img_tags = response.html.find('img')
		for tag in all_img_tags:
			print()
			print(tag)
	except Exception as e:
		logging.error("An error occurred: %s", e)
	finally:
		if ip_rotator is not None:
			ip_rotator.shutdown_gateway()


if __name__ == '__main__':
	main()
