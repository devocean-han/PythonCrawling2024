''' 
Asics(아식스) 추출자(Extractor)들을 모아놓은 모듈.
추출자는 공통적으로 HTTP 응답을 파싱한 soup 객체를 인자로 받아
추출 결과를 반환하는 행동(외부 버튼)이 하나씩 있음
'''

import json
from pprint import pprint
import logging

from extractors import extractors_interface as I
from strategy_decorator import export_strategy

logger = logging.getLogger('Asics.Extractors')
SITE_OFFICIAL = 'Asics'


@export_strategy(SITE_OFFICIAL)
class AsicsMetadataExtractor(I.MetadataExtractor):
    def __init__(self) -> None:
        self.meta_script_selectors = {
            'size_included_script': 'script:-soup-contains("utag_data")',
        }
        
    def get_metadata(self, soup) -> dict[str]:
        metadata = {}
        try:
            script_tag = soup.select_one(self.meta_script_selectors['size_included_script'])
            script_content = script_tag.string
            target_json = script_content.split(' = ')[1].strip(';\n\t')
            metadata = json.loads(target_json)
        except Exception as e:
            print(e)
            logger.error(e, exc_info=True)
            raise
        # 'product_name': ['GEL-CUMULUS 26']
        product_name = metadata['product_name'][0]
        # 'product_unit_price': ['140.00']
        price = metadata['product_unit_price'][0]
        # 'product_no_stock_sizes': '6|6.5',
        # 'product_sizes': ['6', '6.5', ... '15', '16']
        # 'product_sizes': ['K10', '1', '1.5', ...]
        sizes = metadata['product_sizes']
        sizes_out_of_stock = metadata['product_no_stock_sizes'].split('|')
        sizes = [size for size in sizes if size not in sizes_out_of_stock]

        # 'product_id': ['20053313.400'],
        # 'product_full_id': ['0020053313.400.S.6'],
        # 'product_gender': ['MEN'], # KIDS, UNISEX, WOMEN
        # 'product_color': ['400'],
        # 'product_style': ['ANA_1011B792'],
        # 'user_ip_address': '3.15.36.50',
        return metadata


