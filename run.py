import ssl
from app import create_app

app = create_app()

if __name__ == "__main__":
    # ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    # ssl_ctx.load_cert_chain('/home/ubuntu/SoSweet_API.pem')  
    
    app.run(host="0.0.0.0",
            port=5000, 
            # debug=True,
            # ssl_context=ssl_ctx  # 인증서 경로 설정
    )
