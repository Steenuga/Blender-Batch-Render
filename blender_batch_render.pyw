import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import re
import threading
from datetime import datetime, timedelta

# Приховування консолі для Windows
if sys.platform.startswith('win'):
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class BlenderBatchRenderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Blender Batch Render")
        self.root.geometry("900x700")
        self.root.configure(padx=15, pady=15)
        
        self.blender_path = r"C:\Program Files (x86)\Steam\steamapps\common\Blender\blender.exe"
        self.files_to_render = []
        self.current_file_index = -1
        self.process = None
        self.rendering = False
        self.start_time = None
        self.timer_id = None
        
        # Інформація про поточний рендер
        self.total_frames = 0
        self.current_frame = 0
        
        # Головний фрейм
        main_frame = ttk.Frame(root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Фрейм верхніх кнопок
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопки
        ttk.Button(button_frame, text="Додати файли", command=self.add_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистити список", command=self.clear_files).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Видалити вибраний", command=self.remove_selected_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Встановити шлях до Blender", command=self.set_blender_path).pack(side=tk.LEFT, padx=5)
        
        self.render_button = ttk.Button(button_frame, text="Почати рендер", command=self.start_rendering)
        self.render_button.pack(side=tk.LEFT, padx=5)
        
        self.stop_button = ttk.Button(button_frame, text="Зупинити", command=self.stop_rendering, state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5)
        
        # Два панельних фрейми: файли та консоль
        panel_frame = ttk.PanedWindow(main_frame, orient=tk.VERTICAL)
        panel_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Список файлів
        files_frame = ttk.LabelFrame(panel_frame, text="Файли для рендеру")
        
        columns = ('status', 'file', 'frames', 'progress', 'time')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings')
        
        # Заголовки
        self.files_tree.heading('status', text='Статус')
        self.files_tree.heading('file', text='Файл')
        self.files_tree.heading('frames', text='Кадри')
        self.files_tree.heading('progress', text='Прогрес')
        self.files_tree.heading('time', text='Витрачений час')
        
        # Ширина колонок
        self.files_tree.column('status', width=100)
        self.files_tree.column('file', width=350)
        self.files_tree.column('frames', width=100)
        self.files_tree.column('progress', width=100)
        self.files_tree.column('time', width=150)
        
        # Скроллбар
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        self.files_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.files_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Додаємо фрейм в панель
        panel_frame.add(files_frame, weight=1)
        
        # Консольний вивід
        console_frame = ttk.LabelFrame(panel_frame, text="Консоль")
        
        self.console = tk.Text(console_frame, wrap=tk.WORD, bg='black', fg='light green')
        self.console.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Скроллбар для консолі
        console_scrollbar = ttk.Scrollbar(self.console, orient=tk.VERTICAL, command=self.console.yview)
        self.console.configure(yscroll=console_scrollbar.set)
        console_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Додаємо фрейм в панель
        panel_frame.add(console_frame, weight=1)
        
        # Прогрес бар для поточного рендеру
        progress_frame = ttk.LabelFrame(main_frame, text="Поточний рендер")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.current_file_var = tk.StringVar(value="Немає активних рендерів")
        ttk.Label(progress_frame, textvariable=self.current_file_var).pack(anchor=tk.W, padx=5, pady=5)
        
        frame_info_frame = ttk.Frame(progress_frame)
        frame_info_frame.pack(fill=tk.X, padx=5)
        
        self.frame_var = tk.StringVar(value="Кадр: 0 / 0")
        ttk.Label(frame_info_frame, textvariable=self.frame_var).pack(side=tk.LEFT, padx=(0, 15))
        
        self.time_var = tk.StringVar(value="Час: 00:00:00")
        ttk.Label(frame_info_frame, textvariable=self.time_var).pack(side=tk.LEFT)
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)
        
        # Підпис автора
        author_label = ttk.Label(root, text="Created by L. A. Steenuga", foreground="gray")
        author_label.pack(side=tk.BOTTOM, anchor=tk.E, padx=10, pady=5)
        
        # Автоматичне оновлення GUI
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def add_files(self):
        files = filedialog.askopenfilenames(
            title="Виберіть Blender файли",
            filetypes=(("Blender files", "*.blend"), ("All files", "*.*"))
        )
        
        for file in files:
            if file not in [f[0] for f in self.files_to_render]:
                # [шлях, статус, кількість кадрів, поточний кадр, відсоток, час]
                self.files_to_render.append([file, "В черзі", 0, 0, 0, "00:00:00"])
                self.files_tree.insert('', 'end', values=("В черзі", os.path.basename(file), "?", "0%", "00:00:00"))
        
    def clear_files(self):
        if not self.rendering:
            self.files_to_render = []
            for item in self.files_tree.get_children():
                self.files_tree.delete(item)
        else:
            self.log("Неможливо очистити список під час рендерингу")
    
    def remove_selected_file(self):
        if not self.rendering:
            selected = self.files_tree.selection()
            if not selected:
                messagebox.showinfo("Інформація", "Виберіть файл для видалення")
                return
                
            for item in selected:
                values = self.files_tree.item(item, 'values')
                file_name = values[1]
                
                # Видалення з списка файлів
                for i, file_data in enumerate(self.files_to_render):
                    if os.path.basename(file_data[0]) == file_name:
                        self.files_to_render.pop(i)
                        break
                        
                # Видалення з дерева
                self.files_tree.delete(item)
        else:
            self.log("Неможливо видалити файл під час рендерингу")
            
    def set_blender_path(self):
        path = filedialog.askopenfilename(
            title="Виберіть виконуваний файл Blender",
            filetypes=(("Executable files", "*.exe"), ("All files", "*.*"))
        )
        if path:
            self.blender_path = path
            self.log(f"Встановлено новий шлях до Blender: {path}")
    
    def update_timer(self):
        if self.rendering and self.start_time:
            # Оновлюємо час для поточного рендеру
            elapsed_time = time.time() - self.start_time
            time_str = str(timedelta(seconds=int(elapsed_time)))
            self.time_var.set(f"Час: {time_str}")
            
            # Оновлюємо час у дереві
            if 0 <= self.current_file_index < len(self.files_to_render):
                current_file = self.files_to_render[self.current_file_index]
                current_file[5] = time_str
                
                for item in self.files_tree.get_children():
                    if self.files_tree.item(item)['values'][1] == os.path.basename(current_file[0]):
                        values = list(self.files_tree.item(item)['values'])
                        values[4] = time_str
                        self.files_tree.item(item, values=tuple(values))
                        break
            
            # Запускаємо наступне оновлення через 1 секунду
            self.timer_id = self.root.after(1000, self.update_timer)
            
    def start_rendering(self):
        if not self.files_to_render:
            self.log("Додайте файли для рендерингу")
            return
            
        if not os.path.exists(self.blender_path):
            self.log(f"Файл Blender не знайдено: {self.blender_path}")
            return
            
        if not self.rendering:
            self.rendering = True
            self.render_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            
            # Запуск в окремому потоці
            threading.Thread(target=self.render_next_file, daemon=True).start()
    
    def stop_rendering(self):
        if self.rendering and self.process:
            self.rendering = False
            try:
                self.process.terminate()
                self.log("Рендер зупинено користувачем")
            except:
                self.log("Не вдалося зупинити процес")
                
            self.render_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            
            # Зупиняємо таймер
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
            
            # Оновлення статусу файлу
            if 0 <= self.current_file_index < len(self.files_to_render):
                current_file = self.files_to_render[self.current_file_index]
                current_file[1] = "Скасовано"
                
                # Оновлення у дереві
                for item in self.files_tree.get_children():
                    if self.files_tree.item(item)['values'][1] == os.path.basename(current_file[0]):
                        self.files_tree.item(item, values=(
                            "Скасовано",
                            os.path.basename(current_file[0]),
                            f"{current_file[2]}",
                            f"{current_file[4]}%",
                            current_file[5]
                        ))
                        break
    
    def analyze_blend_info(self, filepath):
        """Отримуємо інформацію про кількість кадрів у .blend файлі"""
        cmd = [self.blender_path, "-b", filepath, "--python-expr", "import bpy; print('FRAME_START:', bpy.context.scene.frame_start); print('FRAME_END:', bpy.context.scene.frame_end)"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            output = result.stdout
            
            # Знаходимо початковий і кінцевий кадри
            frame_start = 1
            frame_end = 1
            
            start_match = re.search(r'FRAME_START:\s*(\d+)', output)
            end_match = re.search(r'FRAME_END:\s*(\d+)', output)
            
            if start_match:
                frame_start = int(start_match.group(1))
            if end_match:
                frame_end = int(end_match.group(1))
                
            total_frames = frame_end - frame_start + 1
            return total_frames
        except Exception as e:
            self.log(f"Помилка при аналізі файлу: {e}")
            return 1  # За замовчуванням повертаємо 1 кадр
    
    def render_next_file(self):
        self.current_file_index += 1
        
        if self.current_file_index >= len(self.files_to_render):
            self.log("Всі файли оброблено")
            self.rendering = False
            self.render_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.current_file_var.set("Немає активних рендерів")
            self.progress_var.set(0)
            self.time_var.set("Час: 00:00:00")
            self.frame_var.set("Кадр: 0 / 0")
            
            # Зупиняємо таймер
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                self.timer_id = None
                
            return
            
        current_file = self.files_to_render[self.current_file_index]
        file_path = current_file[0]
        
        # Аналізуємо файл для визначення кількості кадрів
        self.log(f"Аналіз кількості кадрів для файлу {os.path.basename(file_path)}...")
        frames_count = self.analyze_blend_info(file_path)
        self.total_frames = frames_count
        self.current_frame = 0
        
        # Оновлюємо інформацію про кадри
        current_file[2] = frames_count
        
        # Оновлення статусу файлу
        current_file[1] = "Рендериться"
        
        # Оновлення у дереві
        for item in self.files_tree.get_children():
            if self.files_tree.item(item)['values'][1] == os.path.basename(file_path):
                self.files_tree.item(item, values=(
                    "Рендериться",
                    os.path.basename(file_path),
                    str(frames_count),
                    "0%",
                    "00:00:00"
                ))
                break
        
        # Оновлення відображення
        self.current_file_var.set(f"Рендеринг: {os.path.basename(file_path)}")
        self.progress_var.set(0)
        self.frame_var.set(f"Кадр: 0 / {frames_count}")
        
        # Запуск Blender
        cmd = [self.blender_path, "-b", file_path, "-a"]
        self.log(f"Запуск: {' '.join(cmd)}")
        
        # Запуск таймера та запис часу початку
        self.start_time = time.time()
        if self.timer_id:
            self.root.after_cancel(self.timer_id)
        self.timer_id = self.root.after(1000, self.update_timer)
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            creationflags=subprocess.CREATE_NO_WINDOW
        )
        
        # Обробка виводу Blender
        for line in iter(self.process.stdout.readline, ''):
            if not self.rendering:
                break
                
            self.log(line.strip())
            
            # Оновлення прогресу на основі номера кадру
            frame_match = re.search(r'Fra:(\d+)', line)
            if frame_match:
                try:
                    frame_num = int(frame_match.group(1))
                    self.current_frame = frame_num
                    
                    # Розрахунок прогресу
                    if self.total_frames > 0:
                        progress = min(100, (frame_num / self.total_frames) * 100)
                        
                        # Оновлення інтерфейсу через основний потік GUI
                        def update_ui():
                            self.progress_var.set(progress)
                            self.frame_var.set(f"Кадр: {frame_num} / {self.total_frames}")
                            
                            # Оновлення даних файлу
                            current_file[3] = frame_num
                            current_file[4] = progress
                            
                            # Оновлення у дереві
                            for item in self.files_tree.get_children():
                                if self.files_tree.item(item)['values'][1] == os.path.basename(file_path):
                                    values = list(self.files_tree.item(item)['values'])
                                    values[3] = f"{int(progress)}%"
                                    self.files_tree.item(item, values=tuple(values))
                                    break
                        
                        self.root.after(0, update_ui)
                except Exception as e:
                    self.log(f"Помилка при аналізі номера кадру: {e}")
        
        # Завершення рендерингу файлу
        if self.rendering:
            exit_code = self.process.wait()
            elapsed_time = time.time() - self.start_time
            time_str = str(timedelta(seconds=int(elapsed_time)))
            
            status = "Завершено" if exit_code == 0 else "Помилка"
            self.log(f"Файл {os.path.basename(file_path)} {status.lower()}, код: {exit_code}")
            
            # Оновлення даних файлу
            current_file[1] = status
            current_file[4] = 100 if status == "Завершено" else current_file[4]
            current_file[5] = time_str
            
            # Оновлення у дереві
            for item in self.files_tree.get_children():
                if self.files_tree.item(item)['values'][1] == os.path.basename(file_path):
                    self.files_tree.item(item, values=(
                        status,
                        os.path.basename(file_path),
                        str(current_file[2]),
                        "100%" if status == "Завершено" else f"{int(current_file[4])}%",
                        time_str
                    ))
                    break
            
            # Перехід до наступного файлу
            if self.rendering:
                self.render_next_file()
    
    def log(self, message):
        def _log():
            self.console.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
            self.console.see(tk.END)
        
        self.root.after(0, _log)
    
    def on_closing(self):
        if self.rendering:
            if self.process:
                try:
                    self.process.terminate()
                except:
                    pass
                    
            # Зупиняємо таймер
            if self.timer_id:
                self.root.after_cancel(self.timer_id)
                
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = BlenderBatchRenderApp(root)
    root.mainloop()