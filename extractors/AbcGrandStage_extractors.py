''' 
ABC Mart Grand Stage(에이비씨 마트 그랜드 스테이지)의 
추출자(Extractor)들을 모아놓은 모듈.
- 브랜드 Nike(나이키)를 기준으로 우선 작업함.
- 상품명(영한), 가격, 이미지, 사이즈, 상세설명 -> 셀레니움 필요,
메타데이터(script 태그) 추출도 불가능
- 셀레니움을 사용하므로 자동으로 IP 우회 안 함(국내 사이트라서 IP 우회 안하면 좋음)
'''

import json
from pprint import pprint
import logging

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('AbcGrandStage.Extractors')
SITE_OFFICIAL = 'AbcGrandStage'


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageProductNameKoreanExtractor(I.ProductNameKoreanExtractor):
	def __init__(self) -> None:
		self.product_name_selectors = {
			'kor_div': 'div.detail-box-header div.prod-name', 
			# 상품정보제공 공시 중 '소재' 부분:
			'material_td': 'tbody#product-detail-notice td', # tbody의 자식 중 첫 번째 td가 무조건 '소재'일 것이라 가정
		}

	def get_product_name(self, soup) -> str:
		try:
			# 공식 한글 상품명 추출
			div_tag = soup.select_one(self.product_name_selectors['kor_div'])
			product_name_ko = div_tag.text.strip()
			# 소재 추출
			material_td = soup.select_one(self.product_name_selectors['material_td'])
			material_ko = material_td.text.strip()
			return product_name_ko + ' ' + material_ko
		except Exception as e:
			logger.error(e)
			return ''


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageProductNameExtractor(I.ProductNameExtractor):
	def __init__(self) -> None:
		self.product_name_selector = {
			'div': 'div.detail-box-header div.prod-name-en', 
		}

	def get_product_name(self, soup) -> str:
		try:
			# 공식 영문 상품명 추출
			div_tag = soup.select_one(self.product_name_selector['div'])
			product_name = div_tag.text
			return product_name
		except Exception as e:
			logger.error(e)
			return ''


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageBrandNameExtractor(I.BrandNameExtractor):
	def __init__(self) -> None:
		self.brand_name_selector = 'div.detail-box-header input#brandName'
	
	def get_brand_name(self, soup) -> str:
		''' Abc Grand Stage는 한국 사이트이므로 특별히 '한글' 브랜드명을 반환 '''
		try:
			brand_name = soup.select_one(self.brand_name_selector).get('value').strip()
			return brand_name
		except Exception as e:
			logger.error(e)
			return ''


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStagePriceExtractor(I.PriceExtractor):
	def __init__(self) -> None:
		self.standard_selectors = {
			'span': 'div.detail-box-header span[data-product="normal-price-amount"]',
		}

	def get_price(self, soup) -> str:
		''' Abc Grand Stage는 영구 할인가인지 추측할 수 없음을 전제로, 
		무조건 기본 정가로 추출함 '''
		try:
			span_tag = soup.select_one(self.standard_selectors['span'])
			price = span_tag.text
			return price
		except Exception as e:
			logger.error(e)
			return ''


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageImagesExtractor(I.ImagesExtractor):
	def __init__(self) -> None:
		self.image_selectors = {
			'imgs': 'div.product-detail-box ul.detail-thumbs-list img', # 성공
		}

	def get_images(self, soup) -> list[str]:
		try:
			# 추출되는 사이즈: 1200x1200 px 
			img_tags = soup.select(self.image_selectors['imgs'])
			images = [img['src'].split('?')[0] for img in img_tags]
			return images
		except Exception as e:
			logger.error(e)
			return []    


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageSizeOptionsExtractor(I.SizeOptionsExtractor):
	def __init__(self) -> None:
		self.size_options_selectors = {
			'buttons': 'div.product-detail-box button.btn-prod-size:not(.sold-out)', # 품절 아닌 사이즈
		}        

	def get_size_options(self, soup) -> list[str]:
		try:
			button_tags = soup.select(self.size_options_selectors['buttons'])
			sizes = [button.text for button in button_tags]
			return sizes
		except Exception as e:
			logger.error(e)
			return []


