#-*-coding: utf-8-*-

from bs4 import BeautifulSoup as bs
import requests
import pickle
# from googletrans==4.0.0-rc1 import Translator
import googletrans
from google.cloud import translate_v2 as cloud_trans # 구글 번역을 위한 google-cloud-translate 라이브러리
from deep_translator import GoogleTranslator
import translate

## (추가)다양한 사용자 에이전트를 사용하여 크롤러를 "인간처럼" 보이게 만들기:
# 사용자의 웹 브라우저의 식별자
my_user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
					'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_0) Gecko/20100101 Firefox/70.0',
					'Mozilla/5.0 (iPhone; CPU iPhone OS 13_1_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.1 Mobile/15E148 Safari/604.1']

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
headers2 = {
	'User-Agent': my_user_agents[0],
	'Accept': accept,
	'Accept-Language': accept_language,
	'DNT': dnt,  # Do Not Track Request Header
	'Connection': connection,
	'Upgrade-Insecure-Requests': upgrade_insecure_requests
}
## 모질라 파이어폭스 + 맥OS 사용자
headers3 = {
	'User-Agent': my_user_agents[1],
	'Accept': accept,
	'Accept-Language': accept_language,
	'DNT': dnt,  # Do Not Track Request Header
	'Connection': connection,
	'Upgrade-Insecure-Requests': upgrade_insecure_requests
}
## 사파리 + 아이폰 사용자
headers4 = {
	'User-Agent': my_user_agents[2],
	'Accept': accept,
	'Accept-Language': accept_language,
	'DNT': dnt,  # Do Not Track Request Header
	'Connection': connection,
	'Upgrade-Insecure-Requests': upgrade_insecure_requests
}


url_deleted = 'https://www.zappos.com/p/polo-ralph-lauren-charlotte-bear-scuff-slipper-cream/product/9954967/color/1892'
url_outdated = 'https://www.zappos.com/p/polo-ralph-lauren-collins-moccasin-slipper-snuff-1/product/9811783/color/1022969'
url = 'https://www.zappos.com/p/polo-ralph-lauren-kids-cable-knit-cotton-cardigan-big-kids-hint-of-pink-nevis-pony-player/product/8995681/color/732400'

# soup_from_pickle = ''
# soup_from_txt = ''


# 2. HTTP 응답을 파일에 저장 및 불러오기
#(사용하지 않게된 코드)
def get_webpage(url, headers):
	print('-------- ! HTTP 요청함 ----------------')
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		# translated = translator.translate(response.content, target_language='ko')
		soup = bs(response.content, "html.parser")
	return soup
## 2-1. HTTP 응답 객체 자체 저장
def save_webpage_response(url, headers):
	print('-------- ! HTTP 요청함 ----------------')
	response = requests.get(url, headers=headers)
	if response.status_code == 200:
		with open('2024_Zappos/response_Polo_Ralph_Lauren_Collins_Moccasin_Slipper.pickle', 'wb') as f:
			pickle.dump(response, f)
			print('Successfully saved HTTP response----------')
## 2-2. 저장된 HTTP 응답 pickle 파일을 객체로 불러오기 
def load_webpage_response():
	try:
		with open('2024_Zappos/response_Polo_Ralph_Lauren_Collins_Moccasin_Slipper.pickle', 'rb') as f:
			response = pickle.load(f)
			if (response.status_code == 200):
				print('Successfully loaded HTTP response----------')
		return response
	except FileNotFoundError:
		save_webpage_response(url, headers3)

response = load_webpage_response()
print(response.status_code)

## 2-3. 복구한 response 객체를 soup으로 파싱
# ex) new_soup = parse_response_to_soup(load_webpage_response())
def parse_response_to_soup(response):
	if (response.status_code == 200):
		soup = bs(response.content, "html.parser")

	return soup
soup = parse_response_to_soup(response)


# 3. HTTP 응답을 구글 번역 API로 한국어로 번역
## 1. googletrans
# trans = googletrans.Translator()
## 2. google-cloud-translator
# translator = trans.Client()
## 3. deep_translator
# deep_translator = GoogleTranslator(source="auto", target="ko")
## 4. translate
trans = translate.Translator(to_lang="ko")

