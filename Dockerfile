FROM public.ecr.aws/lambda/python:3.13

# Copy requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}

# Install the specified packages
RUN pip install -r requirements.txt

# Copy function code
COPY src/ ${LAMBDA_TASK_ROOT}/src/

# Set the CMD to your handler
CMD [ "src.handlers.lambda_handler.lambda_handler" ] 