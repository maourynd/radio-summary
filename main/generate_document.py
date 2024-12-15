import re

def generate_html_document(content: str) -> str:
    # Convert the content into HTML paragraphs and lists
    lines = content.split('\n')

    html_lines = []
    in_list = False

    for line in lines:
        stripped = line.strip()
        # Detect numbered list items (e.g., "1.", "2.", etc.)
        match = re.match(r"^(\d+)\.\s*(.*)", stripped)
        if match:
            # We found a numbered list item
            number = match.group(1)  # The number (e.g., "1")
            item_text = match.group(2)  # The rest of the text
            # Apply bolding for text wrapped in **
            item_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", item_text)

            if not in_list:
                html_lines.append('<ol style="margin:0; padding:0 0 0 20px;">')
                in_list = True
            html_lines.append(f'<li style="margin-bottom:5px;" value="{number}">{item_text}</li>')
        else:
            if in_list:
                # Close the list if we were in one and now encountered a non-list line
                html_lines.append('</ol>')
                in_list = False
            if stripped:
                # Apply bolding for text wrapped in **
                stripped = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", stripped)
                html_lines.append(
                    f'<p style="margin-bottom:10px; font-family:sans-serif; font-size:14px; line-height:1.5;">{stripped}</p>'
                )

    # If the last lines were part of a list, close the list
    if in_list:
        html_lines.append('</ol>')

    # Create the HTML template
    html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Newsletter</title>
<style>
  body {{
    font-family: Arial, Helvetica, sans-serif;
    color: #333333;
    background-color: #ffffff;
    margin: 20px;
  }}
  h1 {{
    font-size: 24px;
    margin-bottom: 20px;
  }}
</style>
</head>
<body>
<h1>Recent Police Scanner Highlights</h1>
{"".join(html_lines)}
</body>
</html>
"""
    return html_template
