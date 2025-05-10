import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import time
import subprocess
import requests
import json
import re
import os
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import locale
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Türkçe karakter desteği için font kaydı
try:
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
except:
    pass  # Font bulunamazsa varsayılan fontları kullanacak

class HackerStyle:
    """Hacker tarzı uygulaması için tema renkleri ve stilleri"""
    BG_COLOR = "#000000"  # Siyah arkaplan
    FG_COLOR = "#00FF00"  # Matrix yeşili
    ALT_COLOR = "#003300"  # Koyu yeşil
    HIGHLIGHT = "#00AA00"  # Vurgu yeşili
    FONT = ("Courier", 10, "bold")  # Hacker tarzı font
    TITLE_FONT = ("Courier", 16, "bold")
    
    @staticmethod
    def apply_style(widget):
        """Widget'a hacker stilini uygula"""
        widget.config(bg=HackerStyle.BG_COLOR, fg=HackerStyle.FG_COLOR, font=HackerStyle.FONT)
        
    @staticmethod
    def configure_ttk_style():
        """TTK widgetları için stil ayarları"""
        style = ttk.Style()
        
        # Ana stil ayarları
        style.configure(".", 
                      background=HackerStyle.BG_COLOR, 
                      foreground=HackerStyle.FG_COLOR, 
                      font=HackerStyle.FONT)
        
        # Buton stili
        style.configure("TButton", 
                      background=HackerStyle.ALT_COLOR, 
                      foreground=HackerStyle.FG_COLOR)
        style.map("TButton", 
                background=[('active', HackerStyle.HIGHLIGHT)],
                foreground=[('active', HackerStyle.BG_COLOR)])
        
        # Frame stili
        style.configure("TFrame", background=HackerStyle.BG_COLOR)
        
        # LabelFrame stili
        style.configure("TLabelframe", background=HackerStyle.BG_COLOR, foreground=HackerStyle.FG_COLOR)
        style.configure("TLabelframe.Label", background=HackerStyle.BG_COLOR, foreground=HackerStyle.FG_COLOR)
        
        # PanedWindow stili
        style.configure("TPanedwindow", background=HackerStyle.BG_COLOR)
        
        # Progressbar stili
        style.configure("TProgressbar", 
                      background=HackerStyle.FG_COLOR,
                      troughcolor=HackerStyle.ALT_COLOR)
        
        # Label stili
        style.configure("TLabel", background=HackerStyle.BG_COLOR, foreground=HackerStyle.FG_COLOR)
        
        # Combobox stili
        style.configure("TCombobox", 
                      fieldbackground=HackerStyle.ALT_COLOR, 
                      background=HackerStyle.BG_COLOR,
                      foreground=HackerStyle.FG_COLOR,
                      selectbackground=HackerStyle.HIGHLIGHT,
                      selectforeground=HackerStyle.BG_COLOR)
        
        return style

class ChatApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Asistan - Hacker Modu")
        self.root.geometry("900x750")
        self.root.configure(bg=HackerStyle.BG_COLOR)
        
        # Tema stilini ayarla
        self.style = HackerStyle.configure_ttk_style()
        
        # Ana çerçeveyi oluştur
        self.main_frame = ttk.PanedWindow(root, orient=tk.HORIZONTAL)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Sol Panel (Geçmiş ve Modeller)
        self.left_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.left_frame, weight=1)
        
        # Sağ Panel (Chat alanı)
        self.right_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.right_frame, weight=3)
        
        # ASCII Art başlık
        ascii_art = """
  _    _            _              _____  _____ _____ 
 | |  | |          | |            / ____|/ ____|_   _|
 | |__| | __ _  ___| | _____ _ __| |  __| (___   | |  
 |  __  |/ _` |/ __| |/ / _ \ '__| | |_ |\___ \  | |  
 | |  | | (_| | (__|   <  __/ |  | |__| |____) |_| |_ 
 |_|  |_|\__,_|\___|_|\_\___|_|   \_____|_____/|_____|
        """
        
        ascii_label = tk.Label(self.left_frame, text=ascii_art, font=("Courier", 8), justify=tk.LEFT)
        HackerStyle.apply_style(ascii_label)
        ascii_label.pack(pady=(0, 10))
        
        # Geçmiş sorgular bölümü
        history_frame = ttk.LabelFrame(self.left_frame, text=" KAYITLI KONUŞMALAR ")
        history_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.history_listbox = tk.Listbox(history_frame, width=30, height=15, selectmode=tk.SINGLE)
        self.history_listbox.pack(fill="both", expand=True, padx=5, pady=5)
        self.history_listbox.bind('<<ListboxSelect>>', self.on_history_select)
        HackerStyle.apply_style(self.history_listbox)
        
        # Geçmiş için scrollbar
        history_scrollbar = ttk.Scrollbar(self.history_listbox, orient="vertical")
        self.history_listbox.config(yscrollcommand=history_scrollbar.set)
        history_scrollbar.config(command=self.history_listbox.yview)
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Geçmiş yönetimi butonları
        history_button_frame = ttk.Frame(self.left_frame)
        history_button_frame.pack(fill="x", padx=5, pady=5)
        
        self.delete_history_button = ttk.Button(history_button_frame, text="SİL", command=self.delete_selected_history)
        self.delete_history_button.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        
        self.delete_all_history_button = ttk.Button(history_button_frame, text="TÜMÜNÜ SİL", command=self.delete_all_history)
        self.delete_all_history_button.pack(side=tk.LEFT, padx=5, fill="x", expand=True)
        
        # Model Seçimi
        model_frame = ttk.LabelFrame(self.left_frame, text=" MODEL SEÇİMİ ")
        model_frame.pack(fill="x", padx=5, pady=5)

        self.models = self.get_models()
        self.selected_model = tk.StringVar()
        if self.models:
            self.selected_model.set(self.models[0])
        else:
            self.selected_model.set("Model bulunamadı")

        self.model_dropdown = ttk.OptionMenu(model_frame, self.selected_model, *self.models)
        self.model_dropdown.pack(padx=5, pady=5, fill="x")
        
        # Saat ve tarih göstergesi
        time_frame = ttk.Frame(self.left_frame)
        time_frame.pack(fill="x", padx=5, pady=5)
        
        self.time_label = ttk.Label(time_frame, text="00:00:00")
        self.time_label.pack(side=tk.LEFT, padx=5)
        
        self.date_label = ttk.Label(time_frame, text="01 Jan 2025")
        self.date_label.pack(side=tk.RIGHT, padx=5)
        
        self.update_clock()
        
        # Sağ Panel İçeriği - Chat Alanı
        
        # Sohbet Geçmişi
        chat_frame = ttk.LabelFrame(self.right_frame, text=" TERMİNAL ")
        chat_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.chat_text = scrolledtext.ScrolledText(chat_frame, wrap="word", height=20)
        self.chat_text.pack(fill="both", expand=True, padx=5, pady=5)
        self.chat_text.config(state=tk.DISABLED)
        HackerStyle.apply_style(self.chat_text)
        
        # Prompt Giriş Alanı
        input_frame = ttk.Frame(self.right_frame)
        input_frame.pack(fill="x", padx=5, pady=5)
        
        self.prompt_entry = tk.Entry(
            input_frame,
            font=HackerStyle.FONT,
            width=50,
            bd=2,
            relief=tk.GROOVE
        )
        self.prompt_entry.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 5))
        self.prompt_entry.insert(0, "Buraya sorunuzu yazın...")
        self.prompt_entry.bind("<FocusIn>", self.clear_placeholder)
        self.prompt_entry.bind("<FocusOut>", self.restore_placeholder)
        self.prompt_entry.bind("<Return>", lambda event: self.start_generation())
        HackerStyle.apply_style(self.prompt_entry)

        # Buton çerçevesi
        button_frame = ttk.Frame(self.right_frame)
        button_frame.pack(fill="x", pady=5)

        # İlk buton satırı
        button_row1 = ttk.Frame(button_frame)
        button_row1.pack(fill="x", pady=2)
        
        self.ask_button = ttk.Button(button_row1, text="SOR", command=self.start_generation)
        self.ask_button.pack(side=tk.LEFT, padx=5)

        self.stop_button = ttk.Button(button_row1, text="DURDUR", command=self.stop_generation, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        self.clear_button = ttk.Button(button_row1, text="TEMİZLE", command=self.clear_chat)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        # İkinci buton satırı
        button_row2 = ttk.Frame(button_frame)
        button_row2.pack(fill="x", pady=2)
        
        self.save_txt_button = ttk.Button(button_row2, text="TXT KAYDET", command=lambda: self.save_conversation("txt"))
        self.save_txt_button.pack(side=tk.LEFT, padx=5)
        
        self.save_pdf_button = ttk.Button(button_row2, text="PDF KAYDET", command=lambda: self.save_conversation("pdf"))
        self.save_pdf_button.pack(side=tk.LEFT, padx=5)

        # Progress Bar
        self.progress = ttk.Progressbar(self.right_frame, orient='horizontal', mode='indeterminate')
        self.progress.pack(fill="x", padx=5, pady=5)

        # Durum çubuğu
        self.status_var = tk.StringVar()
        self.status_var.set("SİSTEM HAZIR")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Hafıza yapıları
        self.conversation_history = []  # [(prompt, response), (prompt, response), ...]
        self.current_response = ""
        
        # Diğer Ayarlar
        self.is_generating = False
        self.generation_thread = None
        
        # Dosya işlemleri için dizin kontrolü
        self.ensure_history_dir()
        
        # Hoş geldin mesajı
        self.update_welcome_message()

    def update_welcome_message(self):
        """Hoş geldin mesajını göster"""
        welcome_msg = f"""
        [SİSTEM] {datetime.datetime.now().strftime('%d.%m.%Y %H:%M:%S')}
        
        > AI ASİSTAN TERMİNALİ BAŞLATILDI
        > MODEL: {self.selected_model.get()}
        > DURUM: BAĞLANTI KURULDU
        
        > YARDIM İÇİN "help" YAZIN
        > BAŞLAMAK İÇİN MESAJINIZI GİRİN VE "SOR" BUTONUNA BASIN
        
        """
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.insert(tk.END, welcome_msg)
        self.chat_text.config(state=tk.DISABLED)
    
    def update_clock(self):
        """Saat ve tarih bilgisini güncelle"""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        date_str = now.strftime("%d %b %Y")
        
        self.time_label.config(text=time_str)
        self.date_label.config(text=date_str)
        
        # Her saniye güncelle
        self.root.after(1000, self.update_clock)

    def ensure_history_dir(self):
        """Geçmiş dosyalarını saklamak için klasör oluştur"""
        os.makedirs("conversation_history", exist_ok=True)
    
    def clear_placeholder(self, event):
        if self.prompt_entry.get() == "Buraya sorunuzu yazın...":
            self.prompt_entry.delete(0, "end")

    def restore_placeholder(self, event):
        if not self.prompt_entry.get():
            self.prompt_entry.insert(0, "Buraya sorunuzu yazın...")

    def clear_chat(self):
        """Sohbet alanını temizle"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.delete(1.0, tk.END)
        self.chat_text.config(state=tk.DISABLED)
        self.conversation_history = []
        self.status_var.set("SOHBET TEMİZLENDİ")
        self.update_welcome_message()

    def delete_selected_history(self):
        """Seçili geçmiş sohbeti sil"""
        if not self.history_listbox.curselection():
            messagebox.showwarning("Uyarı", "Silinecek bir sohbet seçin!")
            return
            
        selected_idx = self.history_listbox.curselection()[0]
        selected_item = self.history_listbox.get(selected_idx)
        
        filename = f"conversation_history/{selected_item}.json"
        
        try:
            os.remove(filename)
            self.update_history_list()
            self.status_var.set(f"'{selected_item}' SİLİNDİ")
        except Exception as e:
            messagebox.showerror("Hata", f"Sohbet silinirken hata oluştu: {str(e)}")
    
    def delete_all_history(self):
        """Tüm geçmiş sohbetleri sil"""
        confirmation = messagebox.askyesno("Onay", "Tüm geçmiş sohbetleri silmek istediğinize emin misiniz?")
        if not confirmation:
            return
            
        try:
            files = [f for f in os.listdir("conversation_history") if f.endswith('.json')]
            for file in files:
                os.remove(f"conversation_history/{file}")
            
            self.update_history_list()
            self.status_var.set("TÜM GEÇMİŞ SİLİNDİ")
        except Exception as e:
            messagebox.showerror("Hata", f"Geçmiş silinirken hata oluştu: {str(e)}")

    def on_history_select(self, event):
        """Geçmiş sohbetten bir öğe seçildiğinde tetiklenir"""
        if not self.history_listbox.curselection():
            return
            
        selected_idx = self.history_listbox.curselection()[0]
        selected_item = self.history_listbox.get(selected_idx)
        
        # Dosyadan sohbeti yükle
        filename = f"conversation_history/{selected_item}.json"
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    self.conversation_history = json.load(f)
                    
                # Sohbeti görüntüle
                self.chat_text.config(state=tk.NORMAL)
                self.chat_text.delete(1.0, tk.END)
                
                for prompt, response in self.conversation_history:
                    self.chat_text.insert(tk.END, f"> KULLANICI: {prompt}\n\n", "user")
                    self.chat_text.insert(tk.END, f"> AI: {response}\n\n", "ai")
                    
                self.chat_text.config(state=tk.DISABLED)
                self.status_var.set(f"'{selected_item}' YÜKLENDİ")
            except Exception as e:
                messagebox.showerror("Hata", f"Sohbet yüklenirken hata oluştu: {str(e)}")
        else:
            messagebox.showwarning("Uyarı", f"'{selected_item}' BULUNAMADI")
    
    def update_history_list(self):
        """Geçmiş sohbet listesini güncelle"""
        self.history_listbox.delete(0, tk.END)
        try:
            files = [f.replace('.json', '') for f in os.listdir("conversation_history") if f.endswith('.json')]
            for file in sorted(files, reverse=True):
                self.history_listbox.insert(tk.END, file)
        except Exception as e:
            messagebox.showerror("Hata", f"Geçmiş listesi güncellenirken hata oluştu: {str(e)}")

    def start_generation(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt or prompt == "Buraya sorunuzu yazın...":
            messagebox.showwarning("Uyarı", "Geçerli bir soru girin!")
            return
            
        # Bazı özel komutlar için kontrol
        if prompt.lower() == "help":
            self.show_help()
            return
        elif prompt.lower() == "clear":
            self.clear_chat()
            return

        self.progress.start()
        self.is_generating = True
        self.ask_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.status_var.set("YANIT ÜRETİLİYOR...")
        
        # Kullanıcı sorusunu ekle
        self.chat_text.config(state=tk.NORMAL)
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.chat_text.insert(tk.END, f"[{timestamp}] > KULLANICI: {prompt}\n\n", "user")
        self.chat_text.insert(tk.END, f"[{timestamp}] > AI: ", "ai")
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        
        self.current_response = ""  # Yeni yanıt için temizle

        self.generation_thread = threading.Thread(
            target=self.generate_response,
            args=(self.selected_model.get(), prompt),
            daemon=True
        )
        self.generation_thread.start()
        
        # Giriş alanını temizle
        self.prompt_entry.delete(0, tk.END)
        self.prompt_entry.insert(0, "Buraya sorunuzu yazın...")

    def show_help(self):
        """Yardım mesajını göster"""
        help_text = """
        > KOMUT KILAVUZU:
        
        - SOR: Sorunuzu göndermek için butona tıklayın veya Enter tuşuna basın
        - DURDUR: AI'nın yanıt üretmesini durdurmak için kullanın
        - TEMİZLE: Mevcut sohbeti temizler
        - TXT KAYDET: Sohbeti metin dosyası olarak kaydeder
        - PDF KAYDET: Sohbeti PDF raporu olarak kaydeder
        - SİL: Seçili geçmiş sohbeti siler
        - TÜMÜNÜ SİL: Tüm geçmiş sohbetleri siler
        
        > ÖZEL KOMUTLAR:
        - "help": Bu yardım mesajını gösterir
        - "clear": Sohbeti temizler
        """
        
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, help_text)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)

    def stop_generation(self):
        self.is_generating = False
        self.progress.stop()
        self.ask_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("YANIT ÜRETİMİ DURDURULDU")
        
        # Yanıtı konuşma geçmişine ekle
        if self.conversation_history and isinstance(self.conversation_history[-1], list) and len(self.conversation_history[-1]) == 1:
            # Son kullanıcı sorusu var ama AI yanıtı yok
            self.conversation_history[-1].append(self.current_response + " [YARIDA KESİLDİ]")
        
        # Sohbet bittikten sonra otomatik kaydet
        self.auto_save_conversation()

    def generate_response(self, model, prompt):
        api_url = "http://localhost:11434/api/generate"
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": True
        }

        try:
            response = requests.post(api_url, json=payload, stream=True)
            
            # Konuşma geçmişine soruyu ekle
            self.conversation_history.append([prompt])
            
            for line in response.iter_lines():
                if not self.is_generating:
                    break

                if line:
                    try:
                        json_data = json.loads(line.decode('utf-8'))
                        chunk = json_data.get("response", "")
                        self.current_response += chunk

                        # GUI'yi gerçek zamanlı güncelle
                        self.root.after(0, self.update_output, chunk)

                    except json.JSONDecodeError:
                        continue

            # Yanıtı konuşma geçmişine ekle
            if len(self.conversation_history[-1]) == 1:
                self.conversation_history[-1].append(self.current_response)
                
            # Sohbet bittikten sonra otomatik kaydet
            self.auto_save_conversation()
                
            # Son halini güncelle
            self.root.after(0, self.finish_generation)

        except Exception as e:
            error_msg = f"API hatası: {str(e)}"
            self.root.after(0, messagebox.showerror, "Hata", error_msg)
            self.root.after(0, self.update_status, f"HATA: {str(e)}")
            
            # Hata durumunda UI'ı sıfırla
            self.root.after(0, self.reset_ui_after_error)
    
    def reset_ui_after_error(self):
        """Hata durumunda UI'ı sıfırla"""
        self.progress.stop()
        self.is_generating = False
        self.ask_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
    
    def update_status(self, message):
        """Durum çubuğunu güncelle"""
        self.status_var.set(message)

    def update_output(self, text):
        """Sohbet penceresine yanıtı ekle"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, text)
        self.chat_text.config(state=tk.DISABLED)
        self.chat_text.see(tk.END)
        self.root.update_idletasks()

    def finish_generation(self):
        """Üretim tamamlandıktan sonra UI'ı güncelle"""
        self.chat_text.config(state=tk.NORMAL)
        self.chat_text.insert(tk.END, "\n\n")  # Yanıttan sonra boşluk ekle
        self.chat_text.config(state=tk.DISABLED)
        
        self.progress.stop()
        self.is_generating = False
        self.ask_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.status_var.set("YANIT TAMAMLANDI")

    def auto_save_conversation(self):
        """Konuşmayı otomatik olarak kaydet"""
        if not self.conversation_history:
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"conversation_history/conversation_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.conversation_history, f, ensure_ascii=False, indent=2)
            
            # Geçmiş listesini güncelle
            self.update_history_list()
            
        except Exception as e:
            messagebox.showerror("Hata", f"Sohbet kaydedilirken hata oluştu: {str(e)}")

    def save_conversation(self, format_type):
        """Konuşmayı belirtilen formatta kaydet"""
        if not self.conversation_history:
            messagebox.showwarning("Uyarı", "Kaydedilecek sohbet bulunamadı!")
            return
            
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if format_type == "txt":
            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt")],
                initialfile=f"conversation_{timestamp}.txt"
            )
            
            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write("AI Asistan Konuşma Raporu\n")
                        f.write("=" * 50 + "\n")
                        f.write(f"Oluşturulma Tarihi: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
                        f.write(f"Kullanılan Model: {self.selected_model.get()}\n")
                        f.write("=" * 50 + "\n\n")
                        
                        for i, (prompt, response) in enumerate(self.conversation_history):
                            f.write(f"Soru {i+1}:\n{prompt}\n\n")
                            f.write(f"Yanıt {i+1}:\n{response}\n\n")
                            f.write("-" * 50 + "\n\n")
                    
                    self.status_var.set(f"SOHBET KAYDEDILDI: {file_path}")
                except Exception as e:
                    messagebox.showerror("Hata", f"Dosya kaydedilirken hata oluştu: {str(e)}")
      
        elif format_type == "pdf":
         file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf")],
            initialfile=f"conversation_{timestamp}.pdf"
        )
            
        if file_path:
            try:
                # PDF oluşturma
                doc = SimpleDocTemplate(file_path, pagesize=letter)
                styles = getSampleStyleSheet()
                
                # Türkçe karakter desteği için font ayarları
                # DejaVuSans yerine Helvetica-Bold gibi varsayılan fontlar kullanabilir
                try:
                    heading_style = styles["Heading1"].clone('Heading1')
                    heading_style.fontName = 'DejaVuSans'
                except:
                    heading_style = styles["Heading1"]
                
                try:
                    normal_style = styles["Normal"].clone('Normal')
                    normal_style.fontName = 'DejaVuSans'
                except:
                    normal_style = styles["Normal"]
                    
                # PDF içeriği
                content = []
                content.append(Paragraph("AI Asistan Konuşma Raporu", heading_style))
                content.append(Spacer(1, 12))
                
                content.append(Paragraph(f"Oluşturulma Tarihi: {datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", normal_style))
                content.append(Paragraph(f"Kullanılan Model: {self.selected_model.get()}", normal_style))
                content.append(Spacer(1, 12))
                
                for i, (prompt, response) in enumerate(self.conversation_history):
                    content.append(Paragraph(f"Soru {i+1}:", heading_style))
                    content.append(Paragraph(prompt, normal_style))
                    content.append(Spacer(1, 6))
                    
                    content.append(Paragraph(f"Yanıt {i+1}:", heading_style))
                    content.append(Paragraph(response, normal_style))
                    content.append(Spacer(1, 12))
                
                # PDF oluştur
                doc.build(content)
                
                self.status_var.set(f"PDF KAYDEDILDI: {file_path}")
            except Exception as e:
                messagebox.showerror("Hata", f"PDF oluşturulurken hata oluştu: {str(e)}")

    def get_models(self):
        """Mevcut Ollama modellerini getir"""
        api_url = "http://localhost:11434/api/tags"
        
        try:
            response = requests.get(api_url)
            if response.status_code == 200:
                models = [model["name"] for model in response.json()["models"]]
                return models if models else ["Model bulunamadı"]
            else:
                return ["API erişim hatası"]
        except Exception as e:
            print(f"Model listesi alınamadı: {str(e)}")
            return ["Bağlantı hatası"]

