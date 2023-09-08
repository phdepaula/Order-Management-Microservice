from pydantic import BaseModel


class ExternalApiSchema(BaseModel):
    """
    Defines the parameters that must be \
    entered to query the external API
    """

    zip_code: str


class ExternalApiResultSchema(BaseModel):
    """
    Defines how the API response should be \
    for a successful query.
    """

    message: str
    product: dict


class SingleMessageSchema(BaseModel):
    """
    Defines how the API response should be \
    when you want to send just one message.
    """

    message: str
