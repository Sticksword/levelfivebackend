from fastapi import FastAPI, APIRouter
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel
import boto3

import test_run

from sagemaker.processing import ProcessingInput, ProcessingOutput
from sagemaker.processing import ScriptProcessor


class TestRunParam(BaseModel):
    model_name: str
    test_suite: str


app = FastAPI()


SAGEMAKER_ROLE = (
    "arn:aws:iam::102566532692:role/service-role/SageMaker-MySageMakerComputeRole"
)
router_foo = APIRouter()
router_bar = APIRouter()

ecr_repository = "sagemaker-processing-container"
tag = ":latest"
region = "us-west-2"
account_id = "102566532692"
processing_repository_uri = (
    f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repository + tag}"
)


@router_foo.post("/runs")
def create_test_run(test_run_param: TestRunParam):
    # use case is from splash screen, pass in model repo and use case, take you to test run page after with results = pending
    test_run_ = test_run.TestRun(boto3.resource("dynamodb", region_name="us-west-2"))
    test_run_.add_test_run('userkey_a', test_run_param.model_name, test_run_param.test_suite)
    return JSONResponse({"status": 200})


@app.get("/runs/{id}")
def get_test_run(id: str):
    # when a user clicks the demo on splash screen, we initiate a test run and direct them to a "pending page"
    # so this endpoint will get called twice, first to just load and show pending, then to load and show results
    # todo: ^ clean this logic up
    test_run_ = test_run.TestRun(boto3.resource("dynamodb", region_name="us-west-2"))
    res = test_run_.get_test_run('userkey_a', id)
    res["metric_value"] = float(res["metric_value"])  # cast Decimal to something JSON serializable
    return JSONResponse({"status": 200, "res": res})


@router_foo.get("/foo")
def foo():

    script_processor = ScriptProcessor(
        command=["python3"],
        image_uri=processing_repository_uri,
        role=SAGEMAKER_ROLE,
        instance_count=1,
        instance_type="ml.g4dn.xlarge",
    )
    script_processor.run(
        code="sagemaker-script.py",
        inputs=[
            ProcessingInput(
                source="s3://my-bucket-789", destination="/opt/ml/processing/input"
            )
        ],
        outputs=[
            ProcessingOutput(
                output_name="dummy_folder", source="/opt/ml/processing/output"
            ),
        ],
        arguments=[
            "--model",
            "hf-seq2seq",
            "--model_args",
            "pretrained=sticksword/my_first_model",
            "--tasks",
            "hellaswag",
            "--device",
            "cuda:0",
        ],
        wait=False,
    )
    script_processor_job_description = script_processor.jobs[-1].describe()
    print(script_processor_job_description)
    return {"message": "Hello Foo!"}


@router_bar.get("/bar")
def bar():
    return JSONResponse({"message": "Hello Bar!"})


app.include_router(router_foo)
app.include_router(router_bar)

handler_foo = Mangum(router_foo)
handler_bar = Mangum(router_bar)
