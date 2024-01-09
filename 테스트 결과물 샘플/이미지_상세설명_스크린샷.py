from selenium import webdriver
from selenium.webdriver.chrome.options import Options

# 크롬 드라이버 경로 설정 (본인 컴퓨터에 맞게 변경)
chrome_driver_path = 'C:/Users/USER/Downloads/Programs/chromedriver.exe'

# 크롬 브라우저 옵션 설정
chrome_options = Options()
chrome_options.add_argument('--headless')  # 브라우저 창을 띄우지 않고 실행
## (기존 옵션 설정 방법): 
# options = webdriver.ChromeOptions()

# 웹 드라이버 초기화
driver = webdriver.Chrome(chrome_driver_path, options=chrome_options)

# 웹 페이지 로드
# url = 'file:///./2024_Zappos/이미지_상세설명_test.html'  # '현재 디렉터리'는 (왜인지) 파이썬/2024_Zappos가 아니라 파이썬이다. 그리고 상대경로는 어떻게 해도 안된다.
url_absolute = 'file:///C:/Users/USER/Documents/%EC%96%B8%EB%8B%88%20%EC%8A%A4%EB%A7%88%ED%8A%B8%EC%8A%A4%ED%86%A0%EC%96%B4%20%EB%8F%84%EC%9B%80%20%EC%A0%95%EB%B3%B4%EB%B6%84%EB%A5%98/%ED%8C%8C%EC%9D%B4%EC%8D%AC/2024_Zappos/%EC%9D%B4%EB%AF%B8%EC%A7%80_%EC%83%81%EC%84%B8%EC%84%A4%EB%AA%85_test.html'
driver.get(url_absolute)

# 스크린샷 캡쳐
output_path = '2024_Zappos\html_capture_test.png'  # 저장할 이미지 파일 경로
# driver.save_screenshot(output_path)
## 오오오 성공!!!
S = lambda X: driver.execute_script('return document.body.parentNode.scroll'+X)
driver.set_window_size(S('Width'),S('Height')) 
driver.find_element_by_tag_name('body').screenshot(output_path)
'''
S = lambda X : 인자 X를 받는 람다 함수 S를 생성
driver.execute_script() : executes Javascript code
element.scrollWidth : returns the width of an element in pixels(including padding)
element.scrollHeight: returns the height of an element in pixels(including padding)
 => 즉, 1) 브라우저 창을 열고
  2) body의 부모 태그인 html 요소의 높이, 너비로 창 크기를 조절 (headless로 여니까 가능한 기예)
  3) 그리고 body 태그 부분을 캡쳐하고 output_path 경로와 이름으로 파일 저장! 
(참조: https://pythonbasics.org/selenium-screenshot/)
'''

# 브라우저 종료
driver.quit()
## (headless로 실행하고 닫지 못한 크롬창 닫는 방법?)

print(f"스크린샷 저장 완료: {output_path}")
