# EzPage Backend

**ezpage에서 백엔드파트를 맡은 성신여대 AI융합학부 김예준**입니다.  

<table>
  <tr>
    <td align="center">
      <img src="https://github.com/user-attachments/assets/f86e3f79-861d-4a8e-9ef4-3206cb392edd" width="200"/><br/>
      <b> 20221336 김예준 </b>
    </td>
  </tr>
</table>  

---

### 🌟 주요 기능
- ✅ 사용자 관리 (회원가입, 로그인, 인증)
- ✅ 여행 생성/수정/삭제/조회
- ✅ 지출 기록 (수동/스캔 입력)
- ✅ 지갑 관리 (화폐 종류·수량)
- ✅ AI 지불 가이드 (보유 화폐 기반 결제 추천)

---

## ⚙️ 사용 기술
- **Python 3.8+**
- Django 4.2.20
- Django REST Framework 3.16.0
- PostgreSQL (dj-database-url 2.3.0)
- Gunicorn 23.0.0
- JWT 인증 (djangorestframework-simplejwt 5.5.0)
- CORS 지원 (django-cors-headers 4.7.0)
- 이미지 처리 (Pillow 11.2.1)
- 환경 변수 관리 (python-dotenv 1.1.0)
- HTTP 클라이언트 (requests 2.32.3)

---

## 📁 프로젝트 구조
```
ezpage_backend/
├── accounts/           # 사용자 관리 앱
├── expenses/          # 지출 및 지갑 관리 앱
├── ezpage/            # 프로젝트 설정
├── media/             # 업로드된 미디어 파일
├── profiles/          # 사용자 프로필 이미지
├── static/            # 정적 파일
├── templates/         # 템플릿 파일
├── assets/            # 프로젝트 이미지
├── logs/              # 로그 파일
├── .env               # 환경 변수
├── .gitignore         # Git 제외 파일
├── build.sh           # 빌드 스크립트
├── manage.py          # Django 관리 유틸리티
├── Procfile           # Heroku 배포 설정
└── requirements.txt   # Python 의존성 목록
```

---

## 🚀 시작하기

### 1. 환경 설정
1. Python 3.8 이상 설치
2. PostgreSQL 설치 및 데이터베이스 생성
3. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

### 2. 의존성 설치
```bash
pip install -r requirements.txt
```
---
## 🛠️ API 엔드포인트

기본 URL: `https://ezpage-backend.onrender.com/api/v1/`

### ✅ 인증 관련

- `POST /accounts/signup/`: 회원가입  
- `POST /accounts/login/`: 로그인
- `POST /accounts/logout/`: 로그아웃  
- `GET /accounts/profile/`: 프로필 조회  
- `POST /accounts/reset-password/`: 비밀번호 재설정 요청 
- `POST /accounts/reset-password-confirm/`: 비밀번호 재설정 완료
- `POST /accounts/settings/language/`: 언어 및 통화 설정  

### ✈️ 여행 관리

- `POST /trips/`: 여행 생성  
- `GET /trips/`: 전체 여행 리스트 조회  
- `GET /trips/<trip_id>/`: 특정 여행 상세 조회  
- `PATCH /trips/<trip_id>/`: 여행 정보 수정  
- `DELETE /trips/<trip_id>/`: 여행 삭제  

### 💸 지출 관리

- `POST /expenses/`: 지출 수동 입력
- `GET /expenses/?date=YYYY-MM-DD`: 날짜별 지출 조회  
- `POST /expenses/scan-result/`: 스캔 결과로 지출 등록  
- `POST /expenses/guide-payment/`: 지불가이드 결과 기반 지출 등록 + 지갑 차감  
- `POST /expenses/menu_payment/`: AI 기반 메뉴 결제 처리  

### 👛 지갑 (Wallet)

- `POST /wallet/scan-result/`: 글로벌 머니 스캐너 지출 등록  
- `GET /wallet/`: 전체 지갑 조회  
- `PATCH /expenses/wallet/<wallet_id>/update/`: 지폐 수량 수동 수정  
- `POST /expenses/wallet/deduct/`: 지갑 차감 처리  

---

**모든 요청은 인증 필요: `Authorization: Bearer <token>` 헤더 필수**
