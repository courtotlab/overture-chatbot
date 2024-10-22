# onnxruntime does not support Python >3.12
FROM python:3.12

WORKDIR /code

COPY requirements.txt ./
COPY initialize_db ./initialize_db
COPY overture_chatbot ./overture_chatbot
COPY run.sh ./

RUN pip install --upgrade pip
RUN pip install -r requirements.txt
# grant permission
RUN chmod +x run.sh

CMD ["./run.sh"]