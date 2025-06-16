from flask import Flask, request, jsonify
import os
from ocr_analyzer import analyze_contract_with_ocr
from langchain_ollama_analyzer import mainLangChain

app = Flask(__name__)

UPLOAD_FOLDER = 'contract'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file:
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)
        response =main(os.path.abspath(filename))  # Call the main function with the filename without extension
        return jsonify({'message': 'File uploaded successfully', 'filename': filename,
                        'resultInfo':response}), 200
    else:
        return jsonify({'error': 'File upload failed'}), 400
    r


def main(name):
    # os.environ["TESSDATA_PREFIX"] = 'tessdata/'
    # Example usage
    # converter = readPdf.PDFToTextConverter(language='rus+eng+kaz')  # Use 'eng+fra' for English and French

    try:
        # txtFilePath=name
        # # 'contract/scan_txt/'+name+'.txt'
        # # Convert PDF to text
        # extracted_text = converter.convert_pdf_to_text(txtFilePath)
        # print("Conversion completed successfully!")

        # # Print first 500 characters of extracted text as preview
        # print("\nPreview of extracted text:")
        # print(extracted_text[:500] + "...")

        fileName = mainLangChain(name)
        content=''
        with open(fileName, 'r') as file:
            content = file.read()
        return content

    except Exception as e:
        print(f"Error: {str(e)}")
if __name__ == '__main__':
    app.run(debug=True, port=8081)