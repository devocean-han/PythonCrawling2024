'''
North Face Korea(노스페이스 코리아) 추출자들을 모아놓은 모듈. 
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''

import json
from pprint import pprint
import logging
from bs4 import BeautifulSoup as bs

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('NorthFaceKorea.Extractors')
SITE_OFFICIAL = 'NorthFaceKorea'


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaMetadataExtractor(I.MetadataExtractor):
    def __init__(self) -> None:
        self.meta_selectors = {
            'size_included_div': 'div.product-information.fixit-container',
        }
        
    def get_metadata(self, soup) -> dict[str]:
        metadata = {}
        try:
            div_tag = soup.select_one(self.meta_selectors['size_included_div'])
            
            # 상품 ID
            product_id_num = div_tag["data-product-id"]
            privateId = 'NS91Q03C'

            # 가격
            sku_data = json.loads(div_tag["data-sku-data"])
            price = sku_data[0]['price'] # '170,100 원'

            # 색상 id와 이름:
            data_product_options = json.loads(div_tag["data-product-options"])
            color_id, color_name = next(iter(data_product_options[0]["values"].items())) # { "284": "LIGHT_KHAKI" }
            # color_id = data_product_options[0] ["allowsValues"][0]["id"] # "284"
            # color_name = data_product_options[0]["allowsValues"][0]["friendly-name"] # "LIGHT_KHAKI"

            # 사이즈 코드-실측 표
            # size_code_mm_table = data_product_options[1]["values"] 
            allowedValues = data_product_options[1]["allowedValues"]
            size_code_mm_table = {str(el['id']): el['friendlyName'] for el in allowedValues} 
            # pprint(size_code_mm_table) # {'543': '230MM', ...}
            
            # 사이즈 재고:
            sizes_quantity_all = {size_code_mm_table[str(item["selectedOptions"][1])]: item["quantity"] for item in sku_data}
            sizes_instock = [size.replace('MM', '') for size in sizes_quantity_all if sizes_quantity_all[size] != 0]
            sizes_quantity_instock = {size: quantity for size, quantity in sizes_quantity_all.items() if quantity != 0}

            metadata = {
                "product_id_num": product_id_num,
                "price": price,
                "color_id": color_id,
                "color_name": color_name,
                "sizes_instock": sizes_instock,
                "sizes_quantity_instock": sizes_quantity_instock,
                "sizes_quantity_all": sizes_quantity_all,
            }

            # _GLOBAL.MARKETING_DATA()
            # 이걸 콘솔에서 하듯이 동적으로 가져올 수 있으면 위의 모든 정보에 더하여 이미지urls, 한&영 상품명까지 한 방에 가능한데... 아쉽아쉽

        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            raise

        return metadata


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaProductNameKoreanExtractor(I.ProductNameKoreanExtractor):
    def __init__(self) -> None:
        self.product_name_selectors = {
            # "data-kor-name" 속성을 가진 span 태그 선택
            'kor_name_span': 'span[data-kor-name]', 
        }

    def get_product_name(self, soup) -> str:
        try:
            # 공식 한글 상품명 추출
            span_tag = soup.select_one(self.product_name_selectors['kor_name_span'])
            product_name_ko = span_tag['data-kor-name']
            return product_name_ko
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaProductNameExtractor(I.ProductNameExtractor):
    def __init__(self) -> None:
        self.product_name_selectors = {
            'h1': 'h1.product-name', 
        }

    def get_product_name(self, soup) -> str:
        try:
            # 공식 영문 상품명 추출
            product_name = soup.select_one(self.product_name_selectors['h1']).text
            return product_name
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaPriceExtractor(I.PriceExtractor):
    def __init__(self) -> None:
        pass

    def get_price(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = NorthFaceKoreaMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            price = metadata['price'].replace(' 원', '').replace(',', '')
            return price
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaImagesExtractor(I.ImagesExtractor):
    def __init__(self) -> None:
        self.image_selectors = {
            'imgs_all': 'img', 
            'imgs_thumb': 'li.thumb-list img',
        }

    def get_images(self, soup) -> list[str]:
        try:
            # 'imgs' 태그 셀렉터를 이용한 추출
            img_tags = soup.select(self.image_selectors['imgs_thumb'])
            images = [img.get('src') for img in img_tags]
            images = [src.replace('?thumbnail', '') for src in images]
            return images
        except Exception as e:
            logger.error(e)
            return []    


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaSizeOptionsExtractor(I.SizeOptionsExtractor):
    def __init__(self) -> None:
        pass

    def get_size_options(self, soup) -> list[str]:
        try:
            # 메타데이터에서 추출
            metadataExtractor = NorthFaceKoreaMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            sizes = metadata['sizes_instock']
            # 의류의 경우, [085WS, 095M] 같이 'W'가 붙은 것은 '여성 S'로, 안 붙은 것들은 그냥 'S'로 변환함
            sizes = [size.split('(')[1].replace(')', '').replace('W', '여성')
                        if '(' in size else size for size in sizes]
            return sizes
        except Exception as e:
            logger.error(e)
            return []


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaDescriptionImagesExtractor(I.DescriptionImagesExtractor):
    def __init__(self) -> None:
        self.description_images_selectors = {
            'tech_imgs': 'div#product-info div.pdp-details-content div.product-tags:first-of-type img', # 실패. 돼야 하는데 왜 안되는지 모르겠음
            'tech_div': 'div#product-info div.pdp-details-content div.product-tags', # (성공)첫 요소만 선택할 것
            'size_imgs': 'div#product-size div.display-small-only img',
        }
    
    def get_description_images(self, soup):
        try:
            # 테크놀러지 섹션 이미지 추출 
            tech_div = soup.select_one(self.description_images_selectors['tech_div'])
            # 테크놀러지 섹션이 생략된 경우: 이미지 추출도 생략함
            section_title = tech_div.select_one('h3.section-title').text
            if section_title == '테크놀러지': 
                tech_img_tags = tech_div.select('img')
                tech_images = [img.get('src') for img in tech_img_tags]
            else:
                tech_images = []
            # 가로형, 세로형 중 세로형 사이즈 설명 이미지 전체를 추출 
            size_description_imgs = soup.select(self.description_images_selectors['size_imgs'])
            size_images = [img.get('src') for img in size_description_imgs]

            return tech_images + size_images
        except Exception as e:
            logger.error(e)
            return []


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaDescriptionsExtractor(I.DescriptionsExtractor):
    def __init__(self) -> None:
        self.description_selectors = {
            'p': 'div#product-info div.display-small-up p',
        }
    
    def get_descriptions(self, soup) -> list[list[str]]:
        try:
            # Details 중 첫 번째만 title로, 나머지는 bullet으로 
            detail_p_tag = soup.select_one(self.description_selectors['p'])
            detail = detail_p_tag.get_text(separator='<br/>', strip=True)
            details = detail.split('<br/>')

            title = details[0]
            bullets = details[1:]            
            return [[title], bullets]
        except Exception as e:
            logger.error(e)
            return [[],[]]


# TODO: 색상명과 url 추출 가능(via 메타데이터)
# @export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaColorNameExtractor(I.ColorNameExtractor):
    def __init__(self) -> None:
        pass
    
    def get_color_name(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = NorthFaceKoreaMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            # "product_variant": ["Evening Teal/Bright Yellow"],
            color_name = ' '.join(metadata['color_name'].split('_'))
            return color_name
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class NorthFaceKoreaColorUrlsExtractor(I.ColorUrlsExtractor):
    def __init__(self) -> None:
        self.color_urls_selectors = {
            'outer_div': 'div.product-option_radio.selector-color', # 첫 번째 것으로
        }

    def get_color_urls(self, soup) -> list[str]:
        try:
            outer_div = soup.select_one(self.color_urls_selectors['outer_div'])
            color_as = outer_div.select('div.variation-color.selectable:not(.selected) a')
            color_urls = ['https://www.thenorthfacekorea.co.kr' + a.get('href') for a in color_as]
            return color_urls
        except Exception as e:
            logger.error(e)
            return []

