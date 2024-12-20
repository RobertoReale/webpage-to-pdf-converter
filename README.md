# Webpage to PDF Converter

A Python application that converts multiple webpages to PDF files using Selenium and Chrome. The application features a graphical user interface built with tkinter and supports batch processing of URLs from multiple files with different output directories.

## Features

- Graphical user interface for easy operation
- Support for multiple URL files with separate output directories
- Progress tracking with pause/resume functionality
- Robust error handling and recovery
- Configurable Chrome settings
- Support for dynamic content loading
- Automatic retry mechanism for PDF generation

## Requirements

- Python 3.7+
- Google Chrome browser
- ChromeDriver compatible with your Chrome version
- Required Python packages (see requirements.txt)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/webpage-to-pdf-converter.git
cd webpage-to-pdf-converter
```

2. Create and activate a virtual environment (optional but recommended):
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Ensure you have Google Chrome installed and the appropriate ChromeDriver in your system PATH.

## Usage

1. Run the application:
```bash
python webpage_to_pdf.py
```

2. In the application:
   - Click "Add URL File & Directory" to select a text file containing URLs and its corresponding output directory
   - You can add multiple URL files, each with its own output directory
   - Use "Remove Selected" to remove any file-directory pair from the list
   - Click "Start" to begin the conversion process
   - Use "Pause" to temporarily pause the process and "Stop" to cancel it

### Important Usage Notes

⚠️ **Please read these important notes before using the application:**

1. **Initial Chrome Setup**
   - When the Chrome window first appears, make any necessary configurations quickly
   - Click "OK" promptly after configuration to start the download process
   - Do NOT close or interfere with the initial blank page (data:,) as this will break the program

2. **Browser Management**
   - It is strongly recommended to close all other Chrome tabs before starting
   - Only keep the tabs opened by the program running
   - Do not interact with the browser while the program is running

3. **File Path Considerations**
   - Choose output directories with relatively short file paths
   - Long file paths may cause errors in file saving
   - Avoid deep nested folders for output directories

4. **File Naming**
   - The program uses a basic file naming system based on timestamps and URLs
   - No special attention is paid to file name conflicts or special characters
   - Files are named automatically without user input

### URL File Format

The URL files should contain one URL per line, for example:
```
https://www.example.com
https://www.example.org/page1
https://www.example.net/article
```

## Best Practices

1. **Before Starting**
   - Close unnecessary Chrome windows and tabs
   - Choose output directories with short paths
   - Prepare URL files with valid, accessible URLs

2. **During Operation**
   - Don't interact with the Chrome window
   - Let the program handle all browser operations
   - Use the GUI controls (Pause/Stop) if you need to interrupt the process

3. **After Completion**
   - Verify the generated PDFs
   - Check the status messages for any errors
   - Close the program properly when done

## Configuration

The application provides several configurable parameters in the code:

- PDF page size and margins
- Viewport sizes for better content capture
- Wait times for dynamic content
- Retry attempts for PDF generation
- Chrome browser settings

## Troubleshooting

### Common Issues

1. Chrome initialization fails:
   - Ensure ChromeDriver is installed and matches your Chrome version
   - Check if Chrome is properly installed
   - Make sure no other Chrome processes are interfering

2. PDFs are not generated:
   - Check if the URLs are accessible
   - Ensure you have write permissions in the output directory
   - Try increasing the wait time for dynamic content
   - Verify that the initial blank page hasn't been closed

3. PDF content is incomplete:
   - Adjust the viewport size settings
   - Increase the wait time for dynamic content
   - Check if the website requires authentication

4. File saving errors:
   - Choose a different output directory with a shorter path
   - Ensure adequate disk space
   - Check write permissions

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