## 3-1. response 객체를 한국어로 번역 후 soup으로 파싱 테스트
def translate_and_parse_response_to_soup(response):
	if (response.status_code == 200):
		ori_soup = bs(response.content, "html.parser")
		product_recap = ori_soup.select_one('div[id="productRecap"]')

		# # 1. googletrans
		# trans = googletrans.Translator()
		# translated = trans.translate(product_recap.text, dest="ko")
		# soup = bs(translated.text, "html.parser")

		# # 2. google-cloud-translator
		# translator = cloud_trans.Client()
		# translated = translator.translate(product_recap.text, target_language='ko')
		# soup = bs(translated["translatedText"], "html.parser")

		# 3. deep_translator
		deep_translator = GoogleTranslator(source="auto", target="ko")
		translated = deep_translator.translate(product_recap.text[:5000])
		soup = bs(translated, "html.parser")
		print(translated)
		
		# # 4. translate
		# trans = translate.Translator(to_lang="ko")
		# translated = trans.translate(product_recap.text[400:])
		# soup = bs(translated, "html.parser")
		# print(translated)
		# print('---------------')
		# print(soup.prettify())


		# print(translated.text[:1000])
		print('---------------')
		print(soup.prettify()[:1000])
	return soup
# translated_soup = translate_and_parse_response_to_soup(response)
# print(get_full_name(translated_soup))
## => 결과: 
'''
#0. 구글 크롬 번역: 
---------------
폴로 랄프 로렌

샬롯 베어 스커프 슬리퍼
SKU 9954967
$59.95
색상:크림
A 선택 색상

크림

대부분의 경우 맞습니다정사이즈. 하프 사이즈를 입는 경우 사이즈 다운을 고려해 보세요.

사이즈를 계산해보세요
여성용 사이즈:

6

8

9

10
사이즈를 찾을 수 없나요? 우리에게 알려주십시오.
폭 옵션:

중
무료 업그레이드된 배송 및amp; 로 돌아옴
아마존 프라임
사이즈 차트
사이즈 차트 보기
제품정보
Polo Ralph Lauren
보송보송한 슬리퍼인 폴로 랄프 로렌® 샬롯 베어 스커프 슬리퍼는 둥근 발가락 디자인으로 제공됩니다. 직물 갑피와 안감으로 제작된 이 슬리퍼에는 전체 길이의 풋베드가 있어 편안함을 더해줍니다. 유연한 고무 밑창은 실내와 실외 모두에 적합합니다. 앞면의 시그니처 브랜드 디테일이 구조감을 더해줍니다.
슬립온 스타일.
수입.
Zappos.com 용어집 보기
이 설명에서 잘못된 점을 찾으셨나요? 문제를 해결할 수 있도록 도와주세요! 오류 보고
===============

#1. googletrans
---------------
Videopolo Ralph Lauren Charlotte Bear Scuff Slippersku 9954967 $ 59.95 Color : Crimselect a ColorcreamCalculate SizeWomen의 크기 : 68910 크기를 찾지 못합니까?통지 옵션 : Cartpolo Ralph Ralph Lauren Bear Scuff Slipperships 무료 $ 59.95ADD에 $ 59.95ADD로 $ 59.95ADD를 업그레이드하고 RETURNS WISTSIZE ChartView 크기 차트 제품 정보 슬리퍼의 퍼지 쌍, 라운드 트리와 함께 제공 됩니다.설계.섬유 상단과 안감으로 제작 된이 슬리퍼는 편안함을 추가 할 수있 는 전장 발바닥이 있습니다.유연한 고무 아웃솔은 실내와 실외 모두에 적합합니다.전면의 시그니처 브랜드 디테일은 구조에 추가됩니다 .sku : #9954967slip-on style.mported.view zappos.com 용어의 용어집이 설명에서 문제가 있습니까? 우리가 그것을 고치도록 도와주세요!이 페이지가 도움이되었다고보고하십시오. 예요
===============

# 2. 
크레딧 문제로 보류
================

# 3. deep_translator
GoogleTranslator
---------------
동영상 재생Polo Ralph Lauren 샬롯 베어 스커프 슬리퍼SKU 9954967$59.95색상: 크림색상 선택크림사이즈 계산여성 사이즈: 68910사이즈를 찾을 수 없나요? 알려주세요.너비 옵션: M장바구니에 담기Polo Ralph Lauren 샬롯 베어 스커프 슬리퍼 무료$59.95장바구니에 추가하기무료 업그레이드 배송 및 반품 사이즈 차트 보기제품 정보푹신한 슬리퍼, 폴로 랄프 로렌® 샬롯 베어 스커프 슬리퍼는 둥근 앞코로 제공됩니다. 설계. 직물 갑피와 안감으로 제작된 이 슬리퍼에는 전체 길이의 풋베드가 있어 편안함을 더해줍니다. 유연한 고무 밑창은 실내와 실외 모두에 적합합니다. 앞면의 시그니처 브랜드 디테일이 구조를 더욱 돋보이게 합니다.SKU: #9954967슬립온 스타일.수입됨.Zappos.com 용어집 보기 이 설명에서 잘못된 부분을 찾으셨나요? 문제를 해결하도록 도와주세요! 오류 신고 이 페이지가 도움이  되었나요?예아니요
=================

# 4. translate
한 번 번역에 500자 제한
---------------
[:500]
동영상 재생Polo Ralph Lauren Charlotte Bear Scuff SlipperSKU 9954967 $ 59.95 색상: 크림색상 선택크림사이즈 계산여성 사이즈: 68910사이즈를 찾을 수 없나요? 알림. 너비 옵션: M장바구니에 담기Polo Ralph Lauren Charlotte Bear Scuff Slipperships free $ 59.95 장바구니에 담기FREE upgraded shipping & returns with사이즈 차트 보기제품 정보보송한 슬리퍼 한 켤레인 Polo Ralph Lauren ® Charlotte Bear Scuff Slipper는 둥근 발가락 디자인으로 제작되었습니다. 섬유로 제작
----------------
[500:1000]
갑피와 안감을 댄 이 슬리퍼는 전체 길이의 풋베드가 있어 편안함을 더합니다. 
유연한 고무 아웃솔로 실내와 실외 모두에 적합합니다. 전면의 시그니처 브랜드 디테일이 구조에 추가됩니다 .SKU: # 9954967슬립온 스타일. 수입. Zappos.com  용어집 보기이 설명에서 잘못된 점을 찾으셨나요? 문제 해결을 도와주세요! 오류 신고이 페이지가 도움이 되었나요? 예아니요
-----------------
[400:]
Polo Ralph Lauren ® Charlotte Bear Scuff Slipper는 라운드 토 디자인으로 제
공됩니다. 텍스타일 갑피와 안감으로 제작된 이 슬리퍼는 전체 길이의 풋베드가 있어 편안함을 더합니다. 유연한 고무 아웃솔로 실내와 실외 모두에 적합합니다. 전면의 시그니처 브랜드 디테일이 구조에 추가됩니다 .SKU: # 9954967슬립온 스타일. 수입. Zappos.com 용어집 보기이 설명에서 잘못된 점을 찾으셨나요? 문제 해결을 도와주세요! 오류 신고이 페이지가 도움이 되었나요? 예아니요
================
'''

