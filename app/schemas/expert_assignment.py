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
        instrument_name: Nama instrumen terkait (None jika tidak tersedia).
        user_id: ID expert.
        assigned_by: ID admin yang melakukan assign.
        deadline: Batas waktu penilaian.
        status: Status assignment (pending/in_progress/completed/archived).
        is_active: True jika penilaian diperhitungkan dalam kalkulasi CVI; False jika
            dinonaktifkan admin (data tetap tersimpan, tidak dihitung).
        previous_assignment_id: ID assignment sebelumnya yang diarsipkan (None jika bukan revisi).
        revision_number: Nomor revisi dimulai dari 1.
        assigned_at: Waktu penugasan.
        updated_at: Waktu terakhir diperbarui.
    """

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "instrument_id": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
                "instrument_name": "Skala Motivasi Belajar",
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "assigned_by": "f6a7b8c9-d0e1-2345-fab6-789012345678",
                "deadline": "2026-06-30T23:59:59",
                "status": "in_progress",
                "is_active": True,
                "previous_assignment_id": None,
                "revision_number": 1,
                "assigned_at": "2026-05-01T09:00:00",
                "updated_at": "2026-05-01T09:00:00",
            }
        },
    )

    id: str
    instrument_id: str
    instrument_name: str | None = None
    user_id: str
    assigned_by: str
    deadline: datetime | None
    status: str
    is_active: bool = True
    previous_assignment_id: str | None = None
    revision_number: int = 1
    assigned_at: datetime
    updated_at: datetime


class RevisionResult(BaseModel):
    """Schema response untuk operasi pengarsipan dan pembuatan revisi assignment.

    Attributes:
        archived_assignment: Assignment lama yang telah diarsipkan.
        new_assignment: Assignment baru dengan salinan isian sebelumnya.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "archived_assignment": {
                    "id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                    "status": "archived",
                    "revision_number": 1,
                },
                "new_assignment": {
                    "id": "e5f6a7b8-c9d0-1234-efab-345678901234",
                    "status": "in_progress",
                    "previous_assignment_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                    "revision_number": 2,
                },
            }
        }
    )

    archived_assignment: AssignmentResponse
    new_assignment: AssignmentResponse
