# Korean Character Template Generator

This tool generates printable template pages for writing Korean characters. The template is designed to be used for collecting handwritten samples of Korean characters for font style analysis.

## Features

- Generates template pages with grid cells for each Korean character
- Includes Unicode values and reference characters
- Organizes characters by categories
- Creates multiple pages as needed
- Optimized for A4 printing at 300dpi

## Files

- `template_generator.py` - Main script that generates the templates
- `korean_reference_chars.py` - Contains the Korean characters to be included
- `NanumGothic.ttf` - Font file used for rendering characters
- `Dockerfile` - For containerized execution

## Usage

### Running locally

1. Make sure you have Python installed with Pillow library:
   ```
   pip install pillow
   ```

2. Run the template generator:
   ```
   python template_generator.py
   ```

3. Find the generated templates in the `output_templates` directory.

### Running in Docker container

1. Build the Docker image:
   ```
   docker build -t korean-template-generator .
   ```

2. Run the container:
   ```
   docker run -v $(pwd)/output_templates:/app/output_templates korean-template-generator
   ```

3. Find the generated templates in the `output_templates` directory.

## Template Format

Each template page includes:
- A header with the category title
- Grid cells for each character
- Reference character in each cell
- Unicode value for each character
- Guidelines for writing the character

## Output

The script generates multiple pages:
- One or more pages for each character category
- A reference page with all characters

## Customization

You can customize the template by modifying the constants at the top of `template_generator.py`:
- `PAGE_WIDTH` and `PAGE_HEIGHT` - Page dimensions
- `MARGIN` - Page margins
- `GRID_SIZE` - Size of each character cell
- `CHARS_PER_ROW` and `ROWS_PER_PAGE` - Layout configuration
- `FONT_SIZE` - Size of the reference characters

## License

Free to use for font style collection and analysis. 