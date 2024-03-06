''' 
Adidas(아디다스) 추출자(Extractor)들을 모아놓은 모듈.
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''

import json
from pprint import pprint
import logging

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('Adidas.Extractors')
SITE_OFFICIAL = 'Adidas'


@export_strategy(SITE_OFFICIAL)
class AdidasProductNameExtractor(I.ProductNameExtractor):
    def __init__(self) -> None:
        self.product_name_selector = 'h1[data-auto-id="product-title"]'
        
    def get_product_name(self, soup) -> str:
        try:
            product_name = soup.select_one(self.product_name_selector).text
            return product_name
        except Exception as e:
            logger.error(e, exc_info=True)
            return ''


@export_strategy(SITE_OFFICIAL)
class AdidasPriceExtractor(I.PriceExtractor):
    def __init__(self) -> None:
        self.price_selectors = {
            'sale_div': 'div.gl-price-item--sale',
            'outer_price_div': 'div[data-auto-id="gl-price-item"]',
        }
    
    def get_price(self, soup) -> str:
        try:
            sale_div_tag = soup.select_one(self.price_selectors['sale_div'])
            if sale_div_tag:
                return sale_div_tag.text
            else:
                standard_outer_div_tag = soup.select_one(self.price_selectors['outer_price_div'])
                return standard_outer_div_tag.text
        except Exception as e:
            logger.error(e, exc_info=True)
            return ''


# '더보기'를 클릭하기 전의 디폴트 4개만 가능 -> 메타데이터로 전체 추출 가능
@export_strategy(SITE_OFFICIAL)
class AdidasImagesExtractor(I.ImagesExtractor):
    def __init__(self) -> None:
        self.image_selectors = {
            'imgs': 'div#pdp-gallery-desktop-grid-container img',
        }
    
    def get_images(self, soup) -> list[str]:
        try:
            metadata_extractor = AdidasMetadataExtractor()
            metadata = metadata_extractor.get_metadata(soup)
            view_list = metadata['queries'][0]['state']['data']['view_list']
            img_urls = [item['image_url'] for item in view_list]
            img_urls = [url.replace('w_600', 'w_1400') for url in img_urls]
            return img_urls
        except Exception as e:
            logger.error(e, exc_info=True)
            return []
        

# 사이즈: 메타데이터로만 추출 가능 -> 품절 여부 정보는 셀레니움으로만 추출 가능
@export_strategy(SITE_OFFICIAL)
class AdidasSizeOptionsExtractor(I.SizeOptionsExtractor):
    def __init__(self) -> None:
        self.size_options_selectors = {
            'buttons': 'div.size-selector___2kfnl button', # 실패
            'outer_div': 'div.size-selector___2kfnl', # 실패
            'button_divs': 'div.size___2lbev', # 실패
            'instock_buttons': 'button.size___2lbev:not([class*="unavailable"])',
        }

    def get_size_options(self, soup) -> list[str]:
        try:
            buttons = soup.select(self.size_options_selectors['instock_buttons'])
            instock_sizes = [button.text.strip() for button in buttons]
            # 성인 신발 중 'M 6.5 / W 7.5' 같은 경우 '6.5'와 같이 남자 걸로 추출하고, 
            # 키즈의 경우 '13.5K'와 같이 K를 그대로 붙여서 반환함
            instock_sizes = [size.split('/')[0].replace('M', '').strip() 
                                if '/' in size else size for size in instock_sizes]
            return instock_sizes
        except Exception as e:
            logger.error(e, exc_info=True)
            return []


@export_strategy(SITE_OFFICIAL)
class AdidasSizeTransformer(I.SizeTransformer):
    def __init__(self) -> None:
        super().__init__()

    def trans_shoes_mens(self, size_list) -> list[str]:
        try:
            return [str(self.size_tables['shoes']['mens'][float(size)]) 
                    for size in size_list
                    if float(size) in self.size_tables['shoes']['mens']]
        except Exception as e:
            logger.error(e, exc_info=True)
            return size_list
    def trans_shoes_womens(self, size_list) -> list[str]:
        try:
            return [str(self.size_tables['shoes']['womens'][float(size)]) 
                    for size in size_list
                    if float(size) in self.size_tables['shoes']['womens']]
        except Exception as e:
            logger.error(e, exc_info=True)
            return size_list
    def trans_shoes_kids(self, size_list) -> list[str]:
        ''' kids_with_k 테이블을 이용, 'K'가 붙은 문자열 그대로 사이즈 변환 '''
        try:
            return [str(self.size_tables['shoes']['kids_with_k'][size]) 
                    for size in size_list
                    if size in self.size_tables['shoes']['kids_with_k']]
        except Exception as e:
            logger.error(e, exc_info=True)
            print(e)
            return size_list


# 상세설명: 메타데이터로만 추출 가능
@export_strategy(SITE_OFFICIAL)
class AdidasDescriptionsExtractor(I.DescriptionsExtractor):
    def __init__(self) -> None:
        self.description_selectors = {
            'title_h3': 'div#navigation-target-description h3', # 실패
            'title_div': 'div#navigation-target-description', # 실패
            'any_description': ':-soup-contains("Spikeless golf shoes made in part with recycled materials.")', # 실패
        }
    
    def get_descriptions(self, soup) -> list[list[str]]:
        try: 
            metadata_extractor = AdidasMetadataExtractor()
            metadata = metadata_extractor.get_metadata(soup)
            descriptions = metadata['queries'][0]['state']['data']['product_description']
            title = descriptions['subtitle']
            title_sentence = descriptions['text']
            bullets = descriptions['usps']
            return [[title], [title_sentence] + bullets]
        except Exception as e:
            logger.error(e, exc_info=True)
            return [[],[]]


@export_strategy(SITE_OFFICIAL)
class AdidasMetadataExtractor(I.MetadataExtractor):
    def __init__(self):
        self.meta_script_selectors = {
            's1': 'script:-soup-contains("window.DATA_STORE")',
            's2': 'script:-soup-contains("window.REACT_QUERY_DATA")',
        }
    def get_metadata(self, soup):
        # ## for 's1'
        # script_tag = soup.select(self.meta_script_selectors['s1'])[0]
        # script_content = script_tag.string
        # target_json = script_content.split('JSON.parse(')[1].strip(');')
        # metadata = json.loads(json.loads(target_json))
        # pprint(list(metadata['app'].keys())[10:30])

        # for 's2'
        script_tag = soup.select(self.meta_script_selectors['s2'])[0]
        script_content = script_tag.string
        script_content_formatted = script_content.split('REACT_QUERY_DATA = ')[1].strip(');\n')
        metadata = json.loads(script_content_formatted)
        
        # ## images:
        # view_list = metadata['queries'][0]['state']['data']['view_list']
        # img_urls = [item['image_url'] for item in view_list]
        # img_urls = [url.replace('w_600', 'w_1400') for url in img_urls]

        # ## sizes:
        # size_list = metadata['queries'][0]['state']['data']['variation_list']
        # sizes = [item['size'] for item in size_list]
        # ## price:
        # pricing_information = metadata['queries'][0]['state']['data']['pricing_information']
        # current_price = pricing_information['currentPrice']
        # sale_price = pricing_information.get('sale_price')
        # standard_price = pricing_information['standard_price']
        
        # ## descriptions:
        # descriptions = metadata['queries'][0]['state']['data']['product_description']
        # title = descriptions['subtitle']
        # title_sentence = descriptions['text']
        # bullets = descriptions['usps']
        
        # ## size type:
        # attributes = metadata['queries'][0]['state']['data']['attribute_list']
        # gender = attributes.get('gender') # 'M','W','U'
        # kids의 경우: 
        # kids_type = attributes['age'] # ['Infant & Toddler']
        # gender = attributes.get('gender') # 'K'
        # gender_sub = attributes.get('gender_sub') # "Kids Unisex"
        # print('gender: ', gender) # M, W, U, K

        # pprint(metadata)
        return metadata


@export_strategy(SITE_OFFICIAL)
class AdidasSeleniumWaitSelectors(I.SeleniumWaitSelectors):
    def __init__(self) -> None:
        ''' 아디다스의 '타겟 태그 요소'는 사이즈 버튼 태그임 '''
        self.css_selectors_with_target_as_last_element = ['button.size___2lbev']
    
    def get_selectors(self) -> list[str]:
        return self.css_selectors_with_target_as_last_element