@export_strategy(SITE_OFFICIAL)
class AsicsProductNameExtractor(I.ProductNameExtractor):
    def __init__(self) -> None:
        pass

    def get_product_name(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = AsicsMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            product_name = metadata['product_name'][0]
            return product_name
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class AsicsPriceExtractor(I.PriceExtractor):
    def __init__(self) -> None:
        pass

    def get_price(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = AsicsMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            price = metadata['product_unit_price'][0]
            return price
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class AsicsImagesExtractor(I.ImagesExtractor):
    def __init__(self) -> None:
        self.image_selectors = {
            'lis': 'ul.product-primary-image li', # 성공
            'lis_instock': 'ul.product-primary-image li:not([class*="slick-cloned"])', # lis와 같음
            'lis_not_cloned': 'ul.product-primary-image li:not(.slick-cloned)', # lis와 같음
            'imgs': 'ul.product-primary-image li img', # 성공
            'spans': 'ul.product-primary-image li span', # 성공 - 더 간단
        }

    def get_images(self, soup) -> list[str]:
        try:
            # 'imgs' 태그 셀렉터를 이용한 추출
            # img_tags = soup.select(self.image_selectors['imgs'])
            # images = [img['data-src'] if img.get('data-src') is not None else img['src'] for img in img_tags]
            # images = [img.replace('sfcc-product', 'zoom') for img in images]
            # 'spans' 태그 셀렉터를 이용한 추출
            span_tags = soup.select(self.image_selectors['spans'])
            images = [span['data-zoom-image'] for span in span_tags]
            return images
        except Exception as e:
            logger.error(e)
            return []    


@export_strategy(SITE_OFFICIAL)
class AsicsSizeOptionsExtractor(I.SizeOptionsExtractor):
    def __init__(self) -> None:
        pass

    def get_size_options(self, soup) -> list[str]:
        try:
            # 메타데이터에서 추출
            metadataExtractor = AsicsMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            sizes = metadata['product_sizes']
            sizes_out_of_stock = metadata['product_no_stock_sizes'].split('|')
            sizes = [size for size in sizes if size not in sizes_out_of_stock]
            return sizes
        except Exception as e:
            logger.error(e)
            return []


@export_strategy(SITE_OFFICIAL)
class AsicsSizeTypeExtractor(I.SizeTypeExtractor):
    def __init__(self) -> None:
        pass

    def get_size_type(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = AsicsMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            # 'product_gender': ['MEN'], # KIDS, UNISEX, WOMEN
            gender = metadata['product_gender'][0]
            return gender.lower()
        except Exception as e:
            logger.error(e)
            return ''


@export_strategy(SITE_OFFICIAL)
class AsicsSizeTransformer(I.SizeTransformer):
    def __init__(self) -> None:
        super().__init__()

    def trans_shoes_mens(self, size_list) -> list[str]:
        try:
            sizes_transformed = [self.size_tables['shoes']['mens'].get(float(size))
                for size in size_list]
            return [str(size) for size in sizes_transformed
                if size is not None]
        except Exception as e:
            logger.error(e, exc_info=True)
            return size_list
    
    def trans_shoes_womens(self, size_list) -> list[str]:
        try:
            sizes_transformed = [self.size_tables['shoes']['womens'].get(float(size))
                for size in size_list]
            return [str(size) for size in sizes_transformed
                if size is not None]
        except Exception as e:
            logger.error(e, exc_info=True)
            return size_list
    
    def trans_shoes_kids(self, size_list) -> list[str]:
        ''' 아식스는 아동 신발 사이즈에 'K'가 붙는 형식이므로
        ['kids'] 대신 ['kids_with_k']을, 숫자 대신 문자열 그대로 조회 '''
        try:
            sizes_transformed = [self.size_tables['shoes']['kids_with_k'].get(size)
                for size in size_list]
            return [str(size) for size in sizes_transformed
                if size is not None]
        except Exception as e:
            logger.error(e, exc_info=True)
            return size_list


@export_strategy(SITE_OFFICIAL)
class AsicsDescriptionsExtractor(I.DescriptionsExtractor):
    def __init__(self) -> None:
        self.description_selectors = {
            'detail_ps': 'div.product-info-section-inner p',
            'tech_lis': 'div.product-features-section li',
            'tech_fonts': 'div.product-features-section li font', # 실패: li 안에 실제로는 div밖에 (span이)없음
        }
    
    def get_descriptions(self, soup) -> list[list[str]]:
        try:
            # 0. Details 중 첫 번째만 title로, 나머지는 bullet으로 
            detail_p_tags = soup.select(self.description_selectors['detail_ps'])
            details = [p.text.strip() for p in detail_p_tags]
            title = details[0]
            bullets = details[1:]
            # 1. li 하나를 통째로 하나로
            tech_li_tags = soup.select(self.description_selectors['tech_lis'])
            # pprint(tech_li_tags)
            # print('\n\n')
            # techs = [li.text.strip().replace('\n', '').replace('\t', '') for li in tech_li_tags]
            # print(details)
            # print(techs)
            # print()
            # 2. li 따로, 내부 div도 따로
            # print(len(font_tags))
            # techs = [font.text.strip() for font in font_tags]
            tech_texts = [li.get_text(strip=True) for li in tech_li_tags]
            # TODO: .get_text(strip=True)는 <li><div>문장1</div>문장2</li> 형식에서, 문장1과 문장2가 띄어쓰기 없이 붙게 돼서 살짝 아쉬움. 고쳐볼 것.
            
            # pprint(tech_texts)
            bullets.extend(tech_texts)

            return [[title], bullets]
        except Exception as e:
            logger.error(e)
            return [[],[]]


# TODO: 색상명과 url 추출 가능(via 메타데이터)
class AsicsColorNameExtractor(I.ColorNameExtractor):
    def __init__(self) -> None:
        pass
    
    def get_color_name(self, soup) -> str:
        try:
            # 메타데이터에서 추출
            metadataExtractor = AsicsMetadataExtractor()
            metadata = metadataExtractor.get_metadata(soup)
            # "product_variant": ["Evening Teal/Bright Yellow"],
            color_name = metadata['product_variant'][0]
            return color_name
        except Exception as e:
            logger.error(e)
            return ''

@export_strategy(SITE_OFFICIAL)
class AsicsColorUrlsExtractor(I.ColorUrlsExtractor):
    # 'product_color': ['400'],
    # 'product_style': ['ANA_1011B792'],
    # => pid = ANA_1011B792-400
    # => https://www.asics.com/us/en-us/p/{pid}.html
    def __init__(self) -> None:
        self.color_urls_selectors = {
            'direct_as': 'li.variants__item--color:not([aria-checked="true"]) a', # 성공: '현재 색상' 제외
            'lis': 'li.variants__item--color:not([aria-checked="true"]', 
            'direct_as2': 'li.variants__item--color > a', # 이게 안 되면
        }

    def get_color_urls(self, soup) -> list[str]:
        try:
            # # 메타데이터에서 추출
            # metadataExtractor = AsicsMetadataExtractor()
            # metadata = metadataExtractor.get_metadata(soup)
            # product_style = metadata['product_style'][0]
            # color_id = metadata['product_color'][0]
            # pid = f'{product_style}-{color_id}'
            # url = f'https://www.asics.com/us/en-us/p/{pid}.html'
            
            # 어차피 링크는 색상 링크에서 추출해야 함
            a_tags = soup.select(self.color_urls_selectors['direct_as'])
            # 링크 = a['href']
            color_urls = [a['href'] for a in a_tags]            
            # 색상명 = a['title'] # "Select Color: Sheet Rock/Concrete"
            # li에서라면 색상명 = li['data-sizevalue']
            return color_urls
        except Exception as e:
            logger.error(e)
            return []


# .venv\Scripts\activate
# 여기까지는 "on demandware" url을 알아냈는데, 요청도 잘 가는데, 응답이 application/json이 아님:
# => https://www.asics.com/on/demandware.store/Sites-asics-us-Site/en_US/Product-Variation?pid=ANA_1011B792-020&dwvar_ANA__1011B792-020_color=ANA_1011B792%2e020&dwvar_ANA__1011B792-020_width=Standard
# => 최종 시도 url: https://www.asics.com/on/demandware.store/Sites-asics-us-Site/en_US/Product-Variation?pid=ANA_1011B792-002
        

# pid = 'ANA_1011B792'
# "product_id": [
#     "20053313.400"
# ],
# "product_full_id": [
#     "0020053313.400.S.6"
# ],
# "product_name": [
#     "GEL-CUMULUS 26"
# ],
# "product_color": [
#     "400"
# ],"
# api = '''https://p.cquotient.com/pebble?
# tla=bbtn-asics-us&
# activityType=viewProduct&
# callback=CQuotient._act_callback0&
# cookieId=abPF0XUa5afLGz5zmoYopBLQOX&
# userId=&
# emailId=&
# product=id%3A%3AANA_1011B792%7C%7Csku%3A%3A%7C%7Ctype%3A%3Avgroup%7C%7Calt_id%3A%3AANA_1011B792-400&
# realm=BBTN&
# siteId=asics-us&
# instanceType=prd&
# locale=en_US&
# referrer=https%3A%2F%2Fwww.asics.com%2Fus%2Fen-us%2Fmens-running-shoes%2Fc%2Faa10201000%2F&
# currentLocation=https%3A%2F%2Fwww.asics.com%2Fus%2Fen-us%2Fgel-cumulus-26%2Fp%2FANA_1011B792-400.html&
# ls=true&
# _=1709596643011&
# v=v3.1.0&
# fbPixelId=__UNKNOWN__&
# json=%7B%22cookieId%22%3A%22abPF0XUa5afLGz5zmoYopBLQOX%22%2C%22userId%22%3A%22%22%2C%22emailId%22%3A%22%22%2C%22product%22%3A%7B%22id%22%3A%22ANA_1011B792%22%2C%22sku%22%3A%22%22%2C%22type%22%3A%22vgroup%22%2C%22alt_id%22%3A%22ANA_1011B792-400%22%7D%2C%22realm%22%3A%22BBTN%22%2C%22siteId%22%3A%22asics-us%22%2C%22instanceType%22%3A%22prd%22%2C%22locale%22%3A%22en_US%22%2C%22referrer%22%3A%22https%3A%2F%2Fwww.asics.com%2Fus%2Fen-us%2Fmens-running-shoes%2Fc%2Faa10201000%2F%22%2C%22currentLocation%22%3A%22https%3A%2F%2Fwww.asics.com%2Fus%2Fen-us%2Fgel-cumulus-26%2Fp%2FANA_1011B792-400.html%22%2C%22ls%22%3Atrue%2C%22_%22%3A1709596643011%2C%22v%22%3A%22v3.1.0%22%2C%22fbPixelId%22%3A%22__UNKNOWN__%22%7D'''
# json = {"cookieId":"abPF0XUa5afLGz5zmoYopBLQOX","userId":"","emailId":"","product":{"id":"ANA_1011B792","sku":"","type":"vgroup","alt_id":"ANA_1011B792-400"},"realm":"BBTN","siteId":"asics-us","instanceType":"prd","locale":"en_US","referrer":"https://www.asics.com/us/en-us/mens-running-shoes/c/aa10201000/","currentLocation":"https://www.asics.com/us/en-us/gel-cumulus-26/p/ANA_1011B792-400.html","ls":True,"_":1709596643011,"v":"v3.1.0","fbPixelId":"__UNKNOWN__"}
