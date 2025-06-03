**ezpage에서 백엔드파트를 맡은 성신여대 AI융합학부 김예준**입니다.  
---
<img src="YEJUNKIM.png" width="100"/>
<p align="center">20221336 김예준</p>
---
### 🌟 주요 기능
✅ 사용자 관리 (회원가입, 로그인, 인증)  
✅ 여행 생성/수정/삭제/조회  
✅ 지출 기록 (수동/스캔 입력)  
✅ 지갑 관리 (화폐 종류·수량)  
✅ AI 지불 가이드 (보유 화폐 기반 결제 추천)
---
## ⚙️ 사용 기술
- **Python 3.8+**
- Django 4.x / DRF
- PostgreSQL
- Gunicorn, Whitenoise
- python-dotenv (환경 변수 관리)
- requests (AI 서버 통신)
- Pillow (이미지 업로드)
---
### 2️⃣ 프로젝트 설정

```bash
git clone <https://github.com/Sungshin-Capstone/ezpage_Backend.git>
cd ezpage_backend

# 가상환경 생성/활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt
```
---
## 🛠️ API 엔드포인트

기본 URL: `https://ezpage-backend.onrender.com/api/v1/`

**주요 엔드포인트 예시**  
- **사용자**  
  - `POST /accounts/signup/`: 회원가입  
  - `POST /accounts/login/`: 로그인 (JWT 토큰 발급)  
  - `GET /accounts/profile/`: 프로필 조회  

- **여행·지출**  
  - `POST /expenses/`: 지출 기록 생성  
  - `GET /expenses/<trip_id>/`: 여행별 지출 조회  
  - `POST /expenses/scan-result/`: 스캔 결과로 지출 생성  
  - `POST /expenses/payment_guide/`: AI 결제 가이드  
  - `POST /expenses/menu_payment/`: 메뉴 결제 처리  

- **지갑**  
  - `GET /wallet/`: 지갑 요약  
  - `POST /wallet/deduct/`: 지갑 금액 차감  

**인증**: `Authorization: Bearer <token>` 헤더 사용.

## 🗂️ 프로젝트 구조
```
/
├── .github/              # GitHub Actions 등 CI/CD 설정 (TODO)
├── accounts/             # 사용자 계정 관리 앱
├── expenses/             # 지출, 여행, 지갑, 결제 가이드 앱
├── ezpage/               # 메인 프로젝트 설정 및 URLConf
├── logs/                 # 애플리케이션 로그 (TODO: 설정)
├── media/                # 사용자 업로드 미디어 파일 (개발 환경)
├── profiles/             # 사용자 프로필 확장 앱 (가정, TODO: 확인)
├── staticfiles/          # 정적 파일 (collectstatic 후)
├── templates/            # 공통 HTML 템플릿 (TODO: 확인)
├── .gitignore            # Git 추적 제외 파일 설정
├── .idea/                # IDE 설정 파일
├── Procfile              # PaaS 배포 설정 (Render 등)
├── README.md             # 프로젝트 설명 파일
├── requirements.txt      # Python 의존성 목록
└── manage.py             # Django 프로젝트 관리 유틸리티
```