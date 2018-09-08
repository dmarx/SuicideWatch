"""
Via https://stackoverflow.com/a/39225039/819544
"""

import requests

def download_file_from_google_drive(id, destination):
    def get_confirm_token(response):
        for key, value in response.cookies.items():
            if key.startswith('download_warning'):
                return value

        return None

    def save_response_content(response, destination):
        CHUNK_SIZE = 32768

        with open(destination, "wb") as f:
            for chunk in response.iter_content(CHUNK_SIZE):
                if chunk: # filter out keep-alive new chunks
                    f.write(chunk)

    URL = "https://docs.google.com/uc?export=download"

    session = requests.Session()

    response = session.get(URL, params = { 'id' : id }, stream = True)
    token = get_confirm_token(response)

    if token:
        params = { 'id' : id, 'confirm' : token }
        response = session.get(URL, params = params, stream = True)

    save_response_content(response, destination)

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Download database from drive.')
    parser.add_argument('--file-id', default='1o5vjzSi2eeAlvAdwKeR30IDgCvqJTaW7',
                    help='File ID defined in shareable URL.')
    parser.add_argument('--out-path', default='/home/SuicideWatch/data/scrape_results.db',
                    help='File ID defined in shareable URL.')

    args = parser.parse_args()
    download_file_from_google_drive(args.file_id, args.out_path)