# 셀레니움 html에서 추출
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageDescriptionImagesExtractor(I.DescriptionImagesExtractor):
	def __init__(self) -> None:
		self.description_images_selectors = {
			'detail_div_img': 'div#product-detail-description-wrapper img', # 통짜 이미지 하나(혹은 여럿)
		}
	
	def get_description_images(self, soup):
		try:
			# 통짜로 된 900 x 2740 px 이미지를 추출 
			# (나이키: 900x900이미지가 20px 간격으로 여럿 붙은 통짜 이미지) 
			# (디스커버리: 1200x950이미지가 20px 간격으로 여럿 붙은 통짜 이미지) 
			# -> 상단에 착장 이미지 추가로 있을 수 있음(다른 이미지 파일로)
			detail_div_img = soup.select(self.description_images_selectors['detail_div_img'])
			detail_images = [img.get('src') for img in detail_div_img]
			return detail_images
		except Exception as e:
			logger.error(e)
			return []


# 셀레니움 html에서 추출
# TODO: 옷의 경우 '사이즈 변환표'를, 모자 같은 경우 '치수' 항목을 가져와야만 할 것 같은데...
# '사이즈 변환표'의 경우 방법; 
# '치수'의 경우 방법: 추가하기 방법. 뭐가 있을지 전부 짐작해야 추가할 수 있다는 단점이 있음
# 	=> 상품정보제공 고시에서 항목을 전부 가져오고, 그 중 [소재, 치수/굽높이, 제조자, 제조국, 소재별 관리방법, ]이면 통과시킨다
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageDescriptionsExtractor(I.DescriptionsExtractor):
	def __init__(self) -> None:
		self.description_selectors = {
			'spans_and_strongs': 'div#product-detail-description-wrapper span, div#product-detail-description-wrapper strong', # 1. (실패) wrapper 내의 span과 strong 태그 전부
			'direct_parent_div': 'div#product-detail-description-wrapper > div > div',
			'detail_div_direct_children': 'div#product-detail-description-wrapper > div > div > *', # 3. 성공
			'detail_div_test': 'div#product-detail-description-wrapper > * > * > span, div#product-detail-description-wrapper > * > * > strong', # 4. 성공
			'detail_div': 'div#product-detail-description-wrapper', # 5. 성공, 채택(가장 확고한 방법임)
			}
	
	def get_descriptions(self, soup) -> list[list[str]]:
		try:
			# 1. (실패)css로 span과 strong 선택하기(중복 발생)
			# span_strong_tags = soup.select(self.description_selectors['spans_and_strongs'])
			# pprint(span_strong_tags)
			# print()
			# pprint([tag.text for tag in span_strong_tags])
			# print()

			# 2. (실패)직계 부모 div 먼저 선택하고 findChildren으로 선택하기(한 번에 한 종류 태그밖에 선택하지 못하여, 여전히 중복 발생)
			# span_strong_tags = soup.select_one(self.description_selectors['direct_parent_div'])
			# strongs = span_strong_tags.findChildren('strong', recursive=False) # 직계 자식만 검색
			# spans = span_strong_tags.findChildren('span', recursive=False) # 직계 자식만 검색
			# # pprint(span_strong_tags)
			# print([tag.text for tag in strongs])
			# print()
			# print([tag.text for tag in spans])
			# print()

			# 3. (성공)직게 부모 div의 직계 자식들 전부 추출 후 text가 없는 태그 요소는 삭제하기
			# children = soup.select(self.description_selectors['detail_div_direct_children'])
			# valid_texts = [tag.text for tag in children if tag.text.strip() != '']
			# for text in valid_texts:
			# 	print('=============')
			# 	print(text)
			# print()
			# title = valid_texts[0]
			# bullets = valid_texts[1:]

			# 4. (성공)큰 div의 정확히 3번째 자손인 span과 strong 선택하기
			# span_strong_tags = soup.select(self.description_selectors['detail_div_test'])
			# valid_texts = [tag.text for tag in span_strong_tags if tag.text.strip() != '']
			# for tag in valid_texts:
			# 	print('--------')
			# 	print(tag.text)
			# print()
			# title = valid_texts[0]
			# bullets = valid_texts[1:]

			# 5. (성공)find_all(text=True)로 텍스트가 있는 자손 태그 선택하기 (다만 한 줄씩 분리되어 list됨)
			detail_div = soup.select_one(self.description_selectors['detail_div'])
			text_children = detail_div.find_all(text=True)
			valid_texts = [text for text in text_children if text.strip() != ''] # '\n'인 태그 제거
			# for text in valid_texts:
			# 	print('---------')
			# 	print(text)
			# print()
			title = valid_texts[0]
			bullets = valid_texts[1:]

			return [[title], bullets]
		except Exception as e:
			logger.error(e)
			return [[],[]]


