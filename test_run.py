import logging
from botocore.exceptions import ClientError
import uuid


logger = logging.getLogger(__name__)

TEST_SUITES = {
    "mbpp": {"dataset": "mbpp", "metric_name": "pass@k"},
}


class TestRun:
    """Encapsulates an Amazon DynamoDB table of test run data."""

    def __init__(self, dyn_resource):
        """
        :param dyn_resource: A Boto3 DynamoDB resource.
        """
        self.table = dyn_resource.Table("test_suite_runs")

    @staticmethod
    def create_table(dyn_resource):
        """
        Creates an Amazon DynamoDB table that can be used to test suite run data

        :param dyn_resource: the boto3 resource
        :return: The newly created table.
        """
        try:
            table = dyn_resource.create_table(
                TableName="test_suite_runs",
                KeySchema=[
                    {"AttributeName": "userkey", "KeyType": "HASH"},  # Partition key
                    {"AttributeName": "id", "KeyType": "RANGE"},  # Sort key
                ],
                AttributeDefinitions=[
                    {"AttributeName": "userkey", "AttributeType": "S"},
                    {"AttributeName": "id", "AttributeType": "S"},
                ],
                ProvisionedThroughput={
                    "ReadCapacityUnits": 10,
                    "WriteCapacityUnits": 10,
                },
            )
            table.wait_until_exists()
            return table
        except ClientError as err:
            logger.error(
                "Couldn't create table test_suite_runs. Here's why: %s: %s",
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def add_test_run(self, userkey, model_name, test_suite):
        """
        Adds a test run to the table. Currently just adds a pending test to be updated.

        :param model_name: model repo name in huggingface eg. bigcode/santacoder
        :param test_suite: constant that points to a test suite eg. mbpp
        """
        try:
            self.table.put_item(
                Item={
                    "userkey": userkey,
                    "id": str(uuid.uuid4()),
                    "model_name": model_name,
                    **TEST_SUITES[test_suite],
                    "status": "pending",
                    "metric_value": 0.0,
                    "failed_generations": [],
                    "failed_indices": [],
                }
            )
        except ClientError as err:
            logger.error(
                "Error adding TestRun with model_name %s to table %s: %s: %s",
                model_name,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise

    def get_test_run(self, userkey, run_id):
        """
        Gets TestRun data from the table for a specific user.

        :param userkey: userkey of the user
        :param run_id: uuid
        :return: The data about the requested test run.
        """
        try:
            response = self.table.get_item(Key={"userkey": userkey, "id": run_id})
        except ClientError as err:
            logger.error(
                "Error fetching TestRun with userkey %s from table %s: %s: %s",
                userkey,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Item"]

    def update_test_run(self, userkey, run_id, metric_value):
        """
        Updates metric value data for a test run in the table.

        :param userkey: anonymously represents a user
        :param run_id: uuid that uniquely identifies a test run
        :param metric_value: test suite metric output eg. 0.89
        :return: The fields that were updated, with their new values.
        """
        try:
            response = self.table.update_item(
                Key={"userkey": userkey, "id": run_id},
                UpdateExpression="set status=:s, metric_value=:mv",
                ExpressionAttributeValues={":s": "complete", ":mv": metric_value},
                ReturnValues="UPDATED_NEW",
            )
        except ClientError as err:
            logger.error(
                "Error updating TestRun with userkey %s to table %s: %s: %s",
                userkey,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
        else:
            return response["Attributes"]

    def delete_test_run(self, userkey, run_id):
        """
        Deletes a test run from the table.

        :param model_name: model repo name in huggingface eg. bigcode/santacoder
        :param test_suite: constant that points to a test suite eg. mbpp
        """
        try:
            self.table.delete_item(
                Key={"userkey": userkey, "id": run_id},
            )
        except ClientError as err:
            logger.error(
                "Error deleting TestRun with run_id %s to table %s: %s: %s",
                run_id,
                self.table.name,
                err.response["Error"]["Code"],
                err.response["Error"]["Message"],
            )
            raise
