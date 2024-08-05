from datetime import datetime
from typing import Optional

from fastapi.encoders import ENCODERS_BY_TYPE
from pydantic import BaseModel, ConfigDict, Field


class JWT(BaseModel):
    model_config = ConfigDict(
        extra="allow",
        json_encoders={**ENCODERS_BY_TYPE, datetime: lambda v: int(v.timestamp())},
    )
    iss: Optional[str] = Field(None, description="Issuer")
    sub: Optional[str] = Field(None, description="Subject")
    aud: Optional[str] = Field(None, description="Audience")
    exp: Optional[datetime] = Field(None, description="Expiration time")
    nbf: Optional[datetime] = Field(None, description="Not before time")
    iat: Optional[datetime] = Field(None, description="Issued at time")
    jti: Optional[str] = Field(None, description="JWT ID")
