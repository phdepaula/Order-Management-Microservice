from urllib.parse import unquote

import requests
from flask_openapi3 import Tag

from app import app, log
from schemas.external_api import (ExternalApiResultSchema, ExternalApiSchema,
                                  SingleMessageSchema)

TAG_EXTERNAL_API = Tag(
    name="Via Cep External API",
    description="Query to the external ViaCep API \
    that allows obtaining all address information \
    associated with a provided Brazilian zip code.",
)


@app.get(
    "/get_viacep/",
    tags=[TAG_EXTERNAL_API],
    responses={
        "200": ExternalApiResultSchema,
        "400": SingleMessageSchema,
    },
)
def query_viacep_external_api(query: ExternalApiSchema):
    """
    External API query route ViaCep
    """
    log.add_message("Get_viacep route accessed")

    zip_code = unquote(unquote(query.zip_code))

    try:
        log.add_message("Querying viacep external API")

        url = f"https://viacep.com.br/ws/{zip_code}/json/"
        response = requests.get(url)

        if response.status_code != 200:
            raise Exception("Error when querying the Via Cep API")

        data = response.json()

        if data.get("erro"):
            raise Exception("Zip code not found")

        log.add_message("API consulted successfully")

        return_data = {"message": "Success", "data": data}

        log.add_message(f"Get_viacep response: {return_data}")
        log.add_message("Get_viacep status: 200")
        log.add_message("")

        return return_data, 200
    except Exception as error:
        return_data = {"message": f"Error: {error}"}

        log.add_message(f"Get_viacep response: {return_data}")
        log.add_message("Get_viacep status: 400")
        log.add_message("")

        return return_data, 400
