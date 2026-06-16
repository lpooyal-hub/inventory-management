# Inventory Management MVP

지인 요청으로 복잡한 ERP 대신, 매일 출고 기록과 월별 파일 업로드를 함께 쓰는 소규모 사업장의 엑셀 기반 재고관리 업무를 웹 시스템으로 전환한 재고관리 MVP입니다.


## MVP 목표

1. 보유 재고에서 매일 입고/출고/실재고 조정 기록을 남긴다.
2. 제품별 월 출고량을 월별 통계 페이지에서 관리한다.
3. 최근 3개월 월 평균 출고량을 재고현황과 바로 연동한다.
4. 현재고가 평균 대비 부족한 제품을 바로 확인한다.
5. 부족 상태인 제품은 생산주문 필요 대상으로 본다.

## 프로젝트 구조

```text
inventory-management/
  backend/
    app/
      core/
      db/
      models/
      routers/
      schemas/
      services/
      main.py
  frontend/
    src/
      components/
      pages/
      api.js
      App.jsx
```

## 핵심 DB

### products

- `id`
- `product_code`
- `name`
- `barcode`
- `memo`
- `created_at`
- `updated_at`

### stock_movements

- `id`
- `product_id`
- `movement_date`
- `movement_type`
- `quantity`
- `memo`
- `created_at`

`movement_type` 값:

- `IN`
- `OUT`
- `ADJUST`

## 계산 로직

- `현재고 = 입고 합계 - 출고 합계 + 조정 합계`
- `월별 출고량 = 해당 월 OUT 수량 합계`
- `최근 3개월 월 평균 출고량 = 최근 3개월 OUT 합계 / 3`
- `평균 대비 재고수량 = 현재고 - 최근 3개월 월 평균 출고량`
- `평균 대비 재고수량 < 0` 이면 `부족`
- `현재고 < 최근 3개월 월 평균 출고량 * 0.5` 이면 `심각 부족`

## API

- `GET /health`
- `GET /api/products`
- `POST /api/products`
- `GET /api/inventory/summary`
- `POST /api/stock-movements`
- `GET /api/reports/monthly-outbound?year=2026&month=6`
- `GET /api/reports/monthly-outbound-trend?year=2026&month=6&months=12`
- `GET /api/reports/shortage`
- `POST /api/uploads/monthly-preview?year=2026&month=6`
- `POST /api/uploads/monthly-commit`
- `GET /api/monthly-records?year=2026&month=6`
- `DELETE /api/monthly-records?year=2026&month=6`

## 화면

- `/inventory`
  - 제품명
  - 현재고
  - 이번 달 출고량
  - 최근 3개월 월 평균 출고량
  - 평균 대비 재고수량
  - 부족 상태
  - 생산주문 필요 여부

- `/movements`
  - 날짜
  - 제품 선택
  - 입고/출고/실재고 조정
  - 수량 입력
  - 저장

- `/reports/monthly`
  - 월 선택
  - 해당 월 xlsx 업로드
  - 업로드 미리보기
  - 전체 선택 / 전체 해제
  - 월 데이터 리셋
  - 제품별 월 출고량
  - 최근 12개월 출고 추이

- `/reports/shortage`
  - 부족 제품만 표시
  - 빨간불 표시
  - 생산주문 필요 제품 확인

## 참고

- 예전 데이터에 `inbound`, `outbound`, `adjustment` 같은 값이 남아 있어도 서비스 레이어에서 `IN`, `OUT`, `ADJUST`로 흡수하도록 처리했습니다.
- 월별 업로드를 반영하면 해당 월의 제품별 `OUT` movement도 함께 생성되어 최근 3개월 평균과 재고현황에 바로 반영됩니다.
- 같은 월 데이터를 다시 반영할 때는 해당 월 업로드로 생성된 movement를 교체합니다.
- 같은 달에 이미 일일 `OUT` 입력을 많이 해둔 상태에서 같은 달 월업로드를 다시 반영하면 해석이 겹칠 수 있으니, 운영상으로는 마감된 월 통계 업로드에 우선 사용하는 편이 안전합니다.
- 현재 회사 제품은 약 127개로 보고 있으며, `product_code`는 현재 사용하는 신코드, `legacy_code`는 예전 코드로 분리해 관리합니다.
- 엑셀에서 제품명이 `DEEP200 / 딥 리페어링 헤어 마스크(200ml)` 형태라면 `legacy_code=DEEP200`, `name=딥 리페어링 헤어 마스크(200ml)`로 자동 분리합니다.
- 신제품처럼 구코드가 없는 경우에는 `legacy_code`를 비워둡니다.
- 제품 식별의 기준은 내부 `id`이고, 신코드/구코드는 업무상 참조 코드로 취급하는 방향이 맞습니다.

## 제품 일괄 등록

월별 입출고 통계 파일 기준으로 제품 127건을 일괄 등록할 수 있습니다.

```bash
cd inventory-management
python3 backend/scripts/import_products_from_monthly_xlsx.py "/path/to/monthly-inventory.xlsx"
```

등록 기준:

- `상품코드` -> `product_code`
- `상품명` 앞 코드 prefix -> `legacy_code`
- `상품명` 본문 -> `name`
- `바코드` -> `barcode`
- `현재고`는 등록 대상 필터 판단에 사용

현재 규칙:

- 같은 `legacy_code`를 공유하는 제품이 여러 개 있을 때
- 그중 `현재고 > 0`인 제품이 하나라도 있으면
- 같은 구코드 묶음 안에서 `현재고 = 0`인 제품은 이번 등록 대상에서 제외합니다.

예:

- `ORG500` 그룹에서 재고 있는 코드가 있으면
- 재고 0인 `ORG500` 코드는 비사용 코드로 보고 이번 제품 등록에서 제외

이미 제품이 있는 경우에는 다음 우선순위로 기존 레코드를 찾아 업데이트합니다.

1. 신코드 일치
2. 구코드 일치
3. 기존 `product_code`가 구코드와 일치
4. 바코드 일치
5. 제품명 일치
