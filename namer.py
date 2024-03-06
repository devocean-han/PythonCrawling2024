# from importlib import import_module
'''
#^ 사이트 하나를 더할 때마다 해야할 작업:
Namer의
    1) site_name_ko_to_official_table에 한-영 사이트명 쌍 추가
    2) site_name_to_IP_host_table에 사이트명-호스트 쌍 추가
'''

class Namer:
    ''' 사이트명에 대한 모든 테이블, 동작 모음 '''
    # 40개 사이트의 공식 한글->영문 사이트명 목록
    site_name_ko_to_official_table = {
        '자포스': 'Zappos',
        '휠라': 'Fila',
        '반스': 'Vans',
        '라코스테': 'Lacoste',
        '아디다스': 'Adidas',

        '크록스': 'Crocs',
        '노스페이스': 'North Face',
        '콜롬비아': 'Columbia',
        '살로몬': 'Salomon',
        '아식스': 'Asics',
        '호카': 'Hoka',
        '퓨마': 'Puma',

        '리복': 'Reebok',
        '타미힐피거': 'Tommy Hilfiger',
        '락포트': 'Rockport',
        '캘빈클라인': 'Calvin Klein',
        '게스': 'Guess',
        '랄프로렌': 'Ralph Lauren',

        '파타고니아': 'Patagonia',
        '메이시스': 'Macys',
        '갭': 'Gap',
        '갭팩토리': 'Gap Factory',
        '게스팩토리': 'Guess Factory',

        '스케쳐스': 'Skechers',
        '클락스': 'Clarks',
        '팀버랜드': 'Timberland',
        '리바이스': 'Levis',
        '챔피온': 'Champion',
        '케즈': 'Keds',
        
        # 4차
        '알도': 'Aldo',
        '뉴발란스': 'New Balance',
        '하바이아나스': 'Havaianas',
        '테바': 'Teva',
        '무스조': 'Moose Jaw',
        '룰루레몬': 'Lululemon',

        # 5차
        '마시모두띠': 'Massimo Dutti',
        '카터스': 'Carters',
        '센스': 'Ssense',
        '미니로디니': 'Mini Rodini',

        # 내가 추가
        '피엘라벤': 'Fjallraven',
        
    }
    SITES_OFFICIAL = set(site_name_ko_to_official_table.values())
    SITES_PASCAL = [''.join(name.split(' ')) for name in SITES_OFFICIAL]
    site_name_to_IP_host_table = {
        # 1차
        "Zappos": "https://www.zappos.com",
        "Fila": "https://www.fila.com",
        "Vans": "https://www.vans.com",
        "Lacoste": "https://www.lacoste.com",
        "Adidas": "https://www.adidas.com",

        "Crocs": "https://www.crocs.com",
        "North Face": "https://www.thenorthface.com",
        'Columbia': "https://www.columbia.com",
        'Salomon': "https://www.salomon.com",
        'Asics': "https://www.asics.com",
        'Hoka': "https://www.hoka.com",
        'Puma': "https://us.puma.com",
        
        # 한국주소로 자동 연결되는 곳 (우회 이전에는 US 접속 불가능)
        'Reebok': "https://www.reebok.com",
        'Tommy Hilfiger': "https://usa.tommy.com",
        'Rockport': "https://www.rockport.com",
        'Calvin Klein': "https://www.calvinklein.usr",
        'Guess': "https://www.guess.com",
        'Ralph Lauren': "https://www.ralphlauren.com",

        # 2차
        'Patagonia': "https://www.patagonia.com",
        'Macys': "https://www.macys.com",
        'Gap': "https://www.gap.com",
        'Gap Factory': "https://www.gapfactory.com",
        'Guess Factory': "https://www.guessfactory.com",

        # 3차

        'Skechers': "https://www.skechers.com",
        'Clarks': "https://www.clarks.com",
        'Timberland': "https://www.timberland.com",
        'Levis': "https://www.levi.com",
        'Champion': "https://www.champion.com",
        'Keds': "https://www.keds.com",

        # 4차 
        'Aldo': "https://www.aldoshoes.com",
        'New Balance': "https://www.newbalance.com",
        'Havaianas': "https://havaianas.com",
        'Teva': "https://www.teva.com",
        'Moose Jaw': "https://www.moosejaw.com",
        'Lululemon': "https://shop.lululemon.com",

        # 5차 (유럽 / 단위 환산, 환율 다름)
        'Massimo Dutti': "https://www.massimodutti.com",
        'Carters': "https://www.carters.com",
        'Ssense': "https://www.ssense.com",
        'Mini Rodini': "https://www.minirodini.com",

        # 내가 추가
        'Fjallraven': "https://www.fjallraven.com",
    }

    @staticmethod
    def get_official_site_name(site_name):
        '''"언더아머","Under Armour", "UnderArmour" 등의 한/영, 
            띄어쓰기 유무, 대/소문자 유무로 인해 다양한 인풋을 모아 
            하나의 공식 띄어쓰기 있는 영문 사이트명으로 되돌림'''
        '''
        주어진 한글 site_name으로 공식 사이트명을 찾으면 곧바로 반환,
        그렇지 않으면 한/영 상관 없이 소문자화 + 띄어쓰기 제거 후
        한-공식명과 영-공식명의 2개 테이블의 key의 부분문자열인지 체크,
        해당하는 결과가 1개면 그 공식 사이트명을 채택하여 반환하고
        0개 혹은 2개 이상이면 재입력 요청을 위해 빈 문자열('')을 반환함
        -> site_name 공식 사이트명보다 짧고 연이은 키워드여야 한다
        '''
        try:
            return Namer.site_name_ko_to_official_table[site_name]
        except KeyError:
            n = site_name.lower()
            n = ''.join(n.split(' '))
            # 그냥 일단 '띄어쓰기없는소문자' 사이트명의 substring에 걸리는지 살피고, 2개 이상이 걸리면 그 때 해결하기
            result = []
            for ko_name, site_official in Namer.site_name_ko_to_official_table.items():
                lower_no_space_site_official = ''.join(site_official.lower().split(' '))
                if n in ko_name or n in lower_no_space_site_official:
                    result.append(site_official)

            if len(result) == 0:
                print(f'"{site_name}"에 해당하는 공식 사이트명을 찾지 못했습니다')
                return ''
            elif len(result) == 1:
                return result[0]
            else: 
                print(f'2개 이상의 사이트명을 찾았습니다: {result}')
                print('키워드를 좁혀주세요')
                return ''

    @staticmethod
    def get_host_from_site_name(site_official):
        ''' site_name_to_IP_host_table 목록에서 검색하여 반환
        (검색 결과가 None이면 None 그대로 반환)
        '''
        return Namer.site_name_to_IP_host_table.get(site_official)
