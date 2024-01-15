# ==========================================
'''
pip3.9 install requests
pip3.9 install beautifulsoup4
'''
# ==========================================
'''
유스케이스: 
1. HTTP 요청 가능 여부를 테스트
2. 파싱된 응답에서 이미지 추출 가능 여부를 테스트
'''
# ==========================================
#-*-coding: utf-8-*-
import requests
from bs4 import BeautifulSoup as bs
# import pickle
import random
# from deep_translator import GoogleTranslator
import time
import os
from dotenv import load_dotenv
# from Zappos_Class_Batch_Test import IpRotator
import logging
from logging_config import CONFIG, DynamicNameFileHandler # TODO: 파일 위치 잘 잡나 확인

# .env 파일에서 환경 변수 불러오기
load_dotenv()

# 환경 변수 사용
ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
ERROR_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('ERROR_LOG_FILE')) # TODO: 최종 로그 저장 위치 바꾸기
IP_LOG_FILE = os.path.join(ROOT_DIR, '테스트 결과물 샘플', os.getenv('IP_LOG_FILE'))

class Request관리자(bs):
	'''
	상품 페이지 URL, 파일화 여부, IP 우회 여부를 받아 
	HTTP 요청 후 응답 반환
	(크롤링 가능성을 테스트해보기 위한 기본 클래스)
	'''
	def __init__(self, make_file=False, rotate_ip=True):
		'''
		url: 스크래핑할 페이지 url
		make_file: 파일화 여부. False면 응답 객체를 파일로 저장하지 않음.
		rotate_ip: IP 우회 여부. True면 IP를 우회해서 HTTP 요청함.
		'''
		# self.url = url
		self.make_file = make_file
		self.rotate_ip = rotate_ip

		## (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
		header_options = {
			# 사용자의 웹 브라우저의 식별자
			"my_user_agents" : ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
							'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
							'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1',  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'],
			
			# 클라이언트가 이해할 수 있는 컨텐츠 유형은 HTML, XHTML, XML, 이미지, 그리고 모든 다른 유형의 데이터임
			"accept" : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
			
			# 클라이언트가 이해할 수 있는 언어는 미국 영어와 영어임
			"accept_language" : 'en-US,en;q=0.5',
			
			# 웹사이트에 사용자의 행동을 추적하지 말라는 "Do Not Track(추적 금지)" 요청 헤더
			"dnt" : '1',
			
			# 네트워크 연결을 '유지'로 관리하기를 요청
			"connection" : 'keep-alive',
			
			# (클라이언트가)안전하지 않은 연결을 안전한 연결로 업그레이드하고자 함
			"upgrade_insecure_requests" : '1',
		}
        
		## 구글 크롬 + 윈도우 사용자
		self.headers2 = {
            'User-Agent': header_options.my_user_agents[0],
            'Accept': header_options.accept,
            'Accept-Language': header_options.accept_language,
            'DNT': header_options.dnt,  # Do Not Track Request Header
            'Connection': header_options.connection,
            'Upgrade-Insecure-Requests': header_options.upgrade_insecure_requests
        }
        ## 모질라 파이어폭스 + 맥OS 사용자
		self.headers3 = {
            'User-Agent': header_options.my_user_agents[1],
            'Accept': header_options.accept,
            'Accept-Language': header_options.accept_language,
            'DNT': header_options.dnt,  # Do Not Track Request Header
            'Connection': header_options.connection,
            'Upgrade-Insecure-Requests': header_options.upgrade_insecure_requests
        }
        ## 사파리 + 아이폰 사용자
		self.headers4 = {
            'User-Agent': header_options.my_user_agents[2],
            'Accept': header_options.accept,
            'Accept-Language': header_options.accept_language,
            'DNT': header_options.dnt,  # Do Not Track Request Header
            'Connection': header_options.connection,
            'Upgrade-Insecure-Requests': header_options.upgrade_insecure_requests
		}
		## 랜덤 사용자
		self.headers0 = {
			'User-Agent': random.choice(header_options.my_user_agents),
            'Accept': header_options.accept,
            'Accept-Language': header_options.accept_language,
            'DNT': header_options.dnt,  # Do Not Track Request Header
            'Connection': header_options.connection,
            'Upgrade-Insecure-Requests': header_options.upgrade_insecure_requests
		}
		## header2 기반 언더아머 전용 헤더
		self.headersUnderArmour = {
			'User-Agent': header_options.my_user_agents[0],
            'Accept': header_options.accept,
            'Accept-Language': header_options.accept_language,
            'DNT': header_options.dnt,  # Do Not Track Request Header
            'Connection': header_options.connection,
            'Upgrade-Insecure-Requests': header_options.upgrade_insecure_requests,
			'Sec-Fetch-User': '?1',
			'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
			'Sec-Ch-Ua-Mobile': '?0',
			'Sec-Ch-Ua-Platform': '"Windows"',
			'Sec-Fetch-Dest': 'document',
			'Sec-Fetch-Mode': 'navigate',
			'Sec-Fetch-Site': 'same-origin',
			'Cookie': 'ua-geo-data=KR; ua-target-result=/?valid=1&version_account=ms&version_cart=ms&version_checkout=ms&version_clp=ms&version_home=ms&version_pdp=ms&version_plp=ms&version_search=ms; at_check=true; AMCVS_A9733BC75245B1A30A490D4D%40AdobeOrg=1; notice_behavior=implied,eu; s_fid=7C7568B7FD29BD81-3D8A0773EFDA54C4; newVisitorCookie=second; utag_main=v_id:018cd41604f40010fae9cc04215d0506f002206700978$_sn:1$_se:2$_ss:0$_st:1704367093999$ses_id:1704365262073%3Bexp-session$_pn:2%3Bexp-session; AMCV_A9733BC75245B1A30A490D4D%40AdobeOrg=1585540135%7CMCMID%7C13075981143247442353154781213889489271%7CMCOPTOUT-1704372494s%7CNONE%7CvVersion%7C4.4.0; mbox=session#6890e4b31870437098f12aa082014326#1704367156|PC#6890e4b31870437098f12aa082014326.32_0#1767610096; BVImplmain_site=2471; s_sq=underarmourtealiumdev%3D%2526c.%2526a.%2526activitymap.%2526page%253Dhttps%25253A%25252F%25252Fwww.underarmour.com%25252Fen-us%25252Fp%25252Fcurry_brand_shoes_and_gear%25252Funisex_curry_11_dub_nation_basketball_shoes%25252F3026615.html%25253Fdwvar_3026615_size%25253D11%2525252F12.5%252526dwvar_3026615_color%25253D100%2526link%253DList%252520of%252520Product%252520Images%252520Close%252520Dialog%252520Scroll%252520to%252520product%252520image%2525201%252520Scroll%252520to%252520product%252520image%2525202%252520Scroll%252520to%252520product%252520image%2525203%252520Scroll%252520to%252520prod%2526region%253Dmain%2526.activitymap%2526.a%2526.c%2526pid%253Dhttps%25253A%25252F%25252Fwww.underarmour.com%25252Fen-us%25252Fp%25252Fcurry_brand_shoes_and_gear%25252Funisex_curry_11_dub_nation_basketball_shoes%25252F3026615.html%25253Fdwvar_3026615_size%25253D11%2525252F12.5%252526dwvar_3026615_color%25253D100%2526oid%253Dfunctionrg%252528%252529%25257B%25257D%2526oidt%253D2%2526ot%253DDIALOG; _dd_s=rum=2&id=d687491e-13c1-474c-87ec-28c59de16e6a&created=1704369862258&expire=1704371105286'
		}
	
	def request_http(self, url, make_file=False, rotate_ip=True):

		pass
	#  public 끝-------------------------


	# -------------------------------------

