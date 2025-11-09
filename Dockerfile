FROM public.ecr.aws/lambda/python:3.13 AS builder
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -t /opt/python


FROM public.ecr.aws/lambda/python:3.13
COPY --from=builder /opt /opt
COPY app ./app
CMD ["app.main.handler"]
