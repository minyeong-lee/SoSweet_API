from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=5000, 
            # debug=True,
            ssl_context=(
                'home/SoSweet_API.pem',
            )  # 인증서 경로 설정
    )
