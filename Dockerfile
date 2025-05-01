FROM python:3.11-slim

ENV TZ=Asia/Taipei
ENV APP_FILE_DUMP=/app/file_dump
ENV APP_FILE_DUMP_AGE_DAYS=7
ENV OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
ENV GOOGLE_API_KEY=AIzaSyB0000000000000000000000000000000


COPY .tmpbuild/ /app
COPY ./scripts/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh
WORKDIR /app

RUN apt-get update && \
    apt-get install -y ffmpeg && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip install audio_summary-*.whl
RUN rm audio_summary-*.whl
RUN rm -rf *.gz

EXPOSE 8501

CMD ["docker-entrypoint.sh"]