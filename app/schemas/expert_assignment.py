"""Schema Pydantic untuk entitas ExpertAssignment."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AssignmentCreate(BaseModel):
    """Schema request untuk menugaskan expert ke instrumen.

    Attributes:
        user_id: ID expert yang akan ditugaskan.
        deadline: Batas waktu penilaian (opsional).
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "deadline": "2026-06-30T23:59:59",
            }
        }
    )

    user_id: str
    deadline: datetime | None = None


class AssignmentResponse(BaseModel):
    """Schema response untuk data assignment.

    Attributes:
        id: ID unik assignment.
        instrument_id: ID instrumen.
        user_id: ID expert.
        assigned_by: ID admin yang melakukan assign.
        deadline: Batas waktu penilaian.
        status: Status assignment (pending/in_progress/completed).
        assigned_at: Waktu penugasan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "assigned_by": "f6a7b8c9-d0e1-2345-fab6-789012345678",
                "deadline": "2026-06-30T23:59:59",
                "status": "pending",
                "assigned_at": "2026-05-01T09:00:00",
                "updated_at": "2026-05-01T09:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    user_id: str
    assigned_by: str
    deadline: datetime | None
    status: str
    assigned_at: datetime
    updated_at: datetime
