import logging
import logging.config
from logging import LogRecord
import os
''' 
print 대용으로 사용할 핸들러 하나, 
각 사이트마다 에러를 '출력'하고 '기록'할 핸들러 둘,
각 사이트에 http 요청을 보낼 때마다 우회된 IP를 '기록'할 핸들러 하나를 정의한다.

#* 4개 핸들러 설명:
console: ROOT_LEVEL이상 WARNING 미만 메시지 콘솔에 간단히 출력
console_error: WARNING 이상 메시지 콘솔에 간단히 출력
error_to_file: ERROR 이상 메시지 'Log/error.log' 파일에 자세히 기록('request.fail'계통 로거의 메시지는 제외)
request_fail_to_file: INFO 이상 메시지 'Log/사이트명_ip_fail.log' 파일에 자세히 기록('request.fail'계통 로거의 메시지만)

#* 사용 예(Root 포함 모든 로거에 동일하게 해당):
1. 초기 세팅:
import logging
from logging_config import set_logging
set_logging(logging.DEBUG, 'Adidas') # ip 우회 실패 파일을 'Adidas_ip_fail.log'로 설정

2. 'request.fail'계통 로거가 아닌 경우:
logger = logging.getLogger('Adidas.Extractors')
logger.debug('개발 시 콘솔에만 출력')
logger.info('개발 시 콘솔에만 출력')
logger.warning('콘솔에만 에러로 출력하고 파일에는 기록하지 않음')
logger.error(e, exc_info=True) # 콘솔과 파일 모두에, stacktrace 포함

3. 'request.fail'계통 로거의 경우:
logger = logging.getLogger('request.fail.Adidas')
logger.debug('콘솔에만 출력')
logger.info/warning/error/critical('콘솔과 전용 파일 모두에 출력하고 기록)

#* 기타 특징들:
- 모든 핸들러(4개)는 Root 로거에 연결되어 있음
- 따라서 모든 하위 모듈들의 자식 로거를 생성할 때 따로 level을 설정할 필요 없음
- 개발용 print를 logger.debug()레벨로 작성하고, 개발 완료 후에 Root 로거 레벨을 INFO로 올릴 것

'''

ROOT_DIR = os.path.dirname(os.path.realpath((__file__)))
LOG_DIR = os.path.join(ROOT_DIR, 'log')

class DynamicNameFileHandler(logging.FileHandler):
	def __init__(self, logger_name, log_type, mode='a', encoding=None, delay=True):
		''' log_type: "ip" | "error" '''
		filename = f'{logger_name}_{log_type}.log'
		filepath = os.path.join(LOG_DIR, filename)
		super().__init__(filepath, mode, encoding, delay)

# ROOT_LEVEL = logging.DEBUG
# SITE_NAME = '샘플_사이트명'

class MaxLevelFilter(logging.Filter):
	''' level 미만 로그 메시지만 통과시키는 필터 '''
	def __init__(self, level):
		self.level = level
	
	def filter(self, record):
		return record.levelno < self.level

class ExcludeLoggerFilter(logging.Filter):
	''' name과 그 자손 로거가 아닌 로거의 로그 메시지만 통과시키는 필터 '''
	def filter(self, record: LogRecord) -> bool:
		return not super().filter(record)

