from strategy_decorator import STRATEGIES

class StrategyFactory:
    @staticmethod
    def create_strategies(site_official, strategy_names):
        ''' 
        @export_strategy로 마크된 전략이면 해당 사이트의 추출자 인스턴스를,
        마크되지 않았거나 존재하지 않는 전략명이면 None을 차례로 대입시킨
        전략 인스턴스 목록을 반환 
        ex) create_strategy('Vans', ['PriceExtrator', 'SeleniumWaitSelector'])
            => [VansPriceExtractor(), None]
        ex) create_strategy('North Face Korea', ['PriceExtrator', 'SeleniumWaitSelector'])
            => [NorthFaceKoreaPriceExtractor(), None]
        '''
        site_official_pascal = ''.join(site_official.split(' '))
        strategy_instances = []
        for name in strategy_names:
            StrategyClass = STRATEGIES.get((site_official_pascal, site_official_pascal + name))
            if StrategyClass is None:
                strategy_instances.append(None)
            else:
                strategy_instances.append(StrategyClass())
        return strategy_instances