# 셀레니움 html에서 추출
# TODO: 패밀리로 엮인 색상마다 다른 색상 패밀리를 갖는 문제 해결하기
# 	(원래는 오리지널 링크 하나로만 색상url을 검색하고, 
# 	 파생된 링크에서는 따로 색상url을 추출하지 않음)
'''
방법1: 구글시트 열 하나에 ABC전용 상품 코드를 입력하고 새롭게 url를 추출할 때마다
	url에서 상품코드를 분리하여 현재 시트에 이미 존재하는 번호인지 검색
	- 장: 프로그램 실행을 여러번 해도 뭘 이미 추출했는지 기억할 수 있다,
	- 단: 복잡하고 시간이 오래 걸릴 것이다.
	
방법2: 현재 실행중인 url과 추출한 컬러url들의 상품 코드만 기억하도록 한다.
	원본url을 추출하고(상품코드 저장됨) 컬러url 1,2를 뽑아냄. [컬러1, 컬러2]
	컬러1로 갔는데 원본url,컬러2뿐만 아니라 컬러11, 컬러12도 있음 
	여기서도 컬러url을 추출, 대기url 리스트에 저장. [컬러2, 원본, 컬러2, 컬러11, 컬러12]
	다음 순서로, 컬러2로 갔더니 컬러1만 존재, 이 url만 추출 저장됨. [원본, 컬러2, 컬러11, 컬러12, 컬러1]
	원본url을 다시 하려고 보니 이미 상품코드 존재. 
	그러면 원본url은 패스하고, 컬러2도 마찬가지로 추출 들어가기 전 패스. [컬러11, 컬러12, 컬러1]
	컬러11을 들어가니, 본인을 뺀 다섯 url이 전부 있음. 다시 url 저장. [컬러12, 컬러1 | 컬러12, 컬러1, 컬러2, 원본]
	컬러12를 추출하고 마찬가지로 본인 제외 다섯 url을 추가. [컬러1 | 컬러12, 컬러1, 컬러2, 원본 | 원본, 컬러1, 컬러2, 컬러11]
	이후로 대기열의 모든 url은 '이미 추출한 상품코드' 리스트에 전부 들어있음. 
	추출하러 들어가지 않으니 컬러url도 더이상 추가되지 않음. 
	대기url이 다 비고 루프가 끝나게 됨. 

	-> 근데 이런식이면 컬러url 자체를 추출할 때 상품코드 기준으로 set에 저장하면 되잖아?
	어차피 대기url을 순회할 때 지나간 요소를 제거해버리는 식이 아니니까,
	굳이 '이미 추출한 상품코드'와 '대기중인 url(상품코드)'를 분리해서 생각할 게 아니라 
	순회도 set을, 추출한 컬러url을 저장할 때 중복확인도 set을 하면 되지 않을까...
	- 장: 코드 작성과 실행 복잡도가 간단하다. 
	- 단: 프로그램을 실행할 때마다 뭘 했었는지 기억하지 못한다.

만약 방법1을 쓰게 된다면 방법2의 set 이용에 더해, 실제로 '추출 완료한 상품코드' 리스트를 
만들어 사용할 필요가 있다. 구글시트에서 읽어들인 모든 상품코드를 미리 '추출 완료한 상품코드' 
리스트에 넣어두고, 새롭게 추출한 컬러url이 대기열에 추가될지 여부를 '추출 완료한 상품코드' 
리스트와 추출 예정인 bulk 리스트 모두과 중복을 체크하여 결정하도록 한다. 

다만 실시간으로	추가되는 추출 결과 행에 대해서는, 시트에서 상품코드를 가져올건지 프로그램 
내부에서 추가하도록 할 건지	결정...해야 할 텐데 그냥 프로그램 내부에서 추가하도록 하자. 

추출 예정인 bulk리스트가 매번 변하더라도, 추출 완료한 상품코드 리스트는 배치마다 비우지 
않을 것이므로 한 번의 프로그램 실행중에는 괜찮을 것이고, 프로그램을 다시 시작하는 경우엔 
정확히 추출 완료한 상품코드만 시트에서 새롭게 읽어올 것이기 때문에 데이터가 정확할 것이다. 
따라서 문제 없음.
'''