def set_logging(root_level, site_name):
	# 로그를 저장할 LOG_DIR 디렉터리가 존재하지 않으면 생성  
	if not os.path.exists(LOG_DIR):
		os.makedirs(LOG_DIR)
	ROOT_LEVEL = root_level
	SITE_NAME = site_name
	CONFIG = {
		'version': 1,
		'disable_existing_loggers': False, #True,
		'filters': {
			'exclude_warnings': {
				# '()': '2024_ZAPPOS.logging_config.MaxLevelFilter',
				'()': MaxLevelFilter,
				'level': logging.WARNING,
			},
			'only_request_fail': {
				'()': 'logging.Filter',
				'name': 'request.fail',
			},
			'exclude_request_fail': {
				# '()': '2024_ZAPPOS.logging_config.ExcludeLoggerFilter',
				'()': ExcludeLoggerFilter,
				'name': 'request.fail',
			},
		},
		'formatters': {
			'detailed': {
				'class': 'logging.Formatter',
				# 'format': '[%(isbatch)7s]%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s',
				'format': '%(asctime)s [%(name)s] %(levelname)-8s - %(message)s',
			},
			'simple': {
				'class': 'logging.Formatter',
				'format': '%(name)-15s %(levelname)-8s %(message)s'
			},
			'ip': {
				'class': 'logging.Formatter',
				# 'format': '%(asctime)s - %(isok)-8s - %(resion)-12s - %(statuscode)-4s%(status)-15s - %(ip)-15s %(levelname)-8s %(message)s',
				'format': '%(asctime)s - %(levelname)-6s - %(message)-40s',
			}
		},
		'handlers': {
			'console': {
				'level': ROOT_LEVEL,
				'class': 'logging.StreamHandler',
				'stream': 'ext://sys.stdout',
				'filters': ['exclude_warnings'],
				'formatter': 'simple',
			},
			'console_error': {
				'level': "WARNING",
				'class': 'logging.StreamHandler',
				'stream': 'ext://sys.stderr',
				'filters': [],
				'formatter': 'simple',
				# 'exc_info': True, # 불가능
			},
			'request_fail_to_file': {
				'level': "INFO",
				'class': 'logging.FileHandler',
				'filename': os.path.join(LOG_DIR, SITE_NAME + '_ip_fail.log'),
				'delay': True,
				'filters': ['only_request_fail'],
				'formatter': 'ip',
				'encoding': 'utf-8',
			},
			'error_to_file': {
				'level': "ERROR",
				'class': 'logging.FileHandler',
				'filename': os.path.join(LOG_DIR, 'error.log'),
				'delay': True,
				'filters': ['exclude_request_fail'],
				'formatter': 'detailed',
				'encoding': 'utf-8',
			},
			# 'print': {
			# 	'class': 'logging.StreamHandler', 
			# 	'formatter': 'simple',
			# 	'level': 'DEBUG',
			# },
			# 'error_print': {
			# 	'class': 'logging.StreamHandler', 
			# 	'formatter': 'simple',
			# 	'level': 'ERROR',
			# },
			# # 다이내믹하게 바꾸기를 원하는 형태: 
			# 'ip_file': {
			# 	'class': 'logging.FileHandler',
			# 	'filename': f'{logger_name}_ip.log',
			# 	'formatter': 'ip',
			# 	'level': 'INFO',
			# },
			# 'error_file': {
			# 	'class': 'logging.FileHandler', 
			# 	'filename': f'{logger_name}.log',
			# 	'formatter': 'detailed',
			# 	'level': 'ERROR',
			# },


			# 커스텀 핸들러를 사용하는 방법: logger를 만들 때마다 addHandler해줘야 하고 
			# 그러면 최초의 dictConfig() 호출시 대체 어떤 핸들러가 만들어진 상태인건지 알 수 없단 문제 
			# 'ip_file': {
			# 	'()': DynamicNameFileHandler,
			# 	'logger_name': 'default',
			# 	'log_type': 'ip',
			# 	'formatter': 'ip',
			# 	'level': 'DEBUG',
			# },
			# 'error_file': {
			# 	'()': DynamicNameFileHandler,
			# 	'logger_name': 'default',
			# 	'log_type': 'error',
			# 	'formatter': 'detailed',
			# 	'level': 'ERROR',
			# },


			# # 여기서부턴 그냥 하드코딩: 각 사이트별로 2개씩 만듬
			# ## Zappos
			# 'zappos_ip_file': {
			# 	'class': 'logging.FileHandler',
			# 	'filename': 'Log\zappos_ip.log',
			# 	'formatter': 'ip',
			# 	'level': 'DEBUG',
			# },
			# 'zappos_error_file': {
			# 	'class': 'logging.FileHandler', 
			# 	'filename': 'Log\zappos_error.log',
			# 	'formatter': 'detailed',
			# 	'level': 'ERROR',
			# },
			# ## NorthFace
			# 'northface_ip_file': {
			# 	'class': 'logging.FileHandler',
			# 	'filename': 'Log\\northface_ip.log',
			# 	'formatter': 'ip',
			# 	'level': 'DEBUG',
			# },
			# 'northface_error_file': {
			# 	'class': 'logging.FileHandler', 
			# 	'filename': 'Log\\northface_error.log',
			# 	'formatter': 'detailed',
			# 	'level': 'ERROR',
			# },
			# # 추가


			# ## test이름으로 다이내믹 handler
			# 'test': {
			# 	'()': DynamicNameFileHandler,
			# 	'level': 'DEBUG',
			# 	'formatter': 'ip',
			# 	'log_type': 'ip',
			# 	'logger_name': 'test_dynamic',
			# },


			# ## 딕셔너리 강제 삽입 방식의 다이내믹 handler
			# 'test_ip_file': {
			# 	'class': 'logging.FileHandler',
			# 	'filename': 'default.log',
			# 	# 'formatter': 'detailed',
			# 	'level': 'DEBUG'
			# },
			# 'test_error_file': {
			# 	'class': 'logging.FileHandler',
			# 	'filename': 'default.log',
			# 	# 'formatter': 'detailed',
			# 	'level': 'ERROR'
			# },
		},
		# 'loggers': {
		# 	'console': {
		# 		'handlers': ['print'],
		# 		'level': 'DEBUG',
		# 		'propagate': False,
		# 	},
		# 	'test': {
		# 		'handlers': ['test_ip_file', 'test_error_file'],
		# 		'level': 'DEBUG',
		# 		'propagate': False,
		# 	},
		# 	'zappos': { # logger.INFO()면 ip_file에만, logger.ERROR()이상이면 두 파일과 콘솔 모두에
		# 		'handlers': ['error_print', 'zappos_error_file', 'zappos_ip_file'],
		# 		'level': 'INFO', 
		# 		'propagate': False,
		# 		# TODO: 에러가 나든 어쩌든 http 요청을 실제로 보냈을 때만 ip_file에 기록되게 하고 싶은데.
		# 	},
		# 	'northface': { # logger.INFO()면 ip_file에만, logger.ERROR()이상이면 두 파일과 콘솔 모두에
		# 		'handlers': ['error_print', 'northface_error_file', 'northface_ip_file'],
		# 		'level': 'INFO',
		# 		'propagate': False,
		# 		# TODO: 에러가 나든 어쩌든 http 요청을 실제로 보냈을 때만 ip_file에 기록되게 하고 싶은데.
		# 	},
		# 	# 추가
		# },
		'root': {
			'handlers': ['console', 'console_error', 'request_fail_to_file', 'error_to_file'],
			'level': ROOT_LEVEL,
		}
	}

	logging.config.dictConfig(CONFIG)

