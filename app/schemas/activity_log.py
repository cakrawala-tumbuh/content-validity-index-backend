"""Schema Pydantic untuk entitas ActivityLog."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ActivityLogResponse(BaseModel):
    """Schema response untuk satu entri activity log.

    Attributes:
        id: ID unik log.
        user_id: ID pengguna yang melakukan aksi.
        action: Nama aksi yang dilakukan.
        resource_type: Tipe resource yang dioperasikan.
        resource_id: ID resource yang dioperasikan.
        ip_address: Alamat IP pengguna.
        user_agent: User-agent browser/klien.
        metadata_: Data tambahan terkait aksi.
        created_at: Waktu aksi dilakukan.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "f6a7b8c9-d0e1-2345-fab6-789012345678",
                "user_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "action": "submit_rating",
                "resource_type": "assignment",
                "resource_id": "d4e5f6a7-b8c9-0123-defa-234567890123",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0",
                "metadata_": {"n_ratings": 20},
                "created_at": "2026-05-10T14:00:00",
            }
        },
    )

    id: str
    user_id: str | None
    action: str
    resource_type: str | None
    resource_id: str | None
    ip_address: str
    user_agent: str | None
    metadata_: dict[str, Any] | None
    created_at: datetime