# 3-2. 
def translate_sample(text):
	# 3. deep_translator
	deep_translator = GoogleTranslator(source="auto", target="ko")
	translated = deep_translator.translate(text[:5000])
	# soup = bs(translated, "html.parser")
	# print(translated)
	return translated
sample_text="Experience ultimate comfort and support wearing Skechers Hands Free Slip-ins®: GO WALK® Arch Fit® 2.0 - Delara. Designed with our exclusive Heel Pillow™, this vegan slip-on features an athletic mesh upper with a removable Arch Fit® insole, lightweight ULTRA GO® cushioning, plus Comfort Pillars™ for added support."
# translate_sample(sample_text)
'''
=> 결과: 
Skechers Hands Free Slip-ins®: GO WALK® Arch Fit® 2.0 - Delara를 착용하여 최고의 편안함과 지지력을 경험해 보세요. 독점적인 Heel Pillow™로 디자인
된 이 비건 슬립온은 탈착 가능한 Arch Fit® 깔창이 있는 운동용 메쉬 갑피, 가벼운 ULTRA GO® 쿠셔닝, 추가 지지력을 위한 Comfort Pillars™를 특징으로 
합니다. 
'''



## 2-4. soup 객체를 저장하고 불러오기
# ex) new_soup = read_or_save_soup_txt('2024_Zappos/soup_from_saved_response_Polo_Ralph_Lauren_Collins_Moccasin_Slipper.txt', 1)
def read_or_save_soup_txt(file_name, origin_type=1):
	try:
		# 불러오기1: 텍스트 파일에서 soup 객체 복원하기
		with open(file_name, 'r', encoding='utf-8') as file:
			soup_text = file.read()
			soup = bs(soup_text, "html.parser")
		return soup
	except FileNotFoundError:
		# soup 객체 생성
		if (origin_type == 1): # "response 객체 파일에서 파싱한 soup을 저장한 txt파일"
			soup = parse_response_to_soup(load_webpage_response())
		elif (origin_type == 2): # "response 객체를 곧바로 파싱한 soup을 txt로 저장한 파일"
			print('-------- ! HTTP 요청함 ----------------')
			response = requests.get(url, headers=headers3)
			if response.status_code == 200:
				# translated = translator.translate(response.content, target_language='ko')
				soup = bs(response.content, "html.parser")
			else:
				print('해당 URL로 요청에 대한 응답코드가 200이 아니므로 파일로 만들지 못합니다')
				soup = None
			# soup = get_webpage()
		else: 
			print('유효하지 않은 origin_type 넘버입니다')
			return
		# 저장1: 생성한 soup을 텍스트 파일에 저장
		if (soup):
			soup_str = str(soup)
			with open(file_name, 'w', encoding='utf-8') as file:
				file.write(soup_str)
