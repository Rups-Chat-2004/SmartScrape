import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import os
import time
import threading

MAX_PAGES = 7
scraped_data = []

# ========== DARK MODE STYLES ==========
def apply_dark_mode():
    root.configure(bg="#2b2b2b")
    style.theme_use("clam")
    style.configure(".", background="#2b2b2b", foreground="white", fieldbackground="#3c3f41", bordercolor="#555")
    style.configure("TButton", background="#3c3f41", foreground="white")
    style.configure("TLabel", background="#2b2b2b", foreground="white")
    style.configure("TEntry", fieldbackground="#3c3f41", foreground="white")
    style.configure("TOptionMenu", background="#3c3f41", foreground="white")

def apply_light_mode():
    root.configure(bg="#f8f9fa")
    style.theme_use("clam")
    style.configure(".", background="#f8f9fa", foreground="black", fieldbackground="white", bordercolor="#ccc")
    style.configure("TButton", background="white", foreground="black")
    style.configure("TLabel", background="#f8f9fa", foreground="black")
    style.configure("TEntry", fieldbackground="white", foreground="black")
    style.configure("TOptionMenu", background="white", foreground="black")

def toggle_theme():
    if dark_mode_var.get():
        apply_dark_mode()
    else:
        apply_light_mode()

# ========== SCRAPER LOGIC ==========
def detect_and_scrape():
    threading.Thread(target=scrape_thread).start()

def scrape_thread():
    base_url = entry_url.get().strip()
    tag = tag_var.get()

    if not base_url or not tag:
        messagebox.showerror("Error", "Please fill all fields correctly.")
        return

    progress_bar.start()
    scrape_btn.config(state=tk.DISABLED)
    text_box.delete('1.0', tk.END)

    global scraped_data
    scraped_data = []

    try:
        service = Service(os.path.join(os.getcwd(), "chromedriver.exe"))
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        driver = webdriver.Chrome(service=service, options=options)
        wait = WebDriverWait(driver, 10)
        actions = ActionChains(driver)

        driver.get(base_url)

        # Button-based pagination
        button_selectors = ["more", "next", "load", "show", "load-more"]
        found_button = None
        for selector in button_selectors:
            try:
                found_button = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, f"//*[contains(@id, '{selector}') or contains(@class, '{selector}') or contains(text(), '{selector.capitalize()}')]")
                ))
                break
            except:
                continue

        if found_button:
            for _ in range(MAX_PAGES):
                wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, tag)))
                elements = driver.find_elements(By.TAG_NAME, tag)
                scraped_data.extend([el.text.strip() for el in elements if el.text.strip()])
                try:
                    actions.move_to_element(found_button).click().perform()
                    time.sleep(2)
                except:
                    break
        else:
            for i in range(1, MAX_PAGES + 1):
                if "{page}" in base_url:
                    paged_url = base_url.replace("{page}", str(i))
                else:
                    paged_url = base_url.rstrip("/") + f"/page/{i}/"

                driver.get(paged_url)
                try:
                    wait.until(EC.presence_of_all_elements_located((By.TAG_NAME, tag)))
                    elements = driver.find_elements(By.TAG_NAME, tag)
                    new_results = [el.text.strip() for el in elements if el.text.strip()]
                    if not new_results:
                        break
                    scraped_data.extend(new_results)
                except:
                    break

        driver.quit()

        if scraped_data:
            for idx, val in enumerate(scraped_data, 1):
                text_box.insert(tk.END, f"{idx}. {val}\n")
            messagebox.showinfo("Success", f"{len(scraped_data)} items scraped.")
        else:
            messagebox.showwarning("No Data", "No relevant tags found on pages.")

    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        scrape_btn.config(state=tk.NORMAL)
        progress_bar.stop()

# ========== SAVE BUTTONS ==========
def save_csv():
    if not scraped_data:
        messagebox.showwarning("Empty", "Nothing to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")])
    if file_path:
        pd.DataFrame(scraped_data, columns=["Scraped Text"]).to_csv(file_path, index=False)
        messagebox.showinfo("Saved", f"Saved to {file_path}")

def save_excel():
    if not scraped_data:
        messagebox.showwarning("Empty", "Nothing to save.")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
    if file_path:
        pd.DataFrame(scraped_data, columns=["Scraped Text"]).to_excel(file_path, index=False)
        messagebox.showinfo("Saved", f"Saved to {file_path}")

# ========== GUI ==========
root = tk.Tk()
root.title("SmartScrape - Advanced Web Scraper")
root.geometry("700x650")
style = ttk.Style(root)

# Mode Toggle
dark_mode_var = tk.BooleanVar(value=False)

ttk.Label(root, text="SmartScrape", font=("Segoe UI", 16, "bold")).pack(pady=(15, 0))
ttk.Label(root, text="Smart GUI Scraper with Pagination, Themes & Export").pack(pady=(0, 10))

ttk.Checkbutton(root, text="Dark Mode", variable=dark_mode_var, command=toggle_theme).pack()

frame = ttk.LabelFrame(root, text="Scraper Settings", padding=10)
frame.pack(padx=20, pady=10, fill="x")

ttk.Label(frame, text="Enter URL (use {page} if dynamic):").grid(row=0, column=0, sticky="w")
entry_url = ttk.Entry(frame, width=80)
entry_url.grid(row=1, column=0, padx=5, pady=5)

ttk.Label(frame, text="Select HTML Tag:").grid(row=2, column=0, sticky="w")
tag_var = tk.StringVar()
tag_dropdown = ttk.OptionMenu(frame, tag_var, "h1", "h1", "h2", "h3", "p", "div", "span", "li", "a")
tag_dropdown.grid(row=3, column=0, padx=5, pady=5, sticky="w")

scrape_btn = ttk.Button(root, text="Start Scraping", command=detect_and_scrape)
scrape_btn.pack(pady=(10, 5))

progress_bar = ttk.Progressbar(root, mode='indeterminate', length=300)
progress_bar.pack(pady=(0, 10))

output_frame = ttk.LabelFrame(root, text="Scraped Output", padding=10)
output_frame.pack(padx=20, pady=10, fill="both", expand=True)

text_box = tk.Text(output_frame, wrap=tk.WORD, font=("Consolas", 10))
text_box.pack(fill="both", expand=True)

save_frame = ttk.Frame(root)
save_frame.pack(pady=10)
ttk.Button(save_frame, text="Save as CSV", command=save_csv).pack(side=tk.LEFT, padx=10)
ttk.Button(save_frame, text="Save as Excel", command=save_excel).pack(side=tk.LEFT, padx=10)

apply_light_mode()
root.mainloop()
