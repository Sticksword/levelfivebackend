# readme

MVP use case is to have a splash screen and a demo that initiates a test run and takes them to results page
will need to support two endpoints, that's it

todo: clean up requirements.txt

## local setup

``` bash
pip install -r requirements.txt
uvicorn example:app --reload
```

## eval package notes

``` bash
accelerate launch  main.py \
  --model sticksword/my_first_model \
  --tasks mbpp \
  --limit <NUMBER_PROBLEMS> \
  --max_length_generation <MAX_LENGTH> \
  --temperature 0.1 \
  --do_sample True \
  --n_samples 15 \
  --batch_size 10 \
  --precision <PRECISION> \
  --allow_code_execution \
  --save_generations
```

``` bash
accelerate launch  main.py \
  --model bigcode/santacoder \
  --max_length_generation 200 \
  --tasks mbpp \
  --temperature 0.1 \
  --n_samples 15 \
  --batch_size 10 \
  --allow_code_execution \
  --trust_remote_code
```

bigcode
``` bash
accelerate launch  main.py \
  --model sticksword/my_first_model \
  --max_length_generation 200 \
  --tasks mbpp \
  --temperature 0.1 \
  --n_samples 15 \
  --batch_size 10 \
  --allow_code_execution
```

eleuther
``` bash
python main.py \
    --model hf-auto \
    --model_args pretrained=sticksword/my_first_model \
    --tasks hellaswag \
    --device cpu
```

## sagemaker stuff

i'm running using the role ARN directly in my notebook

``` python
role = 'arn:aws:iam::102566532692:role/service-role/SageMaker-MySageMakerComputeRole'
script_processor = ScriptProcessor(
    command=["python3"],
    image_uri=processing_repository_uri,
    role=role,
    instance_count=1,
    instance_type="ml.m5.xlarge",
)
```

the role was created directly from the sagemaker section UI. i also made an IAM user but that's more so for boto3 client stuff like manually reading from s3 and whatnot. i don't think i'll need it for this situation.

using iam credentials inserted into `aws configure`:
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 763104351884.dkr.ecr.us-west-2.amazonaws.com

then I build image:
docker build -t sagemaker-processing-container -f Dockerfile .

before push, need docker login using aws creds:
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 102566532692.dkr.ecr.us-west-2.amazonaws.com

then i tag and push:
docker tag sagemaker-processing-container:latest 102566532692.dkr.ecr.us-west-1.amazonaws.com/sagemaker-processing-container:latest
docker push 102566532692.dkr.ecr.us-west-1.amazonaws.com/sagemaker-processing-container:latest

then i run the notebook to launch script using this image
