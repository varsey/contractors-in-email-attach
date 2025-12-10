import pdfkit

from src.logger.Logger import log

config = pdfkit.configuration(wkhtmltopdf='/usr/local/bin/wkhtmltopdf')


# https://dev.to/vb64/converting-markdown-to-pdf-in-python-5efn
# convert to html first with img url
def generate_pdf(text_collection: dict) -> list:
    result_names = []
    # https://www.syntaxis.be/blog/the-blog-1/post/install-wkhtmltopdf-0-12-5-on-ubuntu-20-04-6
    for fullname, text in text_collection.items():
        name = f'{fullname[:5]}.pdf'
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
        </head>
        <body>
            <p>{text}</p>
        <body>
        </html>
        """
        pdfkit.from_string(html_content, f"{name}", configuration=config)
        print(f'PDF {name} generated')
        result_names.append(name)
    return result_names