class IpRotator:
	def __init__(self, target_host):
		self.target_host = target_host

	def open_gateway(self):
		pass
	def shutdown_gateway(self):
		pass
	#  public 끝-------------------------

class HttpComunicator:
	def __init__(self, product_url, session):
		pass
	def request(self, product_url, session):
		pass
	#  public 끝-------------------------

# TODO: basicConfig의 
class ErrorLogWriter(logging):
	def __init__(self, target_file, is_ip_rotating, aws_region_name, error_message):
		pass
	def setup_file(self, target_file, is_ip_rotating, aws_region_name):
		logging.basicConfig(filename=target_file, level=logging.ERROR, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
	
	def log_error(self, error_message):
		# 그냥 'logger_zappos.info('ip기록')'
		# 'logger_zappos.error('에러기록')' 처럼 사용하면 됨.
		pass
	#  public 끝-------------------------

class Parser(bs):
	def __init__(self):
		pass
	def parse_response_to_soup(self, response):
		pass

class ImageExtractor:
	def __init__(self, parsed_response):
		pass
	def get_all_img_tags(self):
		pass
class UnderArmourImageExtractor(ImageExtractor):
	def __init__(self, parsed_response):
		pass
	def get_img_urls(self):
		pass

class ImageContext:
	def __init__(self):
		self.__strategy = None
	def set_strategy(self, strategy):
		self.__strategy = strategy
	def print_all_img_tags(self):
		if not self.__strategy:
			print('ImageExtractor 타입을 set_strategy해주지 않았습니다')
			return
		img_tags = self.__strategy.get_all_img_tags()
		for tag in img_tags:
			print(tag)

def main():
	"""Tests request with a URL"""
	
	# 1. HTTP 응답 받기
	url = ''
	requestAdmin = Request관리자()
	response = requestAdmin.request_http(url)

	# 2. 파싱
	parser = Parser()
	soup = parser.parse_response_to_soup(response)

	# 3. 파싱 객체에서 전체 이미지 태그 출력
	context = ImageContext()
	brand = input('브랜드(사이트)명 입력: ')
	if brand == 'UnderArmour':
		context.set_strategy(UnderArmourImageExtractor(soup))
	else: # 해당하는 브랜드명이 없는 모든 경우, 기본 타입 ImageExtractor로 지정
		context.set_strategy(ImageExtractor(soup))
	
	context.print_all_img_tags()




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
