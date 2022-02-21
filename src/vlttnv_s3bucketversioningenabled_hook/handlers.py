import logging
from typing import Any, MutableMapping, Optional

from cloudformation_cli_python_lib import (
    BaseHookHandlerRequest,
    HandlerErrorCode,
    Hook,
    HookInvocationPoint,
    OperationStatus,
    ProgressEvent,
    SessionProxy,
    exceptions,
)

from .models import HookHandlerRequest, TypeConfigurationModel

LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
TYPE_NAME = "Vlttnv::S3BucketVersioningEnabled::Hook"

hook = Hook(TYPE_NAME, TypeConfigurationModel)
test_entrypoint = hook.test_entrypoint

def _isBucketExcluded(bucketName: str, excludedBucketSuffixes: str):
    suffixesToExclude = [suffix.strip() for suffix in excludedBucketSuffixes.split(',')]
    for suffix in suffixesToExclude:
        LOG.info(f'**Checking if bucket name {bucketName} starts with {suffix}')
        if suffix and bucketName.startswith(suffix):
            return True
    return False


def _validate_object_versioning(s3Bucket: MutableMapping[str, Any], excludedBucketSuffixes: str) -> ProgressEvent:
    status = OperationStatus.SUCCESS
    message = ""
    error_code = None

    LOG.info(s3Bucket)
    s3BucketName = s3Bucket.get("BucketName")

    if s3BucketName and _isBucketExcluded(s3BucketName, excludedBucketSuffixes):
        status = OperationStatus.SUCCESS
        message = f"Object versioning is not required for bucket named: {s3BucketName}."

    version_configuration = s3Bucket.get("VersioningConfiguration")
    if version_configuration is None or version_configuration.get("Status") != "Enabled":
        status = OperationStatus.FAILED
        message = f"S3 bucket {s3BucketName} does not have object versioning enabled."

    LOG.info(f"{status} - {message}")
    return ProgressEvent(
        status=status,
        message=message,
        errorCode=error_code
    )


@hook.handler(HookInvocationPoint.CREATE_PRE_PROVISION)
def pre_create_handler(
        session: Optional[SessionProxy],
        request: HookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:
    target_model = request.hookContext.targetModel
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS
    )
    target_name = request.hookContext.targetName
    try:
        if "AWS::S3::Bucket" == target_name:
            progress = _validate_object_versioning(
                request.hookContext.targetModel.get("resourceProperties"), 
                type_configuration.excludedBucketSuffixes,
            )
        else:
            raise exceptions.InvalidRequest(f"Unknown target type: {target_name}")

    except exceptions.InvalidRequest as e:
        progress.status = OperationStatus.FAILED
        progress.message = "Unknown target type: {target_name}"
    except BaseException as e:
        progress = ProgressEvent.failed(HandlerErrorCode.InternalFailure, f"Unexpected error {e}")

    return progress


@hook.handler(HookInvocationPoint.UPDATE_PRE_PROVISION)
def pre_update_handler(
        session: Optional[SessionProxy],
        request: BaseHookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:
    target_model = request.hookContext.targetModel
    progress: ProgressEvent = ProgressEvent(
        status=OperationStatus.IN_PROGRESS
    )

    target_name = request.hookContext.targetName
    try:
        if "AWS::S3::Bucket" == target_name:
            progress = _validate_object_versioning(
                request.hookContext.targetModel.get("resourceProperties"), 
                type_configuration.excludedBucketSuffixes,
            )
        else:
            raise exceptions.InvalidRequest(f"Unknown target type: {target_name}")

    except exceptions.InvalidRequest as e:
        progress.status = OperationStatus.FAILED
        progress.message = "Unknown target type: {target_name}"
    except BaseException as e:
        progress = ProgressEvent.failed(HandlerErrorCode.InternalFailure, f"Unexpected error {e}")

    return progress


@hook.handler(HookInvocationPoint.DELETE_PRE_PROVISION)
def pre_delete_handler(
        session: Optional[SessionProxy],
        request: BaseHookHandlerRequest,
        callback_context: MutableMapping[str, Any],
        type_configuration: TypeConfigurationModel
) -> ProgressEvent:
    return ProgressEvent(
        status=OperationStatus.SUCCESS
    )