'''
## 2-5. "response 객체 파일에서 파싱한 soup을 저장한 txt파일"과 "response 객체를 곧바로 파싱한 soup을 txt로 저장한 파일"이 같은지 비교하기
read_or_save_soup_txt('2024_Zappos/test1_res_file_to_soup_txt_Polo_Ralph.txt', 1)
read_or_save_soup_txt('2024_Zappos/test2_soup_to_soup_txt_Polo_Ralph.txt', 2)
### => 'test1_res_file_to_soup_txt_Polo_Ralph.txt'와 'test2...'파일이 잘 생성되는지 눈으로 확인

## 2-6. 2-5에서 읽어들인 soup이 같은지 비교하기
txt_soup1 = read_or_save_soup_txt('2024_Zappos/test1_res_file_to_soup_txt_Polo_Ralph.txt', 1)
txt_soup2 = read_or_save_soup_txt('2024_Zappos/test2_soup_to_soup_txt_Polo_Ralph.txt', 2)
print(f"txt_soup1.length: {len(txt_soup1.prettify())}")
print(f"txt_soup2.length: {len(txt_soup2.prettify())}")

## 2-7. "response 객체 파일에서 파싱한 soup"과 "response 객체를 파싱한 soup을 txt로 저장했다 읽어들여 다시 파싱한 soup"이 같은지 비교하기
pickle_soup1 = parse_response_to_soup(load_webpage_response())
print(f"pickle_soup1.length: {len(pickle_soup1.prettify())}")
print(f"txt_soup2.length: {len(txt_soup2.prettify())}")

## => 2-6, 2-7, 2-8의 결과: 조금씩의 문자 길이 차는 있지만 전부 잘 생성되고 전부 잘 soup으로 변환됐다!
'''

