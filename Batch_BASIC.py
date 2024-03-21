''' 
현재 가능한 사이트: 반스(Vans) 신발, 자포스, 라코스테, 아디다스
추가 예정: 아식스
'''
# ==========================================
'''
pip3.9 install requests
pip3.9 install gspread
pip3.9 install deep-translator
pip3.9 install beautifulsoup4
pip3.9 install requests-ip-rotator
pip3.9 install python-dotenv
(dev) pip3.9 install pyinstaller
pip3.9 install pytest
pip3.9 install selenium
pip3.9 install pytest-timeout
'''
# ==========================================
#-*-coding: utf-8-*-
from bs4 import BeautifulSoup as bs
import requests
import gspread
import random
import os
from requests_ip_rotator import ApiGateway, DEFAULT_REGIONS, EXTRA_REGIONS, ALL_REGIONS
from dotenv import load_dotenv
import logging
from pprint import pprint
import pytest

from site_class import SiteClass
from request_classes import Requestor, Selenior
from logging_config import set_logging
from namer import Namer

# .env 파일에서 환경 변수 불러와 os에 저장
load_dotenv()

# 환경변수 및 전역변수 설정
ROOT_DIR = os.path.dirname(os.path.realpath(__file__))
EXTRA_REGIONS_ONLY = [region for region in EXTRA_REGIONS if region not in DEFAULT_REGIONS]
EXTRA_EXTRA_REGIONS_ONLY = [region for region in ALL_REGIONS if region not in EXTRA_REGIONS]

class IpRotator():
	'''
	IP 우회 게이트웨이를 열고 닫을 수 있는 
	__init__()
	open_gateway(target_site_name)
	request(url)
	shutdown_gateway()
	'''
	def __init__(self) -> None:
		ACCESS_KEY = os.getenv('AWS_ACCESS_KEY_ID')
		SECRET_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
		self.AWS_access_key_id = ACCESS_KEY
		self.AWS_access_key_secret = SECRET_KEY
		self.is_opened = False
		self.endpoints = []
	
	def open_gateway(self, target_site_name):
		'''target_site_name: 띄어쓰기 있는 (site_official 그대로 가져온)정제된 영문명'''
		# 이미 연결된 endpoint 10개가 있으면 아무 일도 하지 않음
		if self.is_opened:
			print(f'이미 연결된 host 존재: {self.target_host}')
			return 
		# target_host = self.site_name_host_table.get(target_site_name)
		self.target_host = Namer.get_host_from_site_name(target_site_name)
		if self.target_host is None: # 매칭되는 주소를 찾지 못했으면 주어진 값 그대로 url로 사용('https://api64.ipify.org'같은 유효한 도메인 주소가 주어졌을 것으로 가정)
			self.target_host = target_site_name

		fail = 0
		while fail <= 3:
			try:
				if 'http' not in self.target_host:
					raise Exception('유효한 http 프로토콜 호스트가 아닙니다')
				# AWS에서 게이트웨이 객체를 생성 및 host에 연결
				self.gateway = ApiGateway(self.target_host, 
									# regions= EXTRA_REGIONS_ONLY,
									access_key_id=self.AWS_access_key_id, 
									access_key_secret=self.AWS_access_key_secret)
				self.endpoints = self.gateway.start()
				self.is_opened = True
				# 세션에 게이트웨이 할당
				self.session = requests.Session()
				self.session.mount(self.target_host, self.gateway)
				break
			except Exception as e:
				fail += 1
				print(e)
				print(f'IP 우회 게이트웨이 연결에 실패하였습니다({fail}/3)')
				# error_logger.error('IP 우회 게이트웨이 연결 실패')

				if fail == 3:
					print(f'IP를 우회하지 않고 진행합니다')
					return
				
				sample_url = input('추출하고자 하는 사이트의 샘플 페이지 url을 입력해주세요("http"포함): ')
				if 'http' in sample_url:
					self.target_host = '/'.join(sample_url.split('/')[:3])
					# self.target_host = sample_url.split('/')[2] # 스키마 없는 호스트로 게이트 열어도 잘 동작은 함
				else:
					# print('해당 url로 호스트 추출에 실패했습니다.')
					# erorr_logger.error('샘플 url 받아 호스트 추출 중 에러 발생, 실패')
					pass
	
	def request(self, url, headers): #TODO: 예외 처리 필요?
		if not self.is_opened:
			print('게이트웨이를 먼저 오픈하세요')
			return {}
		return self.session.get(url, headers=headers)

	def shutdown_gateway(self):
		if self.is_opened:
			self.gateway.shutdown()
			self.endpoints = []
			self.is_opened = False


