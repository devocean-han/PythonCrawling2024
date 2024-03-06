''' Request 관련 클래스를 모아둔 모듈 
Requestor -> HTTP 응답 객체
RequestAndSaveToPickle -> Pickle 파일 (테스트용)
Selenior -> Html 문자열
SeleniorAndSavetoHtml -> Html 파일 (테스트용)
IP Rotator
등이 있을 예정
'''

# TODO: import 문 정리하기
# TODO: IP Rotator와 Google Sheetor 옮겨오기?
# TODO: 테스트 클래스 및 함수 다른 모듈로 분리하기 (테스트를 위해 더 임포트해야 하는 것들이 많아서)
#-*-coding: utf-8-*-
import requests
import pickle
import random
import time
import os
import hashlib
import logging

# from logging_config import set_logging
# set_logging(root_level=logging.INFO, '파이테스트')
iplogger = logging.getLogger('request.fail')
logger = logging.getLogger(__name__)

def make_response_to_log_message(response, error):
    message = ''
    status_code = response.status_code
    status = response.reason
    host = response.request.headers.get('Host') # 'https://swocil0jn1.execute-api.eu-west-3.amazonaws.com'
    region = host.split('.')[2] if host else ''
    ip = response.request.headers.get('X-My-X-Forwarded-For', '')
    message = '%-12s %-4s%-14s %-15s\n\t%s' % (region, status_code, status, ip, str(error))
    return message


ROOT_DIR = os.path.dirname(os.path.realpath(__file__))