# try:
# 	# 불러오기2: pickle 파일에서 soup 객체 복원하기
# 	with open('soup_Polo_Ralph_Lauren_Collins_Moccasin_Slipper.pickle', 'rb') as f:
# 		soup_from_pickle = pickle.load(f)
# 		print('inside pickle context----------')
# 		# get_full_name(soup_from_pickle)
# except FileNotFoundError:	
# 	# 저장2: global_soup을 pickle 객체로 저장
# 	if (global_soup):
# 		with open('soup_Polo_Ralph_Lauren_Collins_Moccasin_Slipper.pickle', 'wb') as f:
# 			pickle.dump(global_soup, f)
# 			print('Saved soup as pickle file')
### => dump 중 "RecursionError: maximum recursion depth exceeded while calling a Python object" 에러 발생. 

# 파일이 닫히면 soup_from_pickle은 사용 못하나? 

# print('with "txt soup"----------')
# get_full_name(soup_from_txt)
# print('with "pickle soup"----------')
# get_full_name(soup_from_pickle)
### => soup_from_txt 됐다!


# 4. 만든 soup을 이용해 내용물 추출하기
## 4-1. 상품 풀네임(상표 + 상품명) 추출
# ex) "Polo Ralph Lauren Charlotte Bear Scuff Slipper"
def get_full_name(soup):
	if soup:
		title_meta_tag = soup.select_one('meta[itemprop="name"]')
		if title_meta_tag:
			product_name = title_meta_tag.get('content')
			return product_name
		else:
			print('No meta tag found')
	else:
		print('Soup is not initialized')
def print_product_name(soup):
	full_name = get_full_name(soup)
	translated = translate_sample(full_name)
	print(f"제품명: {translated} {full_name}")
# print_product_name(soup)
def get_brand_name(soup):
	brand_span_tag = soup.select_one('span[itemprop="brand"]')
	if brand_span_tag:
		brand_name = brand_span_tag.select_one('a[itemprop="url"]').get('aria-label')
		return brand_name.strip()
def get_product_name(soup):
	'''full_name에서 brand_name을 제외한 후반부만 따온다'''
	full_name = get_full_name(soup)
	brand_name = get_brand_name(soup)
	product_name = full_name.replace(brand_name, '').strip()
	return product_name


## 4-2. 상품 이미지 url 추출
def get_images(soup):
	if soup:
		div = soup.find("div", {"id": "stage"})
		images = div.find_all("img")
		# images = soup.select("#productImages img[data-track-label='Zoom-In']")
		src_list = []
		for image in images:
			if "srcset" in image.attrs:
				index = image['src'].find('AC_SR')
				refined_img = '%sAC_SR530,500_.jpg' % image['src'][:index]
				src_list.append(refined_img)
		return src_list
# for src in get_images(soup):
# 	print(src)
'''
=> 성공
결과 샘플: "srcset"속성이 존재하는 다음 다섯 개 <img> 태그에서 크기를 키운 url을 추출 완료함

<img alt="Polo Ralph Lauren Charlotte Bear Scuff Slipper - Pair View" src="https://m.media-amazon.com/images/I/71td85cQhSL._AC_SR73,58_.jpg" srcset="https://m.media-amazon.com/images/I/71td85cQhSL._AC_SR146,116_.jpg 2x"/>
<img alt="Polo Ralph Lauren Charlotte Bear Scuff Slipper - Top View" src="https://m.media-amazon.com/images/I/61DcLvgsKlL._AC_SR73,58_.jpg" srcset="https://m.media-amazon.com/images/I/61DcLvgsKlL._AC_SR146,116_.jpg 2x"/>
<img alt="Polo Ralph Lauren Charlotte Bear Scuff Slipper - Bottom View" src="https://m.media-amazon.com/images/I/61ZHGPhC1bL._AC_SR73,58_.jpg" srcset="https://m.media-amazon.com/images/I/61ZHGPhC1bL._AC_SR146,116_.jpg 2x"/>
<img alt="Polo Ralph Lauren Charlotte Bear Scuff Slipper - Left View" src="https://m.media-amazon.com/images/I/61eqcKcKXyL._AC_SR73,58_.jpg" srcset="https://m.media-amazon.com/images/I/61eqcKcKXyL._AC_SR146,116_.jpg 2x"/>
<img alt="Polo Ralph Lauren Charlotte Bear Scuff Slipper - Back View" src="https://m.media-amazon.com/images/I/61jG1SLkjZL._AC_SR73,58_.jpg" srcset="https://m.media-amazon.com/images/I/61jG1SLkjZL._AC_SR146,116_.jpg 2x"/>

=> 

https://m.media-amazon.com/images/I/71td85cQhSL._AC_SR530,500_.jpg
https://m.media-amazon.com/images/I/61DcLvgsKlL._AC_SR530,500_.jpg
https://m.media-amazon.com/images/I/61ZHGPhC1bL._AC_SR530,500_.jpg
https://m.media-amazon.com/images/I/61eqcKcKXyL._AC_SR530,500_.jpg
https://m.media-amazon.com/images/I/61jG1SLkjZL._AC_SR530,500_.jpg
'''

