from typing import Literal, Optional, Tuple

MS_CALLERS_MAP = {
    "autorizador": "http://m-autorizador:5003",
    "monitor": "http://m-monitor:5001",
    "logistica-inventario": "http://m-logistica-inventario:5002",
}


def call_ms(
    name: Literal["autorizador", "monitor", "logistica-inventarios"],
    resource,
    method: Literal["get", "post", "put", "delete"] = "get",
    data: 'Optional[dict]' = None,
    params: 'Optional[dict]' = None,
    headers: 'Optional[dict]' = None,
) -> Tuple[dict, int]:
    """Llama a otro microservicio y maneja errores comunes"""
    import requests
    from requests.exceptions import RequestException

    base_url = MS_CALLERS_MAP.get(name)
    if not base_url:
        return {"error": f"Microservicio no encontrado: {name}"}, 404

    url = f"{base_url}{resource}"

    try:
        if method.lower() == "get":
            response = requests.get(url, params=params, headers=headers)
        elif method.lower() == "post":
            response = requests.post(url, json=data, headers=headers)
        elif method.lower() == "put":
            response = requests.put(url, json=data, headers=headers)
        elif method.lower() == "delete":
            response = requests.delete(url, headers=headers)
        else:
            return {"error": f"Método HTTP no soportado: {method}"}, 400

        response.raise_for_status()  # Lanza un error para códigos de estado 4xx/5xx
        return {"data": response.json() }, response.status_code
    except RequestException as e:
        print(f"Error llamando al microservicio {name}: {e}")
        return {"error": str(e)}, 500
    except ValueError as ve:
        print(f"Error de valor: {ve}")
        return {"error": str(ve)}, 400
