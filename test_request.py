import fastAPI.config as config
import requests
import json
import sys

def send_font_request(font_name: str = "TestFont"):
    """FastAPI 서버의 /font 엔드포인트에 POST 요청을 보냅니다."""
    api_url = "http://localhost:8000/font"
    headers = {"Content-Type": "application/json"}
    payload = {
        config.FONT_ID_KEY: font_name,
        config.MEMBER_ID_KEY: "213123",
        config.FONT_NAME_KEY: "testFontName",
        config.TEMPLATE_URL_KEY: "https://....",
        config.AUTHOR_KEY: "author",
        config.REQUEST_UUID_KEY: "sadsadsa"
    }
    # payload = {"font_name": font_name}

    print(f"FastAPI 서버 ({api_url})에 폰트 생성 요청 전송 중...")
    print(f"폰트 이름: {font_name}")
    print(f"요청 데이터: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # HTTP 오류 발생 시 예외 발생

        print("\n--- 서버 응답 ---")
        try:
            # JSON 응답 파싱 시도
            print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        except json.JSONDecodeError:
            # JSON 파싱 실패 시 텍스트로 출력
            print(response.text)
        print("-----------------")

    except requests.exceptions.ConnectionError:
        print(f"\n오류: 서버({api_url})에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
    except requests.exceptions.RequestException as e:
        print(f"\n오류: 요청 중 문제가 발생했습니다: {e}")
        if e.response is not None:
            print(f"서버 응답 (오류): {e.response.status_code} - {e.response.text}")

if __name__ == "__main__":
    # 명령줄 인자에서 폰트 이름 가져오기
    if len(sys.argv) > 1:
        font_name_arg = sys.argv[1]
    else:
        font_name_arg = "TestFont"
        print("폰트 이름 인자가 제공되지 않았습니다. 기본값 'TestFont' 사용.")

    send_font_request(font_name_arg) 