class RequestAndSaveToPickle():
	''' HTTP 응답 성공(200) 시 pickle 파일로 변환하여 각 사이트 폴더에 저장
		__init__(custom_site_name, headers_num, ip_rotator)
		load_webpage_response(url): 파일에서 객체 반환. 없으면 저장 후 반환 
		save_webpage_response(url): 파일 저장 후 객체 반환 
		TODO: 'save'는 꼭 객체를 반환해야 할까? 
	'''
	## (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
	# 사용자의 웹 브라우저의 식별자
	my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36', # 라코스테의 경우 이 User Agent로 요청하면 403 Forbidden 거부당함(!)
						'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
						'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1',
						'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']

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
	headers1 = {
		'User-Agent': my_user_agents[3],
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 모질라 파이어폭스 + 맥OS 사용자
	headers2 = {
		'User-Agent': my_user_agents[1],
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 사파리 + 아이폰 사용자 + application/json으로 요청
	headers3 = {
		'User-Agent': my_user_agents[2],
		'Accept': 'application/json',
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 랜덤 사용자
	headers0 = {
		'User-Agent': random.choice(my_user_agents),
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}

	headers_list = [headers0, headers1, headers2, headers3]

	def __init__(self, site_official, headers_num=0, ip_rotator=None):
		self.SITE_OFFICIAL_PASCAL = ''.join(site_official.split(' '))
		self.SITE_PAGES_DIR = os.path.join(ROOT_DIR, 'tests', 'page_samples', self.SITE_OFFICIAL_PASCAL+'_page_samples')
		self.ip_rotator = ip_rotator
		self.headers_list = RequestAndSaveToPickle.headers_list
		self.headers = self.headers_list[headers_num]
	
	def __generate_unique_filename(self, url):
		''' https://www.fila.com/shoes 와 같은 url에서 
		SHA-256 해시값을 이용, url 길이와 상관 없는 고유한 파일명 반환 
		(6자리 해시값은 16^6 가지의 조합 가능) '''
		url_parts = url.split('/')
		path = '/'.join(url_parts[3:])

		unique_identifier = f"{self.SITE_OFFICIAL_PASCAL}_{path}"
		hash_object = hashlib.sha256(unique_identifier.encode())
		hash_hex = hash_object.hexdigest()[:6] # 처음 6자리만 사용
		
		return f"res_{self.SITE_OFFICIAL_PASCAL}_{hash_hex}.pickle"

	# 1. HTTP 응답을 파일에 저장 및 불러오기
	## 1-1. HTTP 응답 객체 자체 저장
	def save_webpage_response(self, url):
		# 응답 객체를 저장할 SITE_PAGES_DIR 디렉터리가 존재하지 않으면 생성  
		if not os.path.exists(self.SITE_PAGES_DIR):
			os.makedirs(self.SITE_PAGES_DIR)
		# HTTP 요청: 200이 아닌 응답은 __get_webpage_response()에서 중단됨
		response = self.__get_webpage_response(url)
		filename = self.__generate_unique_filename(url)
		file_path = os.path.join(self.SITE_PAGES_DIR, filename)
		with open(file_path, 'wb') as f:
			pickle.dump(response, f)
			print('Successfully saved HTTP response----------')
		return response
	## 1-2. 저장된 HTTP 응답 pickle 파일을 객체로 불러오기 
	def load_webpage_response(self, url):
		try:
			filename = self.__generate_unique_filename(url)
			print(filename)
			file_path = os.path.join(self.SITE_PAGES_DIR, filename)				
			with open(file_path, 'rb') as f:
				response = pickle.load(f)
				if (response.status_code == 200):
					print('Successfully loaded HTTP response----------')
			message = make_response_to_log_message(response, response.url)
			iplogger.info(message)
			return response
		except FileNotFoundError:
			return self.save_webpage_response(url)
	# 2. HTTP 응답 사용하고 버리기
	## 2-1. IP rotator(IP 우회)를 통한 요청:
	def __get_webpage_response(self, url):
		print('------------ ! HTTP 요청함 ----------------')
		for n in range(4):
			try:
				if self.ip_rotator is not None and self.ip_rotator.is_opened:
					response = self.ip_rotator.session.get(url, headers=self.headers)
				else: 
					response = requests.get(url, headers=self.headers)
				response.raise_for_status()
				print("Request was successful!")
				return response
			except requests.exceptions.RequestException as e:
				message = make_response_to_log_message(response, e)
				iplogger.error(message)
				print(e)
				print()
				if n == 3:
					print("3번 요청 실패, 프로그램을 종료합니다")
					raise
				print(f"에러 발생: HTTP 재요청중({n+1}/3) ---------------")
				time.sleep(n*1.5)
				continue
			except:
				print(f'알 수 없는 에러 발생: {e.response.status_code}')
				raise
			finally:
				print(f'"response code": "{response.status_code} {response.reason}"')
				print(f'"request object[headers]": "{response.request.headers}"')
				print(f'"response headers": "{response.headers}"')
				# 응답 데이터 크기를 확인합니다.
				response_size = len(response.content)
				print(f'"Response size": "{response_size} bytes"')
				print()
	

class Requestor():
	'''HTTP 응답을 반환
	RequestAndSaveToPickle()과 같은 타입
	__init__(site_official, headers_num=0, ip_rotator=None)
	request(url): 연결된 IP Rotator에게 url로 HTTP 요청 후 응답을 반환
		(IP Rotator가 열려있지 않은 경우, IP 우회 없이 요청 후 응답 반환)
	download_image(url, target_directory): 주어진 이미지 url의 파일명으로 
		타겟 디렉터리에 다운받은 이미지를 저장
	'''
	## (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
	# 사용자의 웹 브라우저의 식별자
	my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
	headers1 = {
		'User-Agent': my_user_agents[0],
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 모질라 파이어폭스 + 맥OS 사용자
	headers2 = {
		'User-Agent': my_user_agents[1],
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 사파리 + 아이폰 사용자
	headers3 = {
		'User-Agent': my_user_agents[2],
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	## 랜덤 사용자
	headers0 = {
		'User-Agent': random.choice(my_user_agents),
		'Accept': accept,
		'Accept-Language': accept_language,
		'DNT': dnt,  # Do Not Track Request Header
		'Connection': connection,
		'Upgrade-Insecure-Requests': upgrade_insecure_requests
	}
	headers_list = [headers0, headers1, headers2, headers3]

	def __init__(self, site_official, headers_num=0, ip_rotator=None) -> None:
		self.SITE_OFFICIAL_PASCAL = ''.join(site_official.split(' '))
		self.headers = Requestor.headers_list[headers_num]
		self.ip_rotator = ip_rotator

	def request(self, url):
		without_ip = False
		print('-------------- ! HTTP 요청함 -----------------')
		for n in range(4):
			try:
				if self.ip_rotator is not None and self.ip_rotator.is_opened and not without_ip:
					response = self.ip_rotator.request(url, self.headers)
				else: 
					response = requests.get(url, headers=self.headers)
				response.raise_for_status()
				print("Request was successful!")
				message = make_response_to_log_message(response, response.url)
				iplogger.info(message)
				return response
			except requests.exceptions.RequestException as e:
				message = make_response_to_log_message(response, e)
				iplogger.error(message)
				print(e)
				print()
				if n == 2:
					# print("3번 요청 실패, 프로그램을 종료합니다")
					# raise
					print("3번 요청 실패, IP 우회 없이 접근을 시도합니다")
					without_ip = True
					continue
				if n == 3:
					print("HTTP 요청 실패. 프로그램을 종료합니다")
					raise
				print(f"에러 발생: HTTP 재요청중({n+2}/3) ---------------")
				time.sleep(n*1.7)
				continue
			except Exception as e:
				print(f'알 수 없는 에러 발생: {e}')
				raise
			finally:
				response_size = len(response.content)
				# print(f'응답 데이터 크기: {response_size} bytes')
				# print()
		
	def download_image(self, url, target_directory) -> str: # TODO: IP 우회버전 추가하기
		'''target_directory에 url 이미지를 파일로 다운 받아 저장 후
		저장한 파일명 반환'''
		try: 
			response = requests.get(url, stream=True)
			response.raise_for_status()
			file_name = os.path.basename(url)  # URL에서 파일 이름 추출

			if '?' in file_name:
				file_name = file_name.split('?')[0]
			file_name, ext = os.path.splitext(file_name) # img.jpg -> img, .jpg
			if ext != '': # 이미 확장자가 붙어있으면 그 확장자로
				file_name = file_name + ' (1)'
				# 이미지 파일명에 숫자를 덧붙입니다.
				i = 2
				while os.path.exists(os.path.join(target_directory, file_name + ext)):
					file_name = file_name.replace(f'({i - 1})', f'({i})')
					i += 1
				new_file_name = f'{file_name}{ext}'
				# print(f'이미지 자체 확장자를 이용한 새 파일명: ', {new_file_name})
			else:
				import imghdr
				extension = imghdr.what(None, response.content)
				if extension is not None: # 자체 확장자가 없고 이미지에서 확장자를 추측 가능한 경우
					file_name = file_name + ' (1)'
					# 이미지 파일명에 숫자를 덧붙입니다.
					i = 2
					while os.path.exists(os.path.join(target_directory, f'{file_name}.{extension}')):
						file_name = file_name.replace(f'({i - 1})', f'({i})')
						i += 1
					new_file_name = f'{file_name}.{extension}'
					# print(f'추측 확장자를 이용한 새 파일명: ', {new_file_name})
			file_path = os.path.join(target_directory, new_file_name)
			
			with open(file_path, 'wb') as file:
				for chunk in response.iter_content(chunk_size=128):
					file.write(chunk)
			
			print(f"이미지가 성공적으로 다운로드되었습니다. 파일 경로: {file_path}")
			return new_file_name
		except Exception as e:
			# logger.error(e)
			print(f"이미지 다운로드에 실패했습니다. HTTP 상태 코드: {response.status_code}")
			return ''

'''
Requestor를 테스트하기 위한 테스트 클래스 정의
'''
import pytest 

# 테스트 데이터 정의

class TestRequestor(): # 통과 (실행시마다 ()내의 숫자 올리면 통과됨)
	def test_download_image_without_ip_rotator_pass(self):
		requestor = Requestor('Zappos')
		img_url1 = 'https://images.vans.com/is/image/Vans/VN000CS0_BKA_HERO?wid=1600&hei=1984&fmt=jpeg&qlt=90&resMode=sharp2&op_usm=0.9,1.7,8,0'
		img_url2 = 'https://m.media-amazon.com/images/I/61RMh62td1L._AC_SR800,1500_.jpg'
		target_directory = os.path.join(ROOT_DIR, 'test')
		img_file_name = requestor.download_image(img_url2, target_directory)
		print(img_file_name)
		assert img_file_name == '61RMh62td1L._AC_SR800,1500_ (3).jpg'


from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pprint import pprint
class SeleniorAndSaveToHtml:
	'''
	Requests로 http 응답 객체를 가져오는 대신
	Selenium으로 url에 접속하여 '타겟 태그 요소'가 
	그려질 때까지 기다렸다 html을 가져온 후
	.html파일로 저장 및 불러오는 클래스.
	load_webpage_html(url, *args): args의 마지막 요소를 
		타겟 요소로 하여 '그려지길' 기다린 url 페이지의 html 문자열을 파일로부터 반환
		(파일이 없으면 셀레니움으로 추출해서 저장 후 반환)
	'''
	def __init__(self, site_official) -> None:
		'''셀레니움 요청 헤더 등 초기 설정'''
		# (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
		# 사용자의 웹 브라우저의 식별자
		my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
				'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1',  
				'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']
		chrome_options = webdriver.ChromeOptions()		
		chrome_options.add_argument(f"--user-agent={my_user_agents[3]}")
		# chrome_options.add_argument(f"--accept-lang={headers['Accept-Language']}")
		# chrome_options.add_argument("--headless")

		self.SITE_OFFICIAL_PASCAL = ''.join(site_official.split(' '))
		self.SITE_PAGES_DIR = os.path.join(ROOT_DIR, 'tests', 'page_samples', self.SITE_OFFICIAL_PASCAL+'_page_samples')
		self.chrome_options = chrome_options
		self.driver = None
	
	def load_webpage_html(self, url, *args):
		try:
			filename = self.__generate_unique_filename(url)
			file_path = os.path.join(self.SITE_PAGES_DIR, filename)
			with open(file_path, 'r', encoding='utf-8') as f:
				html = f.read()
				if len(html) < 100:
					raise FileNotFoundError
				print('Successfully loaded from HTML file-----------')
			return html
		except FileNotFoundError:
			return self.save_webpage_html(url, *args)
	
	def save_webpage_html(self, url, *args):
		# html 소스를 저장할 SITE_PAGES_DIR 디렉터리가 존재하지 않으면 생성  
		if not os.path.exists(self.SITE_PAGES_DIR):
			os.makedirs(self.SITE_PAGES_DIR)
		# html 추출: 
		html = self.__get_html_after_waiting_target_selector(url, *args)
		filename = self.__generate_unique_filename(url)
		file_path = os.path.join(self.SITE_PAGES_DIR, filename)
		with open(file_path, 'w', encoding='utf-8') as f:
			f.write(html)
			print('Successfully saved HTML file----------')
		return html
		
	def __generate_unique_filename(self, url):
		''' https://www.fila.com/shoes 와 같은 url에서 
		SHA-256 해시값을 이용, url 길이와 상관 없는 고유한 파일명 반환 
		(6자리 해시값은 16^6 가지의 조합 가능) '''
		url_parts = url.split('/')
		path = '/'.join(url_parts[3:])

		unique_identifier = f"{self.SITE_OFFICIAL_PASCAL}_{path}"
		hash_object = hashlib.sha256(unique_identifier.encode())
		hash_hex = hash_object.hexdigest()[:6] # 처음 6자리만 사용

		return f"res_{self.SITE_OFFICIAL_PASCAL}_{hash_hex}.html"
	
	def __get_html_after_waiting_target_selector(self, url, *args) -> str: 
		'''
		url을 받아 셀레니움으로 해당 페이지로 접속,
		args로 주어진 CSS selectors를 차례로 기다리고 클릭하기를 반복 후
		마지막 arg의 CSS selector가 '나타난' 시점의 html 문자열을 반환
		(args의 마지막 요소가 즉 '타겟 태그 요소')
		'''
		if self.driver is None:
			self.driver = webdriver.Chrome(self.chrome_options)
		self.driver.get(url)
		try:
			for i, selector in enumerate(args):
				print(f'{i}, {selector}: ')
				if i < len(args) - 1:
					element = WebDriverWait(self.driver, 60).until(
						EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
					)
					element.click()
					print(f'{selector} 클릭함')
				else:
					element = WebDriverWait(self.driver, 60).until(
						EC.presence_of_element_located((By.CSS_SELECTOR, selector))
					)
					print(f'{selector} 나타남')
					html = self.driver.page_source
					# print(html[:100])
					return html
		# except TimeoutException as e:
		# 	print('클릭 요소 기다리다 시간 초과')
		# 	print(e)
		except Exception as e:
			# logger.error(e)
			# print('예상치 못한 에러 발생')
			print(e)
	
	def quit_driver(self):
		''' 현재 드라이버를 종료함
		(호출 이후 다시 브라우저를 구동하려면 새 Selenior 객체 만들것)'''
		self.driver.quit()
	def open_url_as_new_tab(self, url):
		''' (임시)현재 브라우저의 새 탭으로 url을 열고 방금 만든 탭으로 이동 '''
		self.driver.execute_script(f'window.open("{url}");')		
		self.driver.switch_to.window(self.driver.window_handles[-1])

class Selenior():
	'''
	Requests로 http 응답 객체를 가져오는 대신
	Selenium으로 url에 접속하여 '타겟 태그 요소'가 
	그려질 때까지 기다렸다 html을 가져오는 클래스.
	get_html_after_waiting_target_selector(url, *args): args의 마지막 요소를 
		타겟 요소로 하여 '그려지길' 기다린 후 해당 url 페이지의 html 문자열을 반환
	quit_driver(): 현재 드라이버(브라우저)를 종료
	(임시)open_url_as_new_tab(url): 현재 브라우저의 새 탭으로 url을 열고 방금 
		만든 탭으로 이동
	'''
	def __init__(self) -> None:
		'''셀레니움 요청 헤더 등 초기 설정'''
		# (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
		# 사용자의 웹 브라우저의 식별자
		my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
				'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
				'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1',  
				'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36']
		chrome_options = webdriver.ChromeOptions()		
		chrome_options.add_argument(f"--user-agent={my_user_agents[3]}")
		chrome_options.add_argument("--headless")
		chrome_options.add_argument("--log-level=3") # 배포용은 로그 최대한 없앰 (0=DEBUG, 1=INFO, 2=WARNING, 3=ERROR 이상)
		self.chrome_options = chrome_options

		self.driver = None
	
	def get_html_after_waiting_target_selector(self, url, *args) -> str: 
		'''
		url을 받아 셀레니움으로 해당 페이지로 접속,
		args로 주어진 CSS selectors를 차례로 기다리고 클릭하기를 반복 후
		마지막 arg의 CSS selector가 '나타난' 시점의 html 문자열을 반환
		(args의 마지막 요소가 즉 '타겟 태그 요소')
		=> 브라우저 구동 중 에러 발생 시 현재 페이지 그대로 html 반환을 시도,
		거기서도 에러가 나면 빈 문자열('')을 반환함
		'''
		if self.driver is None:
			self.driver = webdriver.Chrome(self.chrome_options)
		self.driver.get(url)
		try:
			for i, selector in enumerate(args):
				# print(f'{i}, {selector}: ')
				if i < len(args) - 1:
					element = WebDriverWait(self.driver, 15).until(
						EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
					)
					element.click()
					# print(f'{selector} 클릭함')
				else:
					element = WebDriverWait(self.driver, 20).until(
						EC.presence_of_element_located((By.CSS_SELECTOR, selector))
					)
					# print(f'{selector} 나타남')
					html = self.driver.page_source
					# print(html[:100])
					return html
		except TimeoutException as e:
			logger.warning('브라우저에서 타겟 데이터를 발견할 수 없어 불완전한 상태로 추출을 진행합니다')
			return self.driver.page_source
		except Exception as e:
			logger.error(f'{e}: 예상치 못한 에러 발생, 불완전한 상태로 추출을 진행합니다')
			try:
				return self.driver.page_source
			except:
				return ''
	
	def quit_driver(self):
		''' 현재 드라이버를 종료함
		(호출 이후 다시 브라우저를 구동하려면 새 Selenior 객체 만들것)'''
		self.driver.quit()
	def open_url_as_new_tab(self, url):
		''' (임시)현재 브라우저의 새 탭으로 url을 열고 방금 만든 탭으로 이동 '''
		self.driver.execute_script(f'window.open("{url}");')		
		self.driver.switch_to.window(self.driver.window_handles[-1])


'''
cookie:
geo_ip=125.139.166.8; adidas_country=us; geo_country=KR; geo_state=; onesite_country=US; gl-feat-enable=CHECKOUT_PAGES_ENABLED; geo_coordinates=lat=37.57, long=127.00; badab=false; sbsd=sYZJHCN52xAULFpCH5PoYok43BiYhWBv4L+2NZq5G/Y4B4Qq2kv3fq7LTyMw8rnn90bRrwKxBMVQ84eNWjgrU0YpcpLocdVynFkEsnh2+FjA1vtp7TXr9lqpYlpyXinYZVkqhB6OEVR5uksrKOkDPzA==; akacd_phased_PDP=3885274290~rv=32~id=60bd7896e7e75a1540876ee37a92303d; ak_bmsc=BE5720EA58CA542947F61C9C9A227AA0~000000000000000000000000000000~YAAQr3XTF0qY2mSNAQAAsOYXohZy8hapTdxmGdgNXh2VWwD/j07k+D+saYg7lsawhofLoZEa0Nh+B26rofyzfwNKCdYcs8suNjJWP9tmPVS6KMj4DgShx0+btlo6jVYP8dHaKsC/uV42bMjwoU8DGnrn2zjsM6b/zVexH9wTLKnhFptnPAodl33Y9rxVGGp5ITqpg1wFivSI3qh9BInDw3a/JADvA1hIJwlqAho25Esw6fbPv/QBhFc/Fwwo+YwejM8Yt7riUKVeYtRtu7zjPqhAvpg6pbHK7x2Qs6Lc9mdU3NvSTP1jhv4P9yEOGONvGbPzHLWpgfR6XIGUFnEckFxcOFv8tuwwxQ6IrtKwTydfylZOMyvldEJxvrUcot+eXnDUnSNkM+gm; bm_sz=3BE44BCBE40075CC449831CBBE531741~YAAQr3XTF0uY2mSNAQAAsOYXohb8HuEnJhYjCB74A3ludd1XSgAdFCeH3n3I0CIGvFpxUJKjiu23jzWNuknimF4dPycG6FJTfn0UyB80GSGwzasCISDLWwBRL4loAmlH+VfzITv5mQEyOB78f9CiqGYT/PDaC8XZFOuDFOt+XBTDyV4oGqUjTSHIUaKUG/8hu1PrBDZt1zumO7SYkpz8sJXMxf9VmPiAnFGOGBeloXSodOCGnENIXH349Be7kEJshYm77yxuX36K7W5uDyo89vDM3q9F6ZN6p6uYFJTpp/TOdlFqUKitzlF6icPdrF0JFwZ7ZLh9qdNwDpdnMU9r0IZkT3m3aHYBL/0n7Vywfgn3Zaz+R90leUevoQ6/09YCqd/aCBm5P2Y8ytMgF7+0jS7WzbLuW8l8R9beRvFswao11/uBq4RAL7IGeWdXQ/eCjvLmXLPSl5fFifBG6tMOY2sk3VOiAsf2Z8E=~3291201~4604994; akacd_Phased_www_adidas_com_Generic=3885274291~rv=87~id=f9fa6bfdcb3b3ee79cd7c01289e6d9bd; _abck=6F4604A167F2FF8A053C50645E3219ED~-1~YAAQr3XTFxaa2mSNAQAASPoXogukK97VFaEgzHnLmXZd97gGiNkDBJJPzozF5/YdLnGyg42FkHqVTNWXp2jNTmjuXPLmlrX4WVQ/llTYuAgFG3dex3JiRdx7Y9Ku9dczr9JWiU6uqHt63BGUC7opGiNpB7qkjvDANtAHW/HuKvgpSqyVyTlht9C/1IgBWAzNh3xzeTUfgDvkyLUmY4/IV/dsDokfYU1Ki5uOsPHjWtlIR9ZiI2rIvVsPR/0AeyBukxQuMKbwqmPJqNtFb2Rta0TPAXzovGz5WF88c+dxaIL+WXUbsUgmqUSiqeH6s9C/0OxxgA2fXit+xsn12Pp1rRVzfGB3qDXRQ5pEX1MG7nwLrYpZY0z6gcVT7NPckzuerIeqrN3TnVJjAh4efoSxV6DTGxD0n1s4zL7BPjku94hXKyWwf7PmKjrcEtYdBFdAue67cc3uJYxuvRXoDVWRsuSqQbMoHAAz00BR5ac+8Q==~-1~-1~1707825096; UserSignUpAndSave=1; persistentBasketCount=0; userBasketCount=0; newsletterShownOnVisit=false
Glassversion:
e009f07
Referer:
https://www.adidas.com/us/predator-24-league-turf-cleats/IG5442.html
Sec-Ch-Ua:
"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"
'''

from bs4 import BeautifulSoup as bs
# 0 클릭 + 타겟 요소 기다림 콤보 테스트를 위한 데이터
urls_no_click = [
	"https://www.adidas.com/us/lite-racer-adapt-5.0/HQ3560.html?pr=product2_rr&slot=4&rec=mt",
	"https://www.adidas.com/us/predator-24-league-turf-cleats/IG5442.html",
	"https://www.adidas.com/us/ae-1-with-love-basketball-shoes-kids/IF1869.html",
]
args_no_click = [
	["button.size___2lbev"],
	["button.size___2lbev"],
	["button.size___2lbev"],
]
total_tag_num_no_click = [
	1,
	1,
	1,
]
ids_no_click = [
	'아디다스1',
	'아디다스2',
	'아디다스3',
]
# 1 클릭 + 타겟 요소 기다림 콤보 테스트를 위한 데이터
urls_two_click = [
	"https://www.lacoste.com/us/lacoste/women/clothing/shorts-skirts/women-s-sport-ultra-dry-golf-skirt/JF9433-51.html?color=NHI",
	"https://www.lacoste.com/us/lacoste/women/shoes/sneakers/women-s-g-elite-golf-shoes/45SFA0010.html?color=03A",
]
args_two_click = [
	["button.js-geolocation-stay.reverse-link", "button.js-pdp-select-size", "ul.grid-template-5 button"],
	["button.js-geolocation-stay.reverse-link", "button.js-pdp-select-size", "ul.grid-template-5 button"],
]
total_tag_num_two_click = [
	1,
	1,
]
ids_two_click = [
	'라코스테1',
	'라코스테2',
]
# 2 클릭 + 타겟 요소 기다림 콤보 테스트를 위한 데이터
class TestSelenior():
	@pytest.mark.parametrize('url,args,total_tag_num', zip(urls_no_click, args_no_click, total_tag_num_no_click), ids=ids_no_click)
	def test_wait_one_selector_pass(self, url, args, total_tag_num): # ex) 아디다스 
		''' 
		0 클릭 후 타겟 요소 기다림 콤보 테스트. 
		html을 가져온 후에는 args의 마지막 '기다림' selector 그대로 태그를
		추출하여 품절 포함 전체 사이즈 태그 개수와 같은지를 비교함
		''' 
		selenior = Selenior()
		html = selenior.get_html_after_waiting_target_selector(url, *args)
		soup = bs(html, "html.parser")
		# buttons = soup.select('button.size___2lbev:not([class*="unavailable"])')
		# instock_sizes = [button.text.strip() for button in buttons]
		# pprint(sorted(instock_sizes))
		buttons = soup.select(args[-1])
		assert len(buttons) == total_tag_num

	@pytest.mark.parametrize('url,args,total_tag_num', zip(urls_two_click, args_two_click, total_tag_num_two_click), ids=ids_two_click)
	def test_two_clicks_and_wait_pass(self, url, args, total_tag_num): # ex) 라코스테
		''' 
		2 클릭 후 타겟 요소 기다림 콤보 테스트. 
		html을 가져온 후에는 args의 마지막 '기다림' selector 그대로 태그를
		추출하여 품절 포함 전체 사이즈 태그 개수와 같은지를 비교함
		''' 
		selenior = Selenior()
		html = selenior.get_html_after_waiting_target_selector(url, *args)
		soup = bs(html, "html.parser")
		# buttons = soup.select('ul.grid-template-5 button:not([class*="is-disabled"])')
		# instock_sizes = sorted([button.text.strip() for button in buttons], key=float)
		# print(len(buttons))
		# print(instock_sizes)
		buttons = soup.select(args[-1])
		assert len(buttons) == total_tag_num
