import logging

''' 
print 대용으로 사용할 핸들러 하나, 
각 사이트마다 에러를 '출력'하고 '기록'할 핸들러 둘,
각 사이트에 http 요청을 보낼 때마다 우회된 IP를 '기록'할 핸들러 하나를 정의한다.
'''
CONFIG = {
	'version': 1,
	'disable_existing_loggers': True,
	'formatters': {
		'detailed': {
			'class': 'logging.Formatter',
			'format': '[%(isbatch)7s]%(asctime)s - %(name)-15s - %(levelname)-8s - %(message)s'
		},
		'simple': {
			'class': 'logging.Formatter',
			'format': '%(name)-15s %(levelname)-8s %(message)s'
		},
		'ip': {
			'class': 'logging.Formatter',
			'format': '%(asctime)s - %(isok)-8s - %(resion)-12s - %(statuscode)-4s%(status)-15s - %(ip)-15s %(levelname)-8s %(message)s'
		}
	},
	'handlers': {
		'print': {
			'class': 'logging.StreamHandler', 
			'formatter': 'simple',
			'level': 'DEBUG',
		},
		'error_print': {
			'calss': 'logging.StreamHandler', 
			'formatter': 'simple',
			'level': 'ERROR',
		},
		# 다이내믹하게 바꾸기를 원하는 형태: 
		'ip_file': {
			'class': 'logging.FileHandler',
			'filename': f'{logger_name}_ip.log',
			'formatter': 'ip',
			'level': 'INFO',
		},
		'error_file': {
			'class': 'logging.FileHandler', 
			'filename': f'{logger_name}.log',
			'formatter': 'detailed',
			'level': 'ERROR',
		},
		# 커스텀 핸들러를 사용하는 방법: logger를 만들 때마다 addHandler해줘야 하고 
		# 그러면 최초의 dictConfig() 호출시 대체 어떤 핸들러가 만들어진 상태인건지 알 수 없단 문제 
		'ip_file': {
			'()': 'CustomNameFileHandler',
			'logger_name': 'default',
			'log_type': 'ip',
			'formatter': 'ip',
			'level': 'INFO',
		},
		'error_file': {
			'()': 'CustomNameFileHandler',
			'logger_name': 'default',
			'log_type': 'error',
			'formatter': 'detailed',
			'level': 'ERROR',
		},
		# 여기서부턴 그냥 하드코딩: 각 사이트별로 2개씩 만듬
		## Zappos
		'zappos_ip_file': {
			'class': 'logging.FileHandler',
			'filename': 'zappos_ip.log',
			'formatter': 'ip',
			'level': 'INFO',
		},
		'zappos_error_file': {
			'class': 'logging.FileHandler', 
			'filename': 'zappos_error.log',
			'formatter': 'detailed',
			'level': 'ERROR',
		},
		## NorthFace
		'northface_ip_file': {
			'class': 'logging.FileHandler',
			'filename': 'northface_ip.log',
			'formatter': 'ip',
			'level': 'INFO',
		},
		'northface_error_file': {
			'class': 'logging.FileHandler', 
			'filename': 'northface_error.log',
			'formatter': 'detailed',
			'level': 'ERROR',
		},
		# 추가
	},
	'loggers': {
		'console': {
			'handlers': ['print'],
			'level': 'DEBUG',
			'propagate': False,
		},
		'zappos': { # logger.INFO()면 ip_file에만, logger.ERROR()이상이면 두 파일과 콘솔 모두에
			'handlers': ['error_print', 'zappos_error_file', 'vip_file'],
			'level': 'INFO', 
			'propagate': False,
			# TODO: 에러가 나든 어쩌든 http 요청을 실제로 보냈을 때만 ip_file에 기록되게 하고 싶은데.
		},
		'northface': { # logger.INFO()면 ip_file에만, logger.ERROR()이상이면 두 파일과 콘솔 모두에
			'handlers': ['error_print', 'northface_error_file', 'northface_ip_file'],
			'level': 'INFO',
			'propagate': False,
			# TODO: 에러가 나든 어쩌든 http 요청을 실제로 보냈을 때만 ip_file에 기록되게 하고 싶은데.
		},
		# 추가
	},
	'root': {
		'handlers': ['print'],
		'level': 'DEBUG',
	}
}

class DynamicNameFileHandler(logging.FileHandler):
	def __init__(self, logger_name, log_type, mode='a', encoding=None, delay=True):
		filename = f'{logger_name}_{log_type}.log'
		super().__init__(filename, mode, encoding, delay)