## 4-3. 색상 선택을 위한 사전 조사
# 같은 제품(9811783) 다른 색상(1022969) 이미지: <label for="6065894-9811783-PRODUCT_PAGE" aria-current="true" class="esa-z fsa-z"><span class="sr-only">Snuff 1</span><div><img src="https://m.media-amazon.com/images/I/711ZnkdtLcL.AC_SS144.jpg" alt="" aria-hidden="true" class="isa-z"></div></label>
# 같은 제품(9811783) 다른 색상(124204) 이미지 : <label for="6167232-9811783-PRODUCT_PAGE" aria-current="false" class="esa-z"><span class="sr-only">Navy 2</span><div><img src="https://m.media-amazon.com/images/I/61mD+g-i21L.AC_SS144.jpg" alt="" aria-hidden="true" class="isa-z"></div></label>
# 같은 제품(9811783) 다른 색상(3) 이미지      : <label for="6065896-9811783-PRODUCT_PAGE" aria-current="false" class="esa-z"><span class="sr-only">Black</span><div><img src="https://m.media-amazon.com/images/I/51n-qY0ySEL.AC_SS144.jpg" alt="" aria-hidden="true" class="isa-z"></div></label>
# => 그 바로 형 태그! : <input type="radio" name="colorSelect" class="sr-only dsa-z" data-color-name="Black" data-style-id="6065896" data-is-new="false" id="6065896-9811783-PRODUCT_PAGE" wfd-id="id131">
# ==> "colorSelect" 단어 자체가 전체 페이지에 딱 컬러별 아이템 개수밖에 없다! <input name="colorSelect">[]

# 끝에 붙는 상품별 url : <meta itemprop="url" content="/product/9811783/color/1022969">
# 	=> 전체 url: "https://www.zappos.com/p/polo-ralph-lauren-collins-moccasin-slipper-snuff-1/product/9811783/color/1022969"
# 또다른 어떤 url: <meta itemprop="url" content="/p/polo-ralph-lauren-collins-moccasin-slipper-snuff-1/product/9811783/color/1022969">
# <input type="hidden" name="productId" value="9811783" wfd-id="id61">
# <input type="hidden" name="colorId" value="1022969" wfd-id="id62">
def get_color_name_of_this_page(soup):
	if (soup):
		color_inputs = soup.find_all("input", {"name": "colorSelect"})
		# 이 <input>의 동생 태그들인 <label>태그에서 "area-current"="true"인 단 하나를 골라서 
		# 지금 <input> 태그의 "data-color-name"속성을 뽑든지, 동생 태그인 <label>의 텍스트를 뽑든지.
		for input in color_inputs:
			sibling_label = input.find_next_sibling()
			if (sibling_label is not None):
				if (sibling_label["aria-current"] == "true"):
					return input["data-color-name"]
# print(f'color name: {get_color_name_of_this_page(soup)}')

## 풀 제품명 만들기
def make_full_title(soup):
	'''브랜드+색상+상품명+영문상품명
		(현재는 영문색상으로 넣음)
	'''
	brand_name_ko = translate_sample(get_brand_name(soup))
	product_name = get_product_name(soup)
	product_name_ko = translate_sample(get_product_name(soup))
	color_name = get_color_name_of_this_page(soup)
	color_name_ko = translate_sample(color_name)
	title = f'{brand_name_ko} {color_name} {product_name_ko} {product_name}'
	return title
print(f'Title: {make_full_title(soup)}')

