import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
import json
import time
import os
import base64
from datetime import datetime
import threading

class WebPageToPDFConverter:
    def __init__(self):
        self.driver = None
        self.paused = False
        self.processing = False
        self.processed_urls = set()
        self.current_url = ""
        self.url_files_and_dirs = []  # List of tuples (url_file, output_dir)
        self.recovery_file = None
        self.total_urls = 0
        self.processed_count = 0
        self.stop_requested = False
        self.driver_lock = threading.Lock()
        
        self.create_gui()

    def create_gui(self):
        """Create the main GUI window"""
        self.root = tk.Tk()
        self.root.title("Webpage to PDF Converter")
        self.root.geometry("600x400")
        self.root.resizable(True, True)

        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # File selection frame
        file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding="5")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        file_frame.columnconfigure(1, weight=1)

        # List of URL files and directories
        self.files_listbox = tk.Listbox(file_frame, height=5)
        self.files_listbox.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Add and Remove buttons
        button_frame = ttk.Frame(file_frame)
        button_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Button(button_frame, text="Add URL File & Directory", command=self.add_url_file_and_dir).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Remove Selected", command=self.remove_selected).pack(side=tk.LEFT, padx=5)

        # Progress frame
        progress_frame = ttk.LabelFrame(main_frame, text="Progress", padding="5")
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        progress_frame.columnconfigure(0, weight=1)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, length=300, mode='determinate', variable=self.progress_var)
        self.progress_bar.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.status_var, wraplength=550)
        self.status_label.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)

        # Current URL label
        self.url_var = tk.StringVar(value="")
        self.url_label = ttk.Label(progress_frame, textvariable=self.url_var, wraplength=550)
        self.url_label.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=5)

        # Control buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        self.start_button = ttk.Button(button_frame, text="Start", command=self.start_conversion)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.toggle_pause, state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Stop", command=self.stop_conversion, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)

    def add_url_file_and_dir(self):
        """Add a URL file and its corresponding output directory"""
        url_file = filedialog.askopenfilename(
            title="Select URLs File",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if url_file:
            output_dir = filedialog.askdirectory(title="Select Output Folder for " + os.path.basename(url_file))
            if output_dir:
                self.url_files_and_dirs.append((url_file, output_dir))
                self.files_listbox.insert(tk.END, f"{os.path.basename(url_file)} -> {os.path.basename(output_dir)}")

    def remove_selected(self):
        """Remove the selected URL file and directory pair"""
        selection = self.files_listbox.curselection()
        if selection:
            index = selection[0]
            self.files_listbox.delete(index)
            self.url_files_and_dirs.pop(index)

    def wait_for_page_load(self, timeout=30):
        """Wait for page load with better detection of dynamic content"""
        try:
            # Wait for the initial page load
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Wait for network requests to finish
            time.sleep(2)
            
            # Try to ensure dynamic content is loaded by checking document.readyState
            ready_state_script = "return document.readyState"
            start_time = time.time()
            while time.time() - start_time < timeout:
                state = self.driver.execute_script(ready_state_script)
                if state == "complete":
                    # Additional wait for any final dynamic content
                    time.sleep(2)
                    return True
                time.sleep(0.5)
            
            return False
        except Exception as e:
            self.status_var.set(f"Error waiting for page load: {str(e)}")
            return False

    def generate_pdf_with_retry(self, max_retries=3):
        """Generate PDF with multiple retries and different strategies"""
        for attempt in range(max_retries):
            try:
                # Try with different viewport sizes on each attempt
                viewport_heights = [900, 1200, 1500]
                self.driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride', {
                    'width': 1200,
                    'height': viewport_heights[attempt % len(viewport_heights)],
                    'deviceScaleFactor': 1,
                    'mobile': False
                })

                # Wait for any resize effects
                time.sleep(1)

                # PDF generation parameters
                pdf_params = {
                    'printBackground': True,
                    'paperWidth': 8.27,  # A4
                    'paperHeight': 11.69,
                    'marginTop': 0.4,
                    'marginBottom': 0.4,
                    'marginLeft': 0.4,
                    'marginRight': 0.4,
                    'scale': 0.9,
                    'preferCSSPageSize': True
                }

                # Generate PDF
                result = self.driver.execute_cdp_cmd('Page.printToPDF', pdf_params)
                
                if not isinstance(result, dict) or 'data' not in result:
                    raise Exception("Invalid PDF data structure received")
                
                try:
                    pdf_bytes = base64.b64decode(result['data'])
                    if len(pdf_bytes) < 1024:  # Less than 1KB
                        raise Exception("Generated PDF is too small")
                    return pdf_bytes
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise Exception(f"PDF generation failed: {str(e)}")
                    continue

            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"All PDF generation attempts failed: {str(e)}")
                time.sleep(2)  # Wait before retry
                continue
        
        raise Exception("PDF generation failed after all attempts")

    def save_as_pdf(self, url):
        """Convert webpage to PDF with improved reliability"""
        try:
            if not self.driver:
                raise Exception("Browser not initialized")

            self.current_url = url
            self.url_var.set(f"Processing: {url}")
            
            # Load the page
            self.driver.get(url)
            if not self.wait_for_page_load(timeout=30):
                raise Exception("Page load timeout")

            # Generate PDF with retry mechanism
            pdf_bytes = self.generate_pdf_with_retry()
            
            # Create filename from URL
            safe_url = url.split('//')[-1].replace('/', '_')
            safe_url = ''.join(c for c in safe_url if c.isalnum() or c in '_-.')[:100]
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{safe_url}.pdf"
            filepath = os.path.join(self.output_dir, filename)
            
            # Save PDF
            with open(filepath, 'wb') as f:
                f.write(pdf_bytes)
            
            # Verify file size
            file_size = os.path.getsize(filepath)
            if file_size < 1024:  # Less than 1KB
                os.remove(filepath)  # Delete invalid file
                raise Exception("Generated PDF is too small")
            
            self.status_var.set(f"Saved: {filename} ({file_size/1024:.1f} KB)")
            return True
            
        except Exception as e:
            self.status_var.set(f"Error processing {url}: {str(e)}")
            return False

    def initialize_driver(self):
        """Initialize Chrome driver with optimized settings"""
        with self.driver_lock:  # Ensure thread-safe driver initialization
            try:
                # If driver exists and is responsive, reuse it
                if self.driver:
                    try:
                        self.driver.current_url
                        return True
                    except WebDriverException:
                        # Only quit if driver is not responsive
                        try:
                            self.driver.quit()
                        except:
                            pass
                        self.driver = None

                chrome_options = webdriver.ChromeOptions()
                chrome_options.add_argument('--start-maximized')
                chrome_options.add_argument('--disable-gpu')
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                chrome_options.add_argument('--force-device-scale-factor=1')
                
                # Set basic printing preferences without specific output directory
                chrome_options.add_experimental_option('prefs', {
                    'printing.print_preview_sticky_settings.appState': json.dumps({
                        'recentDestinations': [{
                            'id': 'Save as PDF',
                            'origin': 'local',
                            'account': '',
                        }],
                        'selectedDestinationId': 'Save as PDF',
                        'version': 2
                    })
                })
                
                self.driver = webdriver.Chrome(options=chrome_options)
                
                # Enable necessary CDP domains
                self.driver.execute_cdp_cmd('Page.enable', {})
                self.driver.execute_cdp_cmd('Network.enable', {})
                
                # Only show configuration message if this is the first initialization
                if not hasattr(self, 'initial_config_done'):
                    self.status_var.set("Chrome opened for manual configuration. Configure as needed and click OK when ready.")
                    self.root.update()
                    messagebox.showinfo("Manual Configuration", 
                        "Please configure Chrome as needed:\n\n" +
                        "- Login to required websites\n" +
                        "- Set any necessary preferences\n" +
                        "- Configure any required extensions\n\n" +
                        "Click OK when you're ready to begin processing URLs.")
                    self.initial_config_done = True
                
                return True
                
            except Exception as e:
                self.status_var.set(f"Error initializing Chrome: {str(e)}")
                messagebox.showerror("Error", f"Failed to initialize Chrome:\n{str(e)}")
                return False

    def process_urls(self):
        """Process URLs from multiple files with improved error handling and recovery"""
        try:
            if not self.initialize_driver():
                return

            total_urls_all_files = 0
            # First count total URLs across all files
            for url_file, _ in self.url_files_and_dirs:
                with open(url_file, 'r') as f:
                    total_urls_all_files += sum(1 for line in f if line.strip())
            
            self.total_urls = total_urls_all_files
            self.processed_count = 0
            self.stop_requested = False
            
            self.status_var.set(f"Starting conversion of {self.total_urls} URLs across {len(self.url_files_and_dirs)} files...")
            
            # Process each file
            for url_file, output_dir in self.url_files_and_dirs:
                if self.stop_requested:
                    break
                
                self.status_var.set(f"Processing file: {os.path.basename(url_file)}")
                
                with open(url_file, 'r') as f:
                    urls = [line.strip() for line in f if line.strip()]
                
                for url in urls:
                    if self.stop_requested:
                        break
                        
                    while self.paused and not self.stop_requested:
                        time.sleep(0.5)
                        continue
                    
                    if not self.processing:
                        break
                    
                    try:
                        with self.driver_lock:
                            # Update the output directory for the current file
                            self.output_dir = output_dir
                            if self.save_as_pdf(url):
                                self.processed_count += 1
                                self.progress_var.set((self.processed_count / self.total_urls) * 100)
                            
                    except WebDriverException as e:
                        if "invalid session id" in str(e).lower() or "no such session" in str(e).lower():
                            self.status_var.set("Attempting to recover browser session...")
                            if not self.initialize_driver():
                                break
                        else:
                            self.status_var.set(f"Error processing {url}: {str(e)}")
                            time.sleep(2)
                    except Exception as e:
                        self.status_var.set(f"Error processing {url}: {str(e)}")
                        time.sleep(2)
                        continue
                    
                    time.sleep(1)
            
            final_status = f"Conversion completed. {self.processed_count} of {self.total_urls} URLs processed."
            self.status_var.set(final_status)
            messagebox.showinfo("Complete", final_status)
            
        except Exception as e:
            self.status_var.set(f"Error in processing: {str(e)}")
            messagebox.showerror("Error", f"An error occurred:\n{str(e)}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources"""
        with self.driver_lock:
            try:
                if self.driver and not self.paused:  # Don't quit if paused
                    self.driver.quit()
                    self.driver = None
            except Exception:
                pass
            
        self.processing = False
        self.start_button.config(state=tk.NORMAL)
        self.pause_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.DISABLED)

    def start_conversion(self):
        """Start the conversion process with validation"""
        if not self.url_files_and_dirs:
            messagebox.showerror("Error", "Please add at least one URL file and output folder pair.")
            return
            
        self.processing = True
        self.paused = False
        self.progress_var.set(0)
        
        self.start_button.config(state=tk.DISABLED)
        self.pause_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.NORMAL)
        
        threading.Thread(target=self.process_urls, daemon=True).start()

    def toggle_pause(self):
        """Toggle pause/resume state"""
        self.paused = not self.paused
        self.pause_button.config(text="Resume" if self.paused else "Pause")
        self.status_var.set("Paused" if self.paused else "Resuming...")
        
        if not self.paused:  # If resuming
            # Check if driver is still alive before resuming
            try:
                with self.driver_lock:
                    if self.driver:
                        self.driver.current_url  # Test if session is alive
            except WebDriverException:
                # Don't initialize here - let process_urls handle it
                pass

    def stop_conversion(self):
        """Stop the conversion process gracefully"""
        if messagebox.askyesno("Confirm Stop", "Are you sure you want to stop the conversion?"):
            self.stop_requested = True
            self.processing = False
            self.status_var.set("Stopping conversion...")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = WebPageToPDFConverter()
    app.run()
