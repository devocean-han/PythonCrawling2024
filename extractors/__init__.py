from pkgutil import iter_modules
from importlib import import_module
# from pprint import pprint

# from strategy_decorator import STRATEGIES

package_path = __path__
# print(package_path)
# -> ['C:\\Users\\USER\\Documents\\언니 스마트스토어 도움 정보분류\\파이썬\\2024_Zappos\\extractors']
# print(__name__)
# -> extractors

for _, module_name, _ in iter_modules(package_path):
    if module_name.endswith('_extractors'):
        import_module('.' + module_name, __name__)
        # -> __init__.py에서 __name__은 패키지 이름이 됨
        # 따라서, '현재 패키지'를 extractors 패키지로 삼고
        # 현재 패키지 내(= '.')의 module_name 모듈을 임포트하겠다는 의미

        # print('\n')
        # print(module_name)
# print('\n')
# pprint(STRATEGIES)