## 4-4. 옵션 추출
def get_size_options(soup):
	if (soup):
		inputs = soup.find_all("input", {"data-track-label": "size"})
		# '품절'을 의미하는 두가지 표식:
		# 1) <input>의 부모 태그 <div>의 class에 "_ya-z"가 붙으면 품절, 없으면 품절 아님
		# 2) <input>의 속성 중 "aria-label"에 "Size 9 is Out of Stock"이라고 되어있으면 품절, "Size 8"이라고만 되어 있으면 품절 아님
		# => 어느 게 더 영속적일까? "OOO is Out of Stock"이라는 문구가 더 자주 바뀔까, class명 "_ya-z"가 더 자주 바뀔까?
		# ==> 일단 자식 input 태그를 찾아놨으니까 그 속성으로 판단하기로 한다:
		remained_sizes = []
		for input in inputs:
			if "out of stock" not in input.attrs["aria-label"].lower():
				size = input['data-label']
				remained_sizes.append(size)
		return remained_sizes

## 4-5. "색상 사이즈" 옵션 프린트
color_name = get_color_name_of_this_page(soup)
sizes = get_size_options(soup)
color_size_options = []
for size in sizes:
	print(f'{color_name} {size}')
	color_size_options.append(f'{color_name} {size}')
print(color_size_options)

## 4-6. 가격(우선 '할인중' 가격으로 추출)
# <span aria-label="$64.95" class="ZF-z _F-z" itemprop="price" content="64.95">...</span>
def get_oriprice(soup):
	spans = soup.find_all("span", {"itemprop": "price"}) # 왜인진 모르지만 결과가 딱 하나 나온다
	# 그래도 "content"="64.95"라는 속성을 가진 태그라면 확정
	for span in spans:
		if "content" in span.attrs:
			return span["aria-label"]
	return "No price was found"
print(f'Price: {get_oriprice(soup)}')

## 4-7. 상세설명
def get_translated_description(soup):
	description_div = soup.find("div", {"itemprop": "description"})
	description_ul = description_div.find("ul")
	li_tags = description_ul.findChildren("li", recursive=False) # ul의 직계 자식 레벨의 li 태그들만 선택
	translated = []
	for description in li_tags:
		if "sku" in description.text.lower():
			continue
		translated.append(translate_sample(description.text))
	return translated
descriptions = get_translated_description(soup)
# for des in descriptions:
# 	print(des)



# 5. 상세 페이지 html 만들기

url_test = ['aaa','bbb','ccc','ddd','eee','fff']
img_urls = get_images(soup)
def make_img_tag(img_url):
	tag = f'<img src="{img_url}">'
	return tag
def make_img_tags(img_list):
	tags = ''
	for url in img_list:
		tags += make_img_tag(url) + '\n'
	return tags
# descriptions
def make_description_tags(ko_descriptions):
	tag = ''
	for des in ko_descriptions:
		tag += f'''<p style="font-size: 22px; font-family: 'Noto Sans'; line-height: 150%;"><b>{des}</b></p>\n'''
	return tag
ko_description_detail = make_description_tags(descriptions)
# color_name
product_images = make_img_tags(img_urls)
html = f'''
<center>
	<img src="https://shop-phinf.pstatic.net/20231223_192/1703294800790PjOlB_PNG/image.png?type=w860">
	{ko_description_detail}

	<div style="display: block;">
		<img src="https://www.skechers.com/on/demandware.static/-/Library-Sites-SkechersSharedLibrary/default/dw72c4120b/images/pdp/logo.svg;">
	</div>
	<div style="display: block;">
		<img src="https://shop-phinf.pstatic.net/20231224_181/1703411552356CimWI_PNG/image.png?type=w860">
	</div>

	<p>
		<font size="5"><b> 색상: {color_name}
	</p>

	{product_images}

	<img src="https://shop-phinf.pstatic.net/20231223_28/1703297049673JNuGv_JPEG/skechers_2.jpg?type=w860">
	'''

# print(html)