def main():
    """Ana uygulama başlatıcı"""
    # Yerel ayarları Türkçe'ye ayarla
    try:
        locale.setlocale(locale.LC_ALL, 'tr_TR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, 'Turkish_Turkey.1254')
        except:
            pass  # Locale ayarları olmadan devam et
    
    root = tk.Tk()
    app = ChatApp(root)
    
    # İlk çalıştırmada geçmiş konuşmaları yükle
    app.update_history_list()
    
    # Terminal başlangıç efekti
    def startup_effect():
        app.chat_text.config(state=tk.NORMAL)
        app.chat_text.insert(tk.END, "> Sistem başlatılıyor...\n")
        app.chat_text.config(state=tk.DISABLED)
        app.root.update_idletasks()
        time.sleep(0.5)
        
        app.chat_text.config(state=tk.NORMAL)
        app.chat_text.insert(tk.END, "> Modeller kontrol ediliyor...\n")
        app.chat_text.config(state=tk.DISABLED)
        app.root.update_idletasks()
        time.sleep(0.5)
        
        app.chat_text.config(state=tk.NORMAL)
        app.chat_text.insert(tk.END, "> AI Asistan hazır!\n\n")
        app.chat_text.config(state=tk.DISABLED)
        app.root.update_idletasks()
        
        # Hoş geldin mesajını göster
        app.update_welcome_message()
    
    # Başlangıç efekti için thread kullan
    threading.Thread(target=startup_effect, daemon=True).start()
    
    # Metin renklendirme etiketleri
    app.chat_text.tag_configure("user", foreground=HackerStyle.HIGHLIGHT)
    app.chat_text.tag_configure("ai", foreground=HackerStyle.FG_COLOR)
    
    # Ana döngüyü başlat
    root.mainloop()

if __name__ == "__main__":
    main()