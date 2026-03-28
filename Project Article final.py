import customtkinter as ctk
from tkinter import messagebox
import requests
from tkinter import filedialog
from bs4 import BeautifulSoup
import os
import threading
import urllib.parse

ctk.set_appearance_mode("dark")  # Modes: system (default), light, dark
ctk.set_default_color_theme("blue")  # Themes: blue (default), dark-blue, green

class Scihub_Downloader:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Project Article")
        self.root.geometry("424x460")

        self.create_widgets()

    def create_widgets(self):
        # Main frame
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(pady=20, padx=20, fill= "x", expand=True)

        #To set title and combox in line
        self.title_box = ctk.CTkFrame(main_frame,fg_color="transparent")
        self.title_box.pack(padx=30, pady=10,fill ="x",expand= True)

        # Title
        title = ctk.CTkLabel(self.title_box, text="Article Downloader", font=("Enhanced Dot Digital-7", 24))
        title.pack(side="left",padx=10,pady=10)

        self.choice_box = ctk.CTkComboBox(self.title_box,values=["sci-hub.se","sci-hub.ru","sci-hub.st"],width= 50)
        self.choice_box.pack(side="right",padx = 2 ,pady=10,fill="x",expand = True)

        self.title_url_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter Article Title")
        self.title_url_entry.pack(pady=10, padx=20, fill="x")

        self.webpage_url_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter DOI of Article")
        self.webpage_url_entry.pack(pady=10, padx=20, fill="x")


        self.filename_entry = ctk.CTkEntry(main_frame, placeholder_text="Enter File Name")
        self.filename_entry.pack(pady=10, padx=20, fill="x")

        #browser buttomn
        self.save_location_frame = ctk.CTkFrame(main_frame,fg_color="transparent")
        self.save_location_frame.pack(padx=20, pady=10,fill ="x",expand= True)
        # Save Location Entry
        self.save_location_entry = ctk.CTkEntry(self.save_location_frame,width= 220)
        self.save_location_entry.pack(side="left",fill="x",expand = True)

        # Browse Button
        self.browse_button = ctk.CTkButton(self.save_location_frame, command=self.browse_location, text="Browse")
        self.browse_button.pack(side="left",padx = 5, fill ="x",expand = True)

        # Default save location
        self.default_save_location = os.path.expanduser("~\Downloads")  # Default to user's home directory , you can cahnge this 
        self.save_location = self.default_save_location
        self.save_location_entry.insert(0, self.save_location) # enter the location into the entry at 0 th positon


        # Submit button
        self.submit_button = ctk.CTkButton(main_frame, text="Download", command=self.submit_data)
        self.submit_button.pack(pady=10, padx=20, fill="x")

        view_button = ctk.CTkButton(main_frame, text="View Pdf", command=self.view_pdf)
        view_button.pack(pady=10, padx=20, fill="x")

        clear_button = ctk.CTkButton(main_frame, text="Clear", command=self.Clear_data)
        clear_button.pack(pady=10, padx=20, fill="x")


    def browse_location(self):
        # Open a file dialog to choose the directory
        selected_folder = filedialog.askdirectory(initialdir=self.save_location, title="Select Save Location")
        if selected_folder:
            self.save_location = selected_folder
            self.save_location_entry.delete(0, ctk.END)  # Clear the previous value
            self.save_location_entry.insert(0, self.save_location)  # Insert the new folder path 

    def submit_data(self):     
        self.submit_button.configure(text="Wait...", state="disabled") 
        download_thread = threading.Thread(target= self.fetchandwrite)
        download_thread.start()

    def fetchandwrite(self):
        try :


            filename = self.filename_entry.get()
            domain = self.choice_box.get()

            title_url = self.title_url_entry.get()
            webpage_url = self.webpage_url_entry.get()

            if filename =="":
                 messagebox.showerror("Error", "Please Enter a valid Filename")
                 self.reset_button() 
                 return
            if  title_url =="" and webpage_url =="":
                messagebox.showerror("Error", "Please provide either a title or DOI.")
                self.reset_button() 
                return
            
            self.submit_button.configure(text="Fetching...", state="disabled")

            if title_url:
                title_url_parsed = urllib.parse.quote(title_url)
                res_1 = requests.get(f'https://api.crossref.org/works?query.title={title_url_parsed}&select=DOI')
                if res_1:
                    webpage_url = res_1.json()["message"]["items"][0]["DOI"]  
                    self.webpage_url_entry.delete(0, ctk.END) # to avoid overwrite error
                    self.webpage_url_entry.insert(0, webpage_url)
                elif res_1=="" or not res_1 :
                     messagebox.showerror("Error", "No DOI found for the provided title.")
                     self.reset_button() 
                     return
            elif webpage_url: 
                doi_url_parsed = urllib.parse.quote(webpage_url)
                res_2 = requests.get(f'https://api.crossref.org/works/{doi_url_parsed}')
                if res_2:
                    title_url = res_2.json()["message"]["title"][0]
                    self.title_url_entry.delete(0, ctk.END) # to avoid overwrite error
                    self.title_url_entry.insert(0, title_url)
                else:
                     messagebox.showerror("Error", "Invalid DOI.")
                     self.reset_button() 
                     return



            save_path = self.save_location_entry.get()
            if not save_path:
                messagebox.showerror("Error", "Please select a valid save location.")
                self.reset_button()  
                return
            
            self.submit_button.configure(text="downloading...", state="disabled") 

            full_url = f"https://{domain}/{webpage_url}"
            response = requests.get(full_url)
            response.raise_for_status()  # Check for HTTP request errors

            # Parse the webpage content
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find the <embed> tag with the PDF
            embed_tag = soup.find('embed', {'id': 'pdf'})
            if not embed_tag:
                messagebox.showerror("Error", "The file you requested is not available on Sci-Hub.")
                self.reset_button()
                return 


            # Extract the src attribute
            pdf_src = embed_tag['src']

            # Handle relative URLs
            pdf_url = requests.compat.urljoin(full_url, pdf_src)

            # Download the PDF
            pdf_response = requests.get(pdf_url)
            pdf_response.raise_for_status()  # this will throw 404 error if no file found in the sci-hub


            pdf_filename = f"{filename}.pdf"
            pdf_path = os.path.join(save_path, pdf_filename)
            with open(pdf_path,"xb") as pdf_file:
                pdf_file.write(pdf_response.content)
            messagebox.showinfo("Success", "Pdf downloaded successfully!")

        except requests.exceptions.RequestException :
            messagebox.showerror("Error", "The file you requested is not available on Sci-Hub.")
        except FileExistsError :
            messagebox.showerror("Error", f"File already exists at {pdf_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error occured {e}")
        

        self.submit_button.configure(text="Download", state="normal")  


    def reset_button(self):
        self.submit_button.configure(text="Download", state="normal")  


    def view_pdf(self):
        try:
            save_path = self.save_location_entry.get()
            filename = self.filename_entry.get()
            pdf_path = os.path.join(save_path,f"{filename}.pdf")
            os.startfile(pdf_path)
        except FileNotFoundError:
            messagebox.showerror("Error", "The specified PDF file was not found.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
    
    def Clear_data(self):
        # Clear the entries
        self.title_url_entry.delete(0,ctk.END)
        self.webpage_url_entry.delete(0, ctk.END)
        self.filename_entry.delete(0,ctk.END)


    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = Scihub_Downloader()
    app.run()