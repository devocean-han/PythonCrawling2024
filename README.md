# PythonCrawling2024

파이썬 크롤링 파일의 편한 공유를 위한 레파지토리

<div id="top"></div>
<br>

<!-- GETTING STARTED -->

## 프로그램 다운로드 및 시작 방법

### 1. Github 레파지토리에서 다운로드

원하는 버전 다운로드 후 압축을 풉니다.  

### 2. 압축 푼 폴더로 이동

cmd를 열고 다음 커맨드를 입력합니다:  
(예를 들어 윈도우에서 "C:\USERS\User\Downloads" 폴더에 "PythonCrawling2024-1.3"이라는 폴더명으로 압출을 풀었다면: )  
```sh
cd "C:\USERS\User\Downloads\PythonCrawling2024-1.3\PythonCrawling2024-1.3"
```
(압축 파일 내부에 동일 이름의 폴더가 하나 더 있음)  

명령어 실행 후 커서가 다음과 같이 깜빡이고 있어야 합니다.
```
C:\USERS\User\Downloads\PythonCrawling2024-1.3\PythonCrawling2024-1.3> | <- 커서
```

### 3. PIP 패키지 설치

열어둔 cmd 창에서 다음 명령어로 프로그램 실행이 필요한 파이썬 패키지를 설치합니다:  
```sh
pip install -r requirements.txt  
```

(requirements.txt가 압축 푼 폴더에 들어있기 때문에 압축 푼 폴더로 이동해서 명령해줘야 했음)

### 4. 필요 파일 수정 혹은 복사 덮어씌우기

새 버전을 다운로드할 때마다 압축 푼 폴더 내에 다음 파일들이 존재하도록 해줘야 합니다:
1. `images.py` 파일 수정 혹은 복사 덮어씌우기
2. `python-crawling-gspread-145332f402e3.json` 파일 복사 붙여넣기
3. `.env` 파일 복사 붙여넣기
<br>  


### 5. 프로그램 실행하기

압축 푼 폴더에서 Batch_BASIC.py 파일을 실행해줍니다.  
1. 방법1: Python IDLE로 하던대로 실행
2. 방법2: 열어둔 cmd 창에서 '압축 푼 폴더로 이동한 상태'에서 그대로 `python Batch_BASIC.py` 명령어 실행
