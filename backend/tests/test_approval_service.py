from services.approval_service import ApprovalService
from unittest.mock import Mock


def test_approval_is_single_use_and_bound_to_target():
    service = ApprovalService()
    approval = service.create("write_file", "notes.md")

    assert service.consume(approval["approval_id"], "write_file", "other.md") is False
    assert service.consume(approval["approval_id"], "write_file", "notes.md") is True

    second = service.create("write_file", "notes.md")
    assert service.consume(second["approval_id"], "write_file", "notes.md") is True
    assert service.consume(second["approval_id"], "write_file", "notes.md") is False


def test_consume_for_request_validates_binding_and_is_single_use():
    service = ApprovalService()
    policy = Mock()
    policy.authorize_approval_consumption.return_value = Mock(allowed=True)
    approval = service.create(
        "write_file",
        "notes.md",
        owner_id="user-1",
        workspace_id="workspace-1",
    )

    assert service.consume_for_request(
        approval["approval_id"],
        "write_file",
        "notes.md",
        owner_id="user-1",
        workspace_id="workspace-1",
        policy=policy,
    ) is True
    assert service.consume_for_request(
        approval["approval_id"],
        "write_file",
        "notes.md",
        owner_id="user-1",
        workspace_id="workspace-1",
        policy=policy,
    ) is False


def test_consume_for_request_rejects_wrong_binding_before_consuming():
    service = ApprovalService()
    policy = Mock()
    policy.authorize_approval_consumption.return_value = Mock(allowed=False)
    approval = service.create(
        "write_file",
        "notes.md",
        owner_id="user-1",
        workspace_id="workspace-1",
    )

    assert service.consume_for_request(
        approval["approval_id"],
        "write_file",
        "notes.md",
        owner_id="user-2",
        workspace_id="workspace-1",
        policy=policy,
    ) is False
    assert service.consume(
        approval["approval_id"],
        "write_file",
        "notes.md",
        owner_id="user-1",
        workspace_id="workspace-1",
    ) is True