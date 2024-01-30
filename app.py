import streamlit as st
import requests
import json
import zipfile
from io import BytesIO

# Función para obtener los datos del reclamo
def get_document_from_pod(claim_id, token):
    url = f"https://b2b.taxi.yandex.net/b2b/cargo/integration/v2/claims/proof-of-delivery/info?claim_id={claim_id}"
    headers = {
        'Authorization': f"Bearer {token}",
        'Content-Type': 'application/json',
        'Accept-Language': 'en'
    }
    response = requests.post(url, headers=headers)
    return json.loads(response.text)

# Función para crear un ZIP con las fotos de un claim
def create_zip(photos, claim_id):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for i, photo in enumerate(photos):
            photo_response = requests.get(photo["url"])
            if photo_response.status_code == 200:
                file_name = f"{claim_id}-{i+1}.jpg"
                zip_file.writestr(file_name, photo_response.content)

    zip_buffer.seek(0)
    return zip_buffer

# Función para crear un ZIP con todas las fotos de todos los claims
def create_zip_for_all_claims(claim_data):
    zip_buffer_all = BytesIO()
    with zipfile.ZipFile(zip_buffer_all, 'w', zipfile.ZIP_DEFLATED) as zip_file_all:
        for claim_id, data in claim_data.items():
            if "proof_of_delivery_info" in data:
                for info in data["proof_of_delivery_info"]:
                    if "photos" in info:
                        for i, photo in enumerate(info["photos"]):
                            photo_response = requests.get(photo["url"])
                            if photo_response.status_code == 200:
                                file_name = f"{claim_id}-{i+1}.jpg"
                                zip_file_all.writestr(file_name, photo_response.content)
    zip_buffer_all.seek(0)
    return zip_buffer_all

# Función principal de la aplicación Streamlit
def main():
    st.title("Consulta y descarga POD")

    token = st.text_input("Token de API:")
    claim_ids_input = st.text_input("Claim IDs (separados por comas):")
    
    if token and claim_ids_input:
        claim_ids = claim_ids_input.split(',')
        claim_data = {}
        for claim_id in claim_ids:
            data = get_document_from_pod(claim_id.strip(), token)
            claim_data[claim_id] = data

        for claim_id, data in claim_data.items():
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.button(f"Mostrar fotos para claim {claim_id}"):
                    pass
            with col2:
                if "proof_of_delivery_info" in data:
                    for info in data["proof_of_delivery_info"]:
                        if "photos" in info:
                            photos = info["photos"]
                            zip_buffer = create_zip(photos, claim_id)
                            st.download_button(label="Descargar fotos como ZIP",
                                               data=zip_buffer,
                                               file_name=f"{claim_id}_fotos.zip",
                                               mime="application/zip")

            if "Mostrar fotos para claim" in st.session_state and st.session_state[f"Mostrar fotos para claim {claim_id}"]:
                if "proof_of_delivery_info" in data:
                    for info in data["proof_of_delivery_info"]:
                        if "photos" in info:
                            photos = info["photos"]
                            for photo in photos:
                                st.image(photo["url"], caption=f"Foto de claim {claim_id}")
                else:
                    st.write(f"No se encontraron fotos para el claim {claim_id}")

        # Botón para descargar todas las fotos de todos los claims
        if st.button("Descargar todas las fotos"):
            all_photos_zip_buffer = create_zip_for_all_claims(claim_data)
            st.download_button(label="Descargar todas las fotos como ZIP",
                               data=all_photos_zip_buffer,
                               file_name="todas_las_fotos.zip",
                               mime="application/zip")

if __name__ == "__main__":
    main()