# 구글 시트 연동
import gspread
def gsheet():
	# Google Sheets API를 사용하기 위한 인증
	gc = gspread.service_account(filename='2024_Zappos\python-crawling-gspread-145332f402e3.json')

	# 스프레드시트 열기
	sh = gc.open('대량등록 시트 테스트')
	# sh = gc.open_by_key('1kXGuatJwOmkMAat38UZ7OLdGBjt3HS1AobTGmlOuDns')
	# sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1kXGuatJwOmkMAat38UZ7OLdGBjt3HS1AobTGmlOuDns/edit#gid=0')
	# sh = gc.create('A new sheet')
	# sh.share()

	# 작업할 워크시트 선택
	worksheet = sh.get_worksheet(0)  # 0은 첫 번째 워크시트를 의미합니다.
	# worksheet = sh.sheet1
	# worksheet = sh.worksheet("시트1")	
	# worksheet_list = sh.worksheets() # 전체 시트 목록
	# worksheet = sh.add_worksheet(title="New gorio worksheet", rows=50, cols=26) # 워크시트 추가
	# sh.del_worksheet(worksheet) # 워크시트 삭제

	# # 데이터 추가
	# price = "$64.45"
	# product_name = "폴로 랄프로렌 slipper"
	# worksheet.append_row([price, product_name], table_range="A6")
	# 데이터 가져오기
	# val = worksheet.acell('B1').value
	# print(val)




# ===========================================
# 판매가
# 사이즈 옵션
# 이미지 + 한글 번역 상세설명
# ==========================================
# 유용할 것 같은 태그들: 
# <span itemprop="sku">9811783</span>
# <meta itemprop="sku" content="9625394"> => meta 태그는 상품 본인의 sku를 가지고 있는 게 없음. 이건 쓰면 안 됨.
# <div class="v4-z" itemprop="description">


'''
- 카테고리 코드
네이버에 카테고리별 목록표가 있음. 
+추후: 맞춰 넣기

- 상품명 
기본: 브랜드명+색상+상품명+영문상품명
+추후: 제목을 더 풍성하게

- 판매가
"$(원 판매가 + 배송비) + 35% 마진"을 환율 적용한 원화가 기본
원 판매가의 구간별로 달라짐
진짜 최저: 75,000원
최저~$50 => 40% 마진
...

- 옵션
Navy 7 -> 네이비 250
브랜드별로 사이즈 변환 테이블이 다 다를 수 있음
(컨버스와 반스가 대표적)

- 옵션 재고 수량
남성 신발: 7.0 ~ 14.0 => 250mm ~ 330mm, '재고 있음'이 4/15 % 이상이면 살리기
	7.0 = 250(mm)
	7.5 = 255
	8.0 = 260 ...
	...
	14.0 = 330
여성 신발: 
	5.0 = 220(mm)
	5.5 = 225
	...
	10.0 = 270
	10.5 = 275
	11.0 = 280
	
+추가: 품절에 가까운 제품을 반영할 수 있도록


- 색상
색상마다 url 필요

- 대표이미지
+추가: 색상이 합쳐진다면 합쳐진 대표이미지로 넣기

- 브랜드
- 제조사
어그, 폴로랄프로렌(로렌, 폴로 등 부가 없이), 뉴발란스

- 상세설명-> 떡 이미지로, 너비 지금 좋음
브랜드 별 소개 이미지
제품명 들어가도 되고 없어도 그만
상세설명(글씨 크기 대략 28)
부제 굳이 필요 없는데, 색상이 여럿인 경우 "색상: 네이비"
이미지들은 1+2+2... 지금 그대로 좋음
브랜드 별 부가 이미지 여럿


'''

# ================================================================
'''
에러 기록

1. 자동 번역 시:
	1) "정말 로퍼 Riali Loafer" 케이스. 
		=> 출발 언어를 '영어'로 고정하면 될까?
	2) "Dezi V 모카신 슬리퍼" 케이스.
		Dezi V도 한글로 번역이 돼야 하는데.

2. HTTP response를 파일로 만들 때, 파일명에 '/'가 들어가서 경로가 이상해지는 케이스

3. URL을 받아올 때, 형식이 'https://'로 시작하지 않는 케이스.


'''