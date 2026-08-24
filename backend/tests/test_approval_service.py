from services.approval_service import ApprovalService


def test_approval_is_single_use_and_bound_to_target():
    service = ApprovalService()
    approval = service.create("write_file", "notes.md")

    assert service.consume(approval["approval_id"], "write_file", "other.md") is False
    assert service.consume(approval["approval_id"], "write_file", "notes.md") is True

    second = service.create("write_file", "notes.md")
    assert service.consume(second["approval_id"], "write_file", "notes.md") is True
    assert service.consume(second["approval_id"], "write_file", "notes.md") is False