class GoogleSheeter():
	''' 구글 시트 연락자
	__init__()
	set_document_and_worksheet(sheet_file_name='대량등록 시트 테스트')
	get_urls(start_cell, batch_size)
	add_rows(target_start_row, data)
	'''
	def __init__(self):
		self.sheet_file_name = ''
		self.g_API_file_path = os.path.join(ROOT_DIR, 'python-crawling-gspread-145332f402e3.json')
		# 구글 시트 연동 
		self.google_client = gspread.service_account(filename=self.g_API_file_path)
		self.sh = '' # 작업할 문서
		self.worksheet = '' # 작업할 시트

	def set_document_and_worksheet(self, sheet_file_name='대량등록 시트 테스트'):
		self.sheet_file_name = sheet_file_name
		while True:
			try:
				self.sh = self.google_client.open(self.sheet_file_name)
				self.__set_worksheet(0)
				break
			except:
				self.sheet_file_name = input('존재하지 않는 스프레드시트입니다. 다시 입력해주세요: ')
	def __set_worksheet(self, sheet_index=0):
		self.worksheet = self.sh.get_worksheet(sheet_index)

	def get_urls(self, start_cell, batch_size):
		''' start_cell로부터 아래로 batch_size만큼 셀을 읽어들여
		빈 칸(빈 문자열)이 아니고 http로 시작하는 유효한 url이면 반환 
		'''
		end_cell = f'S{int(start_cell[1:]) + batch_size - 1}'
		cells = self.worksheet.range(f'{start_cell}:{end_cell}')
		valid_urls = [cell.value for cell in cells 
				if cell.value and self.__is_url(cell.value)]
		return valid_urls
	def __is_url(self, text):
		''' 문자열이 유효한 url 형식인지 검사
		('http'로 시작하는지) '''
		return 'http' in text
	
	def add_rows(self, target_start_row, data):
		'''[[행1 데이터], [행2 데이터], ...] 형태의 이차원 데이터 리스트를 받아 
		target_start_row 행을 아래로 밀어내고 데이터 수만큼 행을 현재 시트에 삽입'''
		self.worksheet.insert_rows(data, target_start_row)
		print(f'\n{len(data)}줄 업로드 완료')



ip_rotator = ''
endpoints = []
def test_ip_rotator_init():
	global ip_rotator
	ip_rotator = IpRotator()
	assert ip_rotator.is_opened == False
@pytest.mark.parametrize("site_name", [("Vans")])
def test_existing_ip_rotator_open_gateway(site_name):
	global ip_rotator
	ip_rotator.open_gateway(site_name)
	global endpoints
	endpoints = ip_rotator.endpoints
	assert ip_rotator.is_opened == True
@pytest.mark.parametrize("site_name,fake_inputs", [("vans",['https://www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj'])])
def test_ip_rotator_open_gateway_success_at_2nd(monkeypatch, site_name, fake_inputs):
	ip_rotator = IpRotator()
	fake_inputs = iter(fake_inputs)
	# fake_inputs = iter(['https://www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	ip_rotator.open_gateway(site_name)
	assert ip_rotator.is_opened == True
@pytest.mark.parametrize("site_name,fake_inputs", [("반스",[])])
def test_ip_rotator_open_gateway_success_at_3rd(monkeypatch, site_name, fake_inputs):
	ip_rotator = IpRotator()
	fake_inputs = iter(['www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj','https://www.vans.com'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	ip_rotator.open_gateway(site_name)
	assert ip_rotator.is_opened == True
@pytest.mark.parametrize("site_name,fake_inputs", [("반스",[])])
def test_ip_rotator_open_gateway_fail(monkeypatch, site_name, fake_inputs):
	ip_rotator = IpRotator()
	fake_inputs = iter(['www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj','www.vans.com'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	ip_rotator.open_gateway(site_name)
	ip_rotator.shutdown_gateway()
	assert ip_rotator.is_opened == True
	
# @pytest.mark.parametrize("site_name", [("Vans")]) # 실험중
# def test_new_ip_rotator_with_existing_host_says_already_opened(site_name): #TODO: 내부적으로 '이미 존재하는 호스트 연결(endpoints)들을 외부로 끌어낼 수 있는지 코드 살펴보기. 즉, '해당 호스트로 이미 열린 endpoints가 있는지 확인하는 메서드' 가능하면 구현하기 
# 	global endpoints
# 	ip_rotator2 = IpRotator()
# 	assert ip_rotator.is_opened == True
# 	ip_rotator.shutdown_gateway()
# 	assert ip_rotator.is_opened == False
# @pytest.mark.parametrize("site_name", [("Vans")])
# def test_ip_rotator_shutdown_gateway_success(site_name):
# 	global ip_rotator
# 	assert ip_rotator.is_opened == True
# 	ip_rotator.shutdown_gateway()
# 	assert ip_rotator.is_opened == False
def test_existing_ip_rotator_shutdown_gateway_twice():
	global ip_rotator
	# global endpoints
	print('닫기 전: ', ip_rotator.endpoints)
	ip_rotator.shutdown_gateway()
	print('1번 닫기: ', ip_rotator.endpoints)
	print(ip_rotator.is_opened)
	# assert ip_rotator.is_opened == False
	ip_rotator.shutdown_gateway()
	print('2번 닫기: ', ip_rotator.endpoints)
	print(ip_rotator.is_opened)
	assert ip_rotator.is_opened == ''
@pytest.mark.parametrize("site_name", [("Vans")])
def test_ip_rotator_open_and_close_gateway(site_name):
	ip_rotator = IpRotator()
	ip_rotator.open_gateway(site_name)
	print(ip_rotator.is_opened)
	pprint(ip_rotator.endpoints)
	assert ip_rotator.is_opened == True
	ip_rotator.shutdown_gateway()
	print(ip_rotator.is_opened)
	pprint(ip_rotator.endpoints)
	assert ip_rotator.is_opened == True
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
@pytest.mark.parametrize("site_name,headers", [("vans",headers_list[0])])
def test_can_ip_rotator_send_request_without_http_protocol(monkeypatch, site_name, headers):
	ip_rotator = IpRotator()
	fake_inputs = iter(['https://www.vans.com/'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	ip_rotator.open_gateway(site_name)
	response = ip_rotator.request('https://www.vans.com/en-us/shoes-c00081/old-skool-pig-suede-shoe-pvn0007nt5qj', headers)
	print(len(response.content))
	ip_rotator.shutdown_gateway()
	assert response.status_code != 200


sc = ''
ip_rotator = ''
SITE_OFFICIAL = ''
requestor = ''
google_sheeter = ''
URLS = []

def test_main(monkeypatch):
	# 인풋 사이트명, 구글 문서명, 배치 사이즈, url행, 쓸 행, 사이즈 타입, 이어서 혹은 그만
	# fake_inputs = iter(['라코스테', '대량등록 시트 테스트', '2', '241', '255', '4', 'q'])
	# 변경 후: 인풋 사이트명, 사이즈 타입, 구글 문서명, 배치 사이즈, url행, 쓸 행, 이어서 혹은 그만
	fake_inputs = iter(['asics', '5', '대량등록 시트 테스트', '1', '311', '327', 'q'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	main()
	assert False

def get_size_type_input(is_size_type_deducible, size_type=None):
	''' 최대 5회 재입력 요구 후 타입 4(변환하지 않음)로 임의 지정함 '''
	tries = 0
	while size_type is None:
		if tries >= 5:
			print(f'-----\n입력 횟수({tries}회)를 초과하여 사이즈 옵션을 4(변환하지 않음으)로 임의 지정합니다\n-----')
			return 4
		tries += 1
		if is_size_type_deducible: # 사이즈 타입 추론 가능: 1,2,3,4,5번 옵션 제공
			possible_size_type = ['1', '2', '3', '4', '5']
			user_input_size_type = input('\n사이즈 타입을 설정해주세요(1.남성 신발 2.여성 신발 3.아동 신발 4.한국 사이즈로 변환하지 않음 5.남성/여성/아동 사이즈 자동 변환): ')
		else: # 1,2,3,4번 옵션만 제공
			possible_size_type = ['1', '2', '3', '4']
			user_input_size_type = input('\n사이즈 타입을 설정해주세요(1.남성 신발 2.여성 신발 3.아동 신발 4.한국 사이즈로 변환하지 않음): ')
		#TODO: "이 사이트는 사이즈 타입 추론이 불가능한 사이트입니다" 안내해야 해나?
		
		if user_input_size_type not in possible_size_type:
			print('유효한 옵션 번호가 아닙니다')
			continue
		else:
			size_type = int(user_input_size_type)
	return size_type
def get_batch_size_input(batch_size):
	''' 주어진 batch_size가 None이면 사용자에게 배치 사이즈 입력을 요구하여 숫자로 변환, None이 아니면 그대로 반환.
	사용자로부터 입력받은 값이 유효한 값(숫자형 문자열)이 아닌 경우 최대 5회 재입력 요구 후 2로 임의 지정 '''
	tries = 0
	while batch_size is None:
		if tries >= 5:
			print(f'-----\n입력 횟수({tries}회)를 초과하여 배치 사이즈를 2로 임의 지정합니다\n-----')
			return 2
		tries += 1
		user_input_batch_size = input('\n한 번에 읽고 작업할 url 개수(배치 사이즈)를 입력해주세요: ')
		if not user_input_batch_size.isdigit():
			print('입력값이 숫자가 아닙니다')
		else:
			batch_size = int(user_input_batch_size)
	return batch_size

def get_start_url_cell_input(url_cell, batch_size):
	''' 
	반환값: 'S115' | None 
	- 기존의 url_cell값을 받아 batch_size를 증가시킨 새 url_cell을 반환
	- 기존 url_cell이 None이면 새로 입력받은 결과 url_cell을 반환
	- 종료 시그널 'q'를 입력받게 되면 None을 반환
	- 재입력 횟수가 5회를 초과하면 'S1'로 임의 반환
	'''
	tries = 0
	while True: 
		if tries >= 5:
			print(f'-----\n입력 횟수({tries}회)를 초과하여 시작 행 번호를 "1"로 임의 지정합니다\n-----')
			return 'S1'
		tries += 1
		user_input_url_cell_num = input(f'\nurl이 적힌 시작 행 번호를 "10"과 같이 입력해주세요(종료를 원할 시 "q", 다음 {batch_size}개의 url로 자동 진행은 엔터): ') 
		if user_input_url_cell_num.lower() == 'q':
			print('q를 입력하여 프로그램을 종료합니다.')
			print('============= 프로그램 종료 =============')
			return None
		elif user_input_url_cell_num.strip() == '':
			if url_cell is None:
				print('처음 url 행 번호는 지정해줘야 합니다.')	
				continue
			url_cell = 'S' + str(int(url_cell[1:]) + batch_size)
			return url_cell
		elif not user_input_url_cell_num.isdigit():
			print(f'유효한 행 번호로 인식할 수 없습니다: {user_input_url_cell_num}')
			continue
		else:
			url_cell = 'S' + str(user_input_url_cell_num)
			return url_cell

def get_initial_upload_row_input(target_row, batch_size) -> int:
	''' 
	반환값: 115
	- 업로드할 행 번호 target_row 값을 사용자로부터 입력받아 반환
	- 최대 5회 재입력 요청 후 batch_size + 2행으로 임의 배정
	'''
	tries = 0
	while target_row is None:
		if tries >= 5:
			print(f'-----\n입력 횟수({tries}회)를 초과하여 업로드 행 번호를 {batch_size + 2}로 임의 지정합니다\n-----')
			return batch_size + 2
		tries += 1
		user_input_upload_row_num = input('\n업로드할 행 번호를 입력해주세요(기존 행을 아래로 밀어내고 삽입되는 방식으로 업로드됩니다): ')
		if not user_input_upload_row_num.isdigit():
			print('유효한 행 번호로 인식할 수 없습니다')
		else: 
			target_row = int(user_input_upload_row_num)
	return target_row



def get_soup_from_direct_json(sc, requestor, url):
	url_transformed = sc.replace_to_direct_json_url(url)
	response = requestor.request(url_transformed)
	soup = response.json() # TODO: if 'application/json' in response.headers['Content-Type'] 사전체크 필요할지도
	return soup
def get_soup_from_selenior(selenior, selenior_selectors, bs, url):
	html = selenior.get_html_after_waiting_target_selector(url, *selenior_selectors)
	soup = bs(html, "html.parser")
	return soup
def get_soup_from_requestor(requestor, bs, url):
	response = requestor.request(url)
	soup = bs(response.content, "html.parser")
	return soup

get_soup_scenario_type = {
	1: get_soup_from_direct_json,
	2: get_soup_from_selenior,
	3: get_soup_from_requestor,
}
def get_soup(is_direct_json_url_possible, is_selenior_needed, url, sc, requestor, selenior, selenior_selectors, bs):
	# 만약 direct_json_url로 변환이 가능하다면 이걸로 무조건 수행
	if is_direct_json_url_possible:
		# soup = get_soup_scenario_type.get(1)()
		return get_soup_from_direct_json(sc, requestor, url)
	# 그렇지 않고 셀레니어 전략이 존재하면 셀레니어로 수행
	elif is_selenior_needed:
		# html = selenior.get_html_after_waiting_target_selector(URLS_ORIGINAL[i], *selenior_selectors)
		# soup = get_soup_scenario_type.get(2)()
		return get_soup_from_selenior(selenior, selenior_selectors, bs, url)
	else: # Requestor + IpRotator 이용
		# soup = get_soup_scenario_type.get(3)()

		print('get_..._requestor 호출됨')
		return get_soup_from_requestor(requestor, bs, url)
	
	return soup


def test_batch_class(monkeypatch):
	# 인풋 사이트명, 사이즈 타입, 구글 문서명, 컬러urls 일괄 추출 여부, 배치 사이즈, url행, 쓸 행, 이어서 혹은 그만
	fake_inputs = iter(['asics', '5', '대량등록 시트 테스트', 'n', '1', '320', '366', 'q'])
	monkeypatch.setattr('builtins.input', lambda _: next(fake_inputs))
	batch = Batch()
	batch.run_batch()
	assert False

class Batch:
	''' 
	
	- run_batch()
	'''
	'''
	전체 협력 흐름을 조정하는 관리자 역할:
	"사이트명 무엇?" 1 2 3 4 4.5 
	"사이즈 타입 무엇?"
	5 "구글 문서명 무엇?" 6
	"동일 제품 다른 컬러 발견 시 자동 추출할 것?"
	-------
	"배치 사이즈 무엇?"
	"읽어들일 셀, 쓸 행 무엇?" 7 8
	9 10 11 12 13 (반복)
	14
	'''
	def __init__(self) -> None:
		self.SITE_OFFICIAL = None
		self.SITE_OFFICIAL_SNAKE = None

		# 플래그
		self.is_size_type_deducible = False
		self.is_direct_json_url_possible = False
		self.is_selenior_needed = False
		# => 기본은 단순 Requestor + Iprotator를 이용하는 요청
		
		# 외부 통신 객체
		self.selenior = None
		self.requestor = None
		self.ip_rotator = None
		self.sc = None
		self.google_sheeter = None

		# 큰 while루프 
		self.size_type = None
		self.selenior_selectors = None
		self.batch_size = None
		self.url_cell = None
		self.target_row = None
		self.URLS = []
		
		# url별 데이터 추출(작은 while 루프)
		self.rows_data = []
		self.auto_extract_color_urls = None
		self.do_not_append_color_urls = []
		self.appended_color_urls_size = 0
		self.batch_i = 0

		print('============= 프로그램 시작 =============\n')
		self.__set_site_official()
		self.__set_logging()
		self.__set_site_and_flags()
		self.__set_size_type()
		self.__set_request_strategy()
		self.__set_gs_document_and_worksheet()
		self.__open_ip_gateway()
		self.__set_auto_extract_color_urls()

	def __set_site_official(self):
		''' SiteClass 생성 및 사이트명 입력 요청, 유효성 검사 '''
		# site_input = input("사이트명을 입력해주세요(ex. 자포스, Zappos, Vans, vans): ") # => sc.get_official_site_name()으로 흡수됨
		self.sc = SiteClass()
		self.SITE_OFFICIAL = self.sc.get_official_site_name() 
			
	def __set_logging(self): # TODO: 로거를 클래스 종속으로 만들어야 할까? 
		# 로깅 셋업
		self.SITE_OFFICIAL_SNAKE = '_'.join(self.SITE_OFFICIAL.split(' '))
		set_logging(logging.INFO, self.SITE_OFFICIAL_SNAKE)
	
	def __set_site_and_flags(self):
		self.sc.set_site(self.SITE_OFFICIAL) # TODO: get_official_site_name()이 띄어쓰기 없는 이름도 받도록 해야함
		self.selenior_selectors = self.sc.get_selenium_wait_selectors() # self.sc.selenium_wait_strategy 직접 접근 막음. 훌륭함
		# is_size_type_deducible = self.sc.size_type_strategy is not None
		# direct_json_url_transformer = self.sc.direct_json_url_transform_strategy # TODO: -> 무조건 호출하는 걸로, 해당 속성을 외부에서 직접 접근하는 것을 막음. 나름 해결 완료
	
		# 위의 세가지 플래그를 속성 그대로 접근해서 일단 사용해봄
		self.is_size_type_deducible = self.sc.size_type_strategy is not None
		self.is_direct_json_url_possible = self.sc.direct_json_url_transform_strategy is not None
		self.is_selenior_needed = self.sc.selenium_wait_strategy is not None

	def __set_size_type(self):
		''' 사이즈 타입 입력받기(최초 입력 후 생략됨) '''
		self.size_type = self.__get_size_type_input(self.is_size_type_deducible, self.size_type)
	def __get_size_type_input(self, is_size_type_deducible, size_type=None):
		''' 최대 5회 재입력 요구 후 타입 4(변환하지 않음)로 임의 지정함 '''
		tries = 0
		while size_type is None:
			if tries >= 5:
				print(f'-----\n입력 횟수({tries}회)를 초과하여 사이즈 옵션을 4(변환하지 않음으)로 임의 지정합니다\n-----')
				return 4
			tries += 1
			if is_size_type_deducible: # 사이즈 타입 추론 가능: 1,2,3,4,5번 옵션 제공
				possible_size_type = ['1', '2', '3', '4', '5']
				user_input_size_type = input('\n사이즈 타입을 설정해주세요(1.남성 신발 2.여성 신발 3.아동 신발 4.한국 사이즈로 변환하지 않음 5.남성/여성/아동 사이즈 자동 변환): ')
			else: # 1,2,3,4번 옵션만 제공
				possible_size_type = ['1', '2', '3', '4']
				user_input_size_type = input('\n사이즈 타입을 설정해주세요(1.남성 신발 2.여성 신발 3.아동 신발 4.한국 사이즈로 변환하지 않음): ')
			#TODO: "이 사이트는 사이즈 타입 추론이 불가능한 사이트입니다" 안내해야 해나?
			
			if user_input_size_type not in possible_size_type:
				print('유효한 옵션 번호가 아닙니다')
				continue
			else:
				size_type = int(user_input_size_type)
		return size_type
	
	def __set_request_strategy(self):
		# Requestor + IpRotator v.s. Selenior 분기
		if not self.is_direct_json_url_possible and self.is_selenior_needed:
			# 셀레니어를 생성하는 유일한 경우: direct_url변환은 불가능한데 셀레니어가 필요한 경우
			self.selenior = Selenior(self.SITE_OFFICIAL)
		else: 
			self.ip_rotator = IpRotator()
			self.requestor = Requestor(self.SITE_OFFICIAL, 0, self.ip_rotator) 
	
	def __set_gs_document_and_worksheet(self):
		''' GoogleSheeter 생성 및 문서, 시트 설정 '''
		self.google_sheeter = GoogleSheeter()
		sheet_file_name = input('작업하고자 하는 구글 스프레드시트 문서 제목을 정확히 입력해주세요("대량등록 매크로야 힘내"를 선택하려면 그냥 엔터): ')
		if not sheet_file_name.strip():
			sheet_file_name = "대량등록 매크로야 힘내"
		self.google_sheeter.set_document_and_worksheet(sheet_file_name)
	
	def __open_ip_gateway(self):
		# => 그냥 ip_rotator가 존재하면 게이트를 열도록 함
		if self.ip_rotator is not None:
			self.ip_rotator.open_gateway(self.SITE_OFFICIAL)

	def __set_auto_extract_color_urls(self):
		auto_extract_input = input('추가 색상 발견 시 일괄 추출을 진행하시겠습니까? (y/n) ')
		if auto_extract_input == 'y':
			self.auto_extract_color_urls = True
			print('-> 추가 색상 발견 시 가능한 모든 색상 상품을 일괄 추출합니다')
		else:
			self.auto_extract_color_urls = False
			print('-> 추가 색상 일괄 추출을 진행하지 않습니다')

	def batch(self):
		''' 사용자가 q를 입력할 때까지 batch_size개씩 url 추출 및 행 데이터 삽입 반복 '''
		while True:
			# 배치 사이즈 입력받기(최초 입력 후 생략됨)
			self.batch_size = Batch.get_batch_size_input(self.batch_size)

			# 읽어들일 url 행 입력받기
			self.url_cell = Batch.get_start_url_cell_input(self.url_cell, self.batch_size)
			if self.url_cell is None:
				# 한 번 사용자 입력을 받았는데도 url_cell이 None으로 남아있다는 것은
				# 사용자가 종료 시그널 'q'를 입력했다는 뜻 => outer while루프를 빠져나감
				break

			# 업로드 행 입력받기(최초 입력 후 생략됨)
			self.target_row = Batch.get_initial_upload_row_input(self.target_row, self.batch_size)
			
			# url 읽어들이기
			self.URLS = self.google_sheeter.get_urls(self.url_cell, self.batch_size)
			
			# URLS별 행 데이터 추출(색상 url도 도중에 추가)
			self.__set_rows_data_for_all_URLS()			
			# 추출한 batch_size개 데이터 한 번에 시트에 기록 
			self.google_sheeter.add_rows(self.target_row, self.rows_data)
			# 다음 batch 입력할 행 업데이트
			self.target_row += self.batch_size + self.appended_color_urls_size
			
	@staticmethod
	def get_batch_size_input(batch_size):
		''' 주어진 batch_size가 None이면 사용자에게 배치 사이즈 입력을 요구하여 숫자로 변환, None이 아니면 그대로 반환.
		사용자로부터 입력받은 값이 유효한 값(숫자형 문자열)이 아닌 경우 최대 5회 재입력 요구 후 2로 임의 지정 '''
		tries = 0
		while batch_size is None:
			if tries >= 5:
				print(f'-----\n입력 횟수({tries}회)를 초과하여 배치 사이즈를 2로 임의 지정합니다\n-----')
				return 2
			tries += 1
			user_input_batch_size = input('\n한 번에 읽고 작업할 url 개수(배치 사이즈)를 입력해주세요: ')
			if not user_input_batch_size.isdigit():
				print('입력값이 숫자가 아닙니다')
			else:
				batch_size = int(user_input_batch_size)
		return batch_size
		
	@staticmethod
	def get_start_url_cell_input(url_cell, batch_size):
		''' 
		반환값: 'S115' | None 
		- 기존의 url_cell값을 받아 batch_size를 증가시킨 새 url_cell을 반환
		- 기존 url_cell이 None이면 새로 입력받은 결과 url_cell을 반환
		- 종료 시그널 'q'를 입력받게 되면 None을 반환
		- 재입력 횟수가 5회를 초과하면 'S1'로 임의 반환
		'''
		tries = 0
		while True: 
			if tries >= 5:
				print(f'-----\n입력 횟수({tries}회)를 초과하여 시작 행 번호를 "1"로 임의 지정합니다\n-----')
				return 'S1'
			tries += 1
			user_input_url_cell_num = input(f'\nurl이 적힌 시작 행 번호를 "10"과 같이 입력해주세요(종료를 원할 시 "q", 다음 {batch_size}개의 url로 자동 진행은 엔터): ') 
			if user_input_url_cell_num.lower() == 'q':
				print('q를 입력하여 프로그램을 종료합니다.')
				print('============= 프로그램 종료 =============')
				return None
			elif user_input_url_cell_num.strip() == '':
				if url_cell is None:
					print('처음 url 행 번호는 지정해줘야 합니다.')	
					continue
				url_cell = 'S' + str(int(url_cell[1:]) + batch_size)
				return url_cell
			elif not user_input_url_cell_num.isdigit():
				print(f'유효한 행 번호로 인식할 수 없습니다: {user_input_url_cell_num}')
				continue
			else:
				url_cell = 'S' + str(user_input_url_cell_num)
				return url_cell
	
	@staticmethod
	def get_initial_upload_row_input(target_row, batch_size) -> int:
		''' 
		반환값: 115
		- 업로드할 행 번호 target_row 값을 사용자로부터 입력받아 반환
		- 최대 5회 재입력 요청 후 batch_size + 2행으로 임의 배정
		'''
		tries = 0
		while target_row is None:
			if tries >= 5:
				print(f'-----\n입력 횟수({tries}회)를 초과하여 업로드 행 번호를 {batch_size + 2}로 임의 지정합니다\n-----')
				return batch_size + 2
			tries += 1
			user_input_upload_row_num = input('\n업로드할 행 번호를 입력해주세요(기존 행을 아래로 밀어내고 삽입되는 방식으로 업로드됩니다): ')
			if not user_input_upload_row_num.isdigit():
				print('유효한 행 번호로 인식할 수 없습니다')
			else: 
				target_row = int(user_input_upload_row_num)
		return target_row

	def __set_rows_data_for_all_URLS(self):
		# 한 뭉텅이의 URLS와 운명(초기화)를 함께하는 속성들:
		self.rows_data = []
		self.batch_i = 0
		self.do_not_append_color_urls = []
		self.appended_color_urls_size = 0
		
		# batch_size개 URLS 전체 순회
		while self.batch_i < len(self.URLS):
			print('\n-----------------------------')
			print(f'{self.batch_i + 1}/{len(self.URLS)} (S{str(int(self.url_cell[1:]) + self.batch_i - self.appended_color_urls_size)}) 작업중...')
			url = self.URLS[self.batch_i]
			row_data = self.__get_row_data_of_one_url(url)
			self.rows_data.append(row_data)

			if self.auto_extract_color_urls == True:
				self.__append_color_urls()
			self.batch_i += 1
	
	def __get_row_data_of_one_url(self, url):
		# 요청 --(버튼(2) + (3) 조합)-> soup
		soup = Batch.get_soup(
			self.is_direct_json_url_possible, 
			self.is_selenior_needed, 
			url, 
			self.sc, 
			self.requestor, 
			self.selenior, 
			self.selenior_selectors, 
			bs
		)

		# soup --(사이즈 타입)--> row_data 
		self.sc.set_all_data(soup, self.size_type)
		row_data = self.sc.get_sheet_formatted_row_data(self.size_type)
		row_data[-4] = url # row 데이터에 원본 url 정보 추가
		return row_data
	
	@staticmethod
	def get_soup_from_direct_json(sc, requestor, url):
		url_transformed = sc.replace_to_direct_json_url(url)
		response = requestor.request(url_transformed)
		soup = response.json() # TODO: if 'application/json' in response.headers['Content-Type'] 사전체크 필요할지도
		return soup
	
	@staticmethod
	def get_soup_from_selenior(selenior, selenior_selectors, bs, url):
		html = selenior.get_html_after_waiting_target_selector(url, *selenior_selectors)
		soup = bs(html, "html.parser")
		return soup
	
	@staticmethod
	def get_soup_from_requestor(requestor, bs, url):
		response = requestor.request(url)
		soup = bs(response.content, "html.parser")
		return soup

	get_soup_scenario_type = {
		1: get_soup_from_direct_json,
		2: get_soup_from_selenior,
		3: get_soup_from_requestor,
	}
	
	@staticmethod
	def get_soup(is_direct_json_url_possible, is_selenior_needed, url, sc, requestor, selenior, selenior_selectors, bs):
		# 만약 direct_json_url로 변환이 가능하다면 이걸로 무조건 수행
		if is_direct_json_url_possible:
			# soup = get_soup_scenario_type.get(1)()
			# print('get_soup_from_direct_json 호출됨')
			return Batch.get_soup_from_direct_json(sc, requestor, url)
		# 그렇지 않고 셀레니어 전략이 존재하면 셀레니어로 수행
		elif is_selenior_needed:
			# html = selenior.get_html_after_waiting_target_selector(URLS_ORIGINAL[i], *selenior_selectors)
			# soup = get_soup_scenario_type.get(2)()
			# print('get_soup_from_selenior 호출됨')
			return Batch.get_soup_from_selenior(selenior, selenior_selectors, bs, url)
		else: # Requestor + IpRotator 이용
			# soup = get_soup_scenario_type.get(3)()
			# print('get_soup_from_requestor 호출됨')
			return Batch.get_soup_from_requestor(requestor, bs, url)
		
		return soup
	
	def __append_color_urls(self):
		''' 
		순회할 다른 색상 url을 찾은 경우:
		현재 i가 '다시 색상 url을 추가하지 말아야 할 i범위'가 아니면 URLS에 추가
		(URLS가 json 직접 응답 url이 아닌 것으로 가정)
		'''
		color_urls = self.sc.color_urls
		if len(color_urls) >= 1 and self.batch_i not in self.do_not_append_color_urls:
			print(f'\n추가 색상을 발견하여 추가 추출을 진행합니다 ( +{len(color_urls)}개 )\n')
			# 현재 URLS i번째 직후 자리에 추가 색상 urls 삽입
			self.URLS = Batch.insert_urls(self.URLS, self.batch_i, color_urls)
			
			# 새롭게 삽입한 색상 urls를 순회할 동안은 또 색상 urls를 추가로 URLS에 등록하지 않도록 '다시 색상 url을 추가하지 말아야 할 i범위'를 정의  
			self.do_not_append_color_urls = range(self.batch_i + 1, self.batch_i + 1 + len(color_urls))
			self.appended_color_urls_size += len(color_urls)

			# TODO: 공통 타이틀에 영문 색상명도 추가하기? 복잡하니까 일단 넘어가자

	@staticmethod
	def insert_urls(urls, index, additional_urls):
		'''
		주어진 urls 목록의 index 자리에 additional_urls를 삽입하여 반환 
		'''
		return urls[:index + 1] + additional_urls + urls[index + 1:]
	
	def run_batch(self):
		try:
			self.batch()
		except Exception as e:
			# error_logger.error("An error occurred: %s", e)
			raise e
		finally:
			if self.ip_rotator:
				self.ip_rotator.shutdown_gateway()

def batch():
	'''
	전체 협력 흐름을 조정하는 관리자 역할:
	"사이트명 무엇?" 1 2 3 4 4.5 
	5 "구글 문서명 무엇?" 6
	"읽어들일 셀, 쓸 행 무엇?" 7 8
	"사이즈 타입 무엇?"
	9 10 11 12 13 (반복)
	14
	'''
	global ip_rotator

	is_size_type_deducible = False
	is_direct_json_url_possible = False
	is_selenior_needed = False
	# => 기본은 단순 Requestor + Iprotator를 이용하는 요청
	
	selenior = None
	requestor = None
	# ip_rotator = None
	sc = None
	google_sheeter = None
	
	size_type = None
	selenior_selectors = None

	def front_half():
		nonlocal selenior
		nonlocal requestor
		global ip_rotator
		nonlocal sc
		nonlocal google_sheeter
		nonlocal size_type
		nonlocal selenior_selectors

		print('============= 프로그램 시작 =============\n')
		site_input = input("사이트명을 입력해주세요(ex. 자포스, Zappos, Vans, vans): ")
		sc = SiteClass()
		SITE_OFFICIAL = sc.get_official_site_name(site_input) # TODO: 유효성 검사 및 루프 있어야 함
		# 로깅 셋업
		SITE_OFFICIAL_SNAKE = '_'.join(SITE_OFFICIAL.split(' '))
		set_logging(logging.INFO, SITE_OFFICIAL_SNAKE)

		sc.set_site(SITE_OFFICIAL) # TODO: get_official_site_name()이 띄어쓰기 없는 이름도 받도록 해야함
		selenior_selectors = sc.get_selenium_wait_selectors() # sc.selenium_wait_strategy 직접 접근 막음. 훌륭함
		is_size_type_deducible = sc.size_type_strategy is not None
		# direct_json_url_transformer = sc.direct_json_url_transform_strategy # TODO: -> 무조건 호출하는 걸로, 해당 속성을 외부에서 직접 접근하는 것을 막음. 나름 해결 완료
		
		# 위의 세가지 플래그를 속성 그대로 접근해서 일단 사용해봄
		is_size_type_deducible = sc.size_type_strategy is not None
		is_direct_json_url_possible = sc.direct_json_url_transform_strategy is not None
		is_selenior_needed = sc.selenium_wait_strategy is not None

		# 사이즈 타입 입력받기(최초 입력 후 생략됨)
		size_type = get_size_type_input(is_size_type_deducible, None)

		# selenior = None
		# requestor = None
		# ip_rotator = None
		# Requestor + IpRotator v.s. Selenior 분기
		if not is_direct_json_url_possible and is_selenior_needed:
			# 셀레니어를 생성하는 유일한 경우: direct_url변환은 불가능한데 셀레니어가 필요한 경우
			selenior = Selenior()
		else: 
			ip_rotator = IpRotator()
			requestor = Requestor(SITE_OFFICIAL, 0, ip_rotator) 

		google_sheeter = GoogleSheeter()
		sheet_file_name = input('작업하고자 하는 구글 스프레드시트 문서 제목을 정확히 입력해주세요("대량등록 매크로야 힘내"를 선택하려면 그냥 엔터): ')
		if not sheet_file_name.strip():
			sheet_file_name = "대량등록 매크로야 힘내"
		google_sheeter.set_document_and_worksheet(sheet_file_name)

		# if size_type == 3 or len(selenior_selectors) == 0: 
		# 	ip_rotator.open_gateway(SITE_OFFICIAL)
		# => 그냥 ip_rotator가 존재하면 게이트를 열도록 함
		if ip_rotator is not None:
			ip_rotator.open_gateway(SITE_OFFICIAL)
	front_half()

	batch_size = None
	url_cell = None
	target_row = None
	# size_type = None
	# quit = False
	while True:
		# 배치 사이즈 입력받기(최초 입력 후 생략됨)
		batch_size = get_batch_size_input(batch_size)

		# 읽어들일 url 행 입력받기
		url_cell = get_start_url_cell_input(url_cell, batch_size)
		if url_cell is None:
			# 한 번 사용자 입력을 받았는데도 url_cell이 None으로 남아있다는 것은
			# 사용자가 종료 시그널 'q'를 입력했다는 뜻 => outer while루프를 빠져나감
			break

		# 업로드 행 입력받기(최초 입력 후 생략됨)
		target_row = get_initial_upload_row_input(target_row, batch_size)
		
		# url 읽어들이고 변환하기
		URLS = google_sheeter.get_urls(url_cell, batch_size)
		# URLS_ORIGINAL = google_sheeter.get_urls(url_cell, batch_size)
		# URLS = transform_urls(URLS_ORIGINAL, is_direct_json_url_possible)
		# def transform_urls(urls_original, is_direct_json_url_possible):
		# 	''' urls_original 목록을 받아 'json 직접 추출'이 가능하다면
		# 	해당 url로 변환한 결과를, 그렇지 않다면 원본 그대로를 반환 '''
		# 	if is_direct_json_url_possible:
		# 		return sc.replace_to_direct_json_urls(urls_original)
		# 	else:
		# 		return urls_original


		# url별 데이터 추출
		rows_data = []
		# for i, url in enumerate(URLS):
		i = 0
		do_not_append_color_urls = []
		appended_color_urls_size = 0
					
		while i < len(URLS):
			url = URLS[i]
			print('\n-----------------------------')
			print(f'{i + 1}/{len(URLS)} (S{str(int(url_cell[1:]) + i - appended_color_urls_size)}) 작업중...')
			
			# 요청 --(버튼(2) + (3) 조합)-> soup
			soup = get_soup(is_direct_json_url_possible, is_selenior_needed, url, sc, requestor, selenior, selenior_selectors, bs)

			# soup --(사이즈 타입)--> row_data 
			sc.set_all_data(soup, size_type)
			row_data = sc.get_sheet_formatted_row_data(size_type)
			if size_type == 3: # 아동 신발 대표이미지 로컬에 저장
				target_directory = os.path.join("C:", "Jubilee's Com", "Downloads")
				# target_directory = os.path.join(ROOT_DIR, 'test')
				title_image_file_name = requestor.download_image(row_data[-3], target_directory)
				row_data[-3] = title_image_file_name
			else: 
				# row_data[-4] = URLS_ORIGINAL[i] # row 데이터에 원본 url 정보 추가
				row_data[-4] = url # row 데이터에 원본 url 정보 추가
			rows_data.append(row_data)

			# 순회할 다른 색상 url을 찾은 경우:
			# 현재 i가 '다시 색상 url을 추가하지 말아야 할 i범위'가 아니면 URLS에 추가
			# (URLS가 json 직접 응답 url이 아닌 것으로 가정)
			if len(sc.color_urls) >= 1 and i not in do_not_append_color_urls:
				print(f'\n추가 색상을 발견하여 추가 추출을 진행합니다 ( +{len(sc.color_urls)}개 )\n')
				# 현재 URLS i번째 직후 자리에 추가 색상 urls 삽입
				URLS = insert_urls(URLS, i, sc.color_urls)
				def insert_urls(urls, index, additional_urls):
					'''
					주어진 urls 목록의 index 자리에 additional_urls를 삽입하여 반환 
					'''
					return urls[:index + 1] + additional_urls + urls[index + 1:]
				
				# 새롭게 삽입한 색상 urls를 순회할 동안은 또 색상 urls를 추가로 URLS에 등록하지 않도록 '다시 색상 url을 추가하지 말아야 할 i범위'를 정의  
				do_not_append_color_urls = range(i + 1, i + 1 + len(sc.color_urls))
				appended_color_urls_size += len(sc.color_urls)

				# 3) 공통 타이틀에 영문 색상명도 추가하기? 복잡하니까 일단 그냥 가자
			i += 1

		# 추출한 batch_size개 데이터 한 번에 시트에 기록 
		google_sheeter.add_rows(target_row, rows_data)
		target_row += batch_size + appended_color_urls_size

def run_batch():
	global ip_rotator
	try:
		batch()
	except Exception as e:
		# error_logger.error("An error occurred: %s", e)
		raise e
	finally:
		if ip_rotator:
			ip_rotator.shutdown_gateway()

def main():
	# run_batch()
	batch = Batch()
	batch.run_batch()


if __name__ == '__main__':
	main()