''' 정리:
방법0(현재): 그냥 원본 url에서 추출한 컬러url만 추가로 순회함
방법2: 프로그램 실행중에만 기억하는, 대기url Set만 이용하는 방법
	(근데 ABC만 어떻게 다르게 만들 것인가, 다른 사이트 전부 이렇게 만들 것인가?)
방법1: 방법2에 추가적으로 프로그램 시작 시에 한 번 구글 시트를 읽어오고,
	대기url Set 뿐만 아니라 추출 완료한 상품코드 Set도 따로 운용하는 방법
'''
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageColorUrlsExtractor(I.ColorUrlsExtractor):
	# 다른 컬러 링크 태그: <a href="/product?prdtNo=1020101719"> 
	# => https://grandstage.a-rt.com{href}
	# => https://grandstage.a-rt.com/product?prdtNo=1020101719
	def __init__(self) -> None:
		self.color_urls_selectors = {
			'as': 'ul.style-color-list a',
		}

	def get_color_urls(self, soup) -> list[str]:
		try:
			a_tags = soup.select(self.color_urls_selectors['as'])
			color_urls = ['https://grandstage.a-rt.com' + a['href'] for a in a_tags]
			return color_urls
		except Exception as e:
			logger.error(e)
			return []


# TODO: 직접 테스트 실행 떄는 안 됐는데, 디버깅으로 실행하니 셀레니움 잘 실행되어 html이 잘 저장됨. 확인 필요
@export_strategy(SITE_OFFICIAL)
class AbcGrandStageSeleniumWaitSelectors(I.SeleniumWaitSelectors):
	def __init__(self) -> None:
		''' AbcGrandStage는 모든 항목(상품명, 가격, 이미지, 사이즈, 상세설명)을 셀레니어로 그리고 가져와야 하므로, '타겟 태그 요소'를 그 중 가장 로딩이 늦는 사이즈 버튼 태그로 타겟팅함
		=> 혹은, 이것과 저것 모두가 로딩된 걸 체크하는 방법 도입하기
		1. 일단 사이즈 버튼 태그를 타겟팅함
		2. 이후 '모둔 사이즈 버튼'과 '상세설명 이미지'와 '대표 이미지' 모두를 확인하는 것으로 수정하기
		'''
		self.css_selectors_with_target_as_last_element = ['button.btn-prod-size']
	
	def get_selectors(self) -> list[str]:
		return self.css_selectors_with_target_as_last_element

