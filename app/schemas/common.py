"""Schema Pydantic umum yang digunakan di seluruh aplikasi."""

from pydantic import BaseModel, ConfigDict


class MessageResponse(BaseModel):
    """Schema response generik berisi pesan teks.

    Attributes:
        message: Pesan yang dikembalikan.
    """

    model_config = ConfigDict(json_schema_extra={"example": {"message": "Operasi berhasil."}})

    message: str
