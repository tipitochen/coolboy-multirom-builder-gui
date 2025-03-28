import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import os
import subprocess
import shutil
import threading

# Ruta base: el directorio donde se encuentra este script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Rutas relativas al directorio base
GAMES_FOLDER = os.path.join(BASE_DIR, "games/")
GAMELIST_PATH = os.path.join(BASE_DIR, "configs/games.list")
BUILD_SCRIPT = os.path.join(BASE_DIR, "build.bat")
MENU_ASM_PATH = os.path.join(BASE_DIR, "menu.asm")
DEFAULT_OUTPUT_FOLDER = BASE_DIR  # Carpeta por defecto: donde está el programa
ROM_OUTPUT_NAME = "multirom.nes"  # Nombre de la ROM generada por build.bat

# Opciones iniciales para menu.asm
menu_options = {
    "ENABLE_SOUND": 0,
    "SHOW_FPS": 0,
    "DEBUG_MODE": 0,
    "MAX_PLAYERS": 2
}

def load_menu_options():
    """Carga las opciones desde menu.asm."""
    if os.path.exists(MENU_ASM_PATH):
        with open(MENU_ASM_PATH, "r") as f:
            for line in f:
                for key in menu_options.keys():
                    if line.startswith(f"{key} ="):
                        value = line.split("=")[1].strip()
                        menu_options[key] = int(value) if value.isdigit() else value

def save_menu_options():
    """Guarda las opciones en menu.asm."""
    if os.path.exists(MENU_ASM_PATH):
        with open(MENU_ASM_PATH, "w") as f:
            for key, value in menu_options.items():
                f.write(f"{key} = {value}\n")
        messagebox.showinfo("Éxito", "Opciones guardadas correctamente en menu.asm.")
    else:
        messagebox.showerror("Error", "No se encontró el archivo menu.asm.")

def update_enable_sound():
    """Actualiza la línea ENABLE_SOUND .equ en menu.asm dependiendo de la cantidad de juegos."""
    num_games = listbox_games.size()
    enable_sound_value = 1 if num_games > 1 else 0  # Habilitar sonido si hay más de 1 juego

    if os.path.exists(MENU_ASM_PATH):
        with open(MENU_ASM_PATH, "r") as f:
            lines = f.readlines()

        # Modificar la línea ENABLE_SOUND .equ
        with open(MENU_ASM_PATH, "w") as f:
            for line in lines:
                if line.strip().startswith("ENABLE_SOUND .equ"):
                    f.write(f"ENABLE_SOUND .equ {enable_sound_value}\n")
                else:
                    f.write(line)

def edit_menu_options():
    """Abre una ventana para editar las opciones de menu.asm."""
    def save_changes():
        """Guarda los cambios realizados en la ventana."""
        try:
            menu_options["ENABLE_SOUND"] = int(enable_sound_var.get())
            menu_options["SHOW_FPS"] = int(show_fps_var.get())
            menu_options["DEBUG_MODE"] = int(debug_mode_var.get())
            menu_options["MAX_PLAYERS"] = int(max_players_entry.get())
            save_menu_options()
            edit_window.destroy()
        except ValueError:
            messagebox.showerror("Error", "Por favor, ingresa valores válidos.")

    # Crear ventana de edición
    edit_window = tk.Toplevel(root)
    edit_window.title("Editar Opciones de menu.asm")
    edit_window.geometry("400x300")

    # Checkboxes y entradas para las opciones
    enable_sound_var = tk.IntVar(value=menu_options["ENABLE_SOUND"])
    show_fps_var = tk.IntVar(value=menu_options["SHOW_FPS"])
    debug_mode_var = tk.IntVar(value=menu_options["DEBUG_MODE"])

    tk.Checkbutton(edit_window, text="Habilitar sonido (ENABLE_SOUND)", variable=enable_sound_var).pack(anchor="w", pady=5)
    tk.Checkbutton(edit_window, text="Mostrar FPS (SHOW_FPS)", variable=show_fps_var).pack(anchor="w", pady=5)
    tk.Checkbutton(edit_window, text="Modo Debug (DEBUG_MODE)", variable=debug_mode_var).pack(anchor="w", pady=5)

    tk.Label(edit_window, text="Máximo de jugadores (MAX_PLAYERS):").pack(anchor="w", pady=5)
    max_players_entry = tk.Entry(edit_window)
    max_players_entry.insert(0, menu_options["MAX_PLAYERS"])
    max_players_entry.pack(anchor="w", pady=5)

    # Botón para guardar cambios
    tk.Button(edit_window, text="Guardar cambios", command=save_changes).pack(pady=10)

def load_games():
    """Carga los juegos desde configs/games.list y muestra solo el nombre en la lista."""
    listbox_games.delete(0, tk.END)  # Limpiar la lista visual
    if os.path.exists(GAMELIST_PATH):
        with open(GAMELIST_PATH, "r") as f:
            for line in f:
                game_entry = line.strip()
                if game_entry:
                    # Extraer solo el nombre del juego (después del "|")
                    try:
                        game_name = game_entry.split(" | ")[1]
                        listbox_games.insert(tk.END, game_name)
                    except IndexError:
                        messagebox.showerror("Error", f"Formato incorrecto en la línea: {game_entry}")
    update_enable_sound()  # Actualizar ENABLE_SOUND al cargar los juegos

def add_new_game():
    """Permite seleccionar un nuevo juego, copiarlo a la carpeta games y agregarlo a la lista."""
    # Seleccionar archivo ROM
    file_path = filedialog.askopenfilename(filetypes=[("NES ROMs", "*.nes")])
    if file_path:
        file_name = os.path.basename(file_path)  # Obtener el nombre del archivo
        new_path = os.path.join(GAMES_FOLDER, file_name)  # Ruta destino en la carpeta games

        # Copiar el archivo a la carpeta games
        if not os.path.exists(new_path):  # Evitar duplicados
            try:
                os.makedirs(GAMES_FOLDER, exist_ok=True)  # Crear carpeta games si no existe
                shutil.copy(file_path, new_path)  # Copiar la ROM
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo copiar el archivo: {e}")
                return

        # Crear la carpeta configs si no existe
        os.makedirs(os.path.dirname(GAMELIST_PATH), exist_ok=True)

        # Agregar el juego al archivo games.list
        game_name = os.path.splitext(file_name)[0]  # Nombre del juego sin extensión
        game_entry = f"{new_path} | {game_name}"  # Formato: ruta | nombre
        try:
            with open(GAMELIST_PATH, "a") as f:
                f.write(f"{game_entry}\n")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo escribir en games.list: {e}")
            return

        # Mostrar solo el nombre del juego en la lista visual
        listbox_games.insert(tk.END, game_name)
        update_enable_sound()  # Actualizar ENABLE_SOUND
        messagebox.showinfo("Éxito", f"{file_name} agregado correctamente.")
    else:
        messagebox.showwarning("Advertencia", "No seleccionaste ningún archivo.")

def delete_game():
    """Elimina el juego seleccionado de la lista y de la carpeta games."""
    selected_index = listbox_games.curselection()
    if not selected_index:
        messagebox.showwarning("Advertencia", "No seleccionaste ningún juego para eliminar.")
        return

    # Obtener el nombre del juego seleccionado
    selected_game_name = listbox_games.get(selected_index)
    listbox_games.delete(selected_index)

    # Buscar y eliminar la entrada completa en games.list
    if os.path.exists(GAMELIST_PATH):
        with open(GAMELIST_PATH, "r") as f:
            lines = f.readlines()
        with open(GAMELIST_PATH, "w") as f:
            for line in lines:
                if selected_game_name not in line:  # Comparar solo el nombre
                    f.write(line)
                else:
                    # Eliminar el archivo ROM correspondiente
                    rom_path = line.split(" | ")[0]
                    if os.path.exists(rom_path):
                        try:
                            os.remove(rom_path)
                        except Exception as e:
                            messagebox.showerror("Error", f"No se pudo eliminar el archivo ROM: {e}")

    update_enable_sound()  # Actualizar ENABLE_SOUND
    messagebox.showinfo("Éxito", f"El juego '{selected_game_name}' fue eliminado correctamente.")

def select_output_folder():
    """Permite seleccionar la carpeta de salida para las ROMs generadas."""
    global DEFAULT_OUTPUT_FOLDER
    folder_selected = filedialog.askdirectory()
    if folder_selected:
        DEFAULT_OUTPUT_FOLDER = folder_selected
        lbl_output_folder.config(text=f"Carpeta de salida: {DEFAULT_OUTPUT_FOLDER}")
    else:
        messagebox.showinfo("Información", "No se cambió la carpeta de salida.")

def build_rom():
    """Ejecuta el script build.bat para generar la ROM y muestra el resultado en tiempo real."""
    try:
        # Crear una ventana para mostrar la salida
        output_window = tk.Toplevel(root)
        output_window.title("Resultado de Generar ROM")
        output_window.geometry("600x400")

        # Crear un cuadro de texto con scroll para mostrar la salida
        text_area = scrolledtext.ScrolledText(output_window, wrap=tk.WORD, width=80, height=20)
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Función para ejecutar el script y capturar la salida en tiempo real
        def run_build_script():
            try:
                process = subprocess.Popen(
                    [BUILD_SCRIPT],
                    cwd=BASE_DIR,  # Asegurarse de que se ejecute en la carpeta del script
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Leer la salida en tiempo real
                for line in process.stdout:
                    text_area.insert(tk.END, line)
                    text_area.see(tk.END)  # Desplazar automáticamente hacia abajo
                for line in process.stderr:
                    text_area.insert(tk.END, "[ERROR] " + line)
                    text_area.see(tk.END)

                process.wait()  # Esperar a que el proceso termine
                if process.returncode == 0:
                    text_area.insert(tk.END, "\nROM generada correctamente.\n")

                    # Mover la ROM generada a la carpeta seleccionada
                    source_path = os.path.join(BASE_DIR, ROM_OUTPUT_NAME)
                    destination_path = os.path.join(DEFAULT_OUTPUT_FOLDER, ROM_OUTPUT_NAME)
                    if os.path.exists(source_path):
                        try:
                            shutil.move(source_path, destination_path)
                            text_area.insert(tk.END, f"\nROM movida a: {destination_path}\n")
                        except Exception as e:
                            text_area.insert(tk.END, f"\nError al mover la ROM: {e}\n")
                    else:
                        text_area.insert(tk.END, "\nError: No se encontró la ROM generada.\n")
                else:
                    text_area.insert(tk.END, "\nError al generar la ROM.\n")
            except Exception as e:
                text_area.insert(tk.END, f"\nError al ejecutar build.bat: {e}\n")

        # Ejecutar el script en un hilo separado para no bloquear la interfaz
        threading.Thread(target=run_build_script).start()

    except Exception as e:
        messagebox.showerror("Error", f"Error al ejecutar build.bat: {e}")

def convert_to_mapper_4():
    """Convierte una ROM seleccionada a Mapper 4."""
    file_path = filedialog.askopenfilename(filetypes=[("NES ROMs", "*.nes")])
    if not file_path:
        messagebox.showwarning("Advertencia", "No seleccionaste ningún archivo.")
        return

    # Ruta de salida para la ROM convertida
    output_path = os.path.splitext(file_path)[0] + "_mapper4.nes"

    try:
        # Comando para convertir la ROM (reemplaza esto con la herramienta que uses)
        # Aquí asumimos que tienes una herramienta llamada "nes_mapper_converter"
        result = subprocess.run(
            ["nes_mapper_converter", "--input", file_path, "--output", output_path, "--to-mapper", "4"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            messagebox.showinfo("Éxito", f"ROM convertida correctamente a Mapper 4.\nGuardada en: {output_path}")
        else:
            messagebox.showerror("Error", f"Error al convertir la ROM:\n{result.stderr}")
    except FileNotFoundError:
        messagebox.showerror("Error", "No se encontró la herramienta de conversión. Asegúrate de tener 'nes_mapper_converter' instalada.")
    except Exception as e:
        messagebox.showerror("Error", f"Error inesperado: {e}")

def center_window(window):
    """Centra la ventana en la pantalla."""
    window.update_idletasks()
    width = window.winfo_width()
    height = window.winfo_height()
    x = (window.winfo_screenwidth() // 2) - (width // 2)
    y = (window.winfo_screenheight() // 2) - (height // 2)
    window.geometry(f"{width}x{height}+{x}+{y}")

# Crear la ventana principal
root = tk.Tk()
root.title("MultiROM Builder by TipitoChen")
root.geometry("600x500")

# Centrar la ventana en la pantalla
center_window(root)

# Lista de juegos
tk.Label(root, text="Juegos en la lista:").pack()
listbox_games = tk.Listbox(root)
listbox_games.pack(fill=tk.BOTH, expand=True)

# Botones
btn_add_game = tk.Button(root, text="Agregar juego", command=add_new_game, width=20)
btn_add_game.pack(pady=5)

btn_delete_game = tk.Button(root, text="Eliminar juego", command=delete_game, width=20)
btn_delete_game.pack(pady=5)

btn_build = tk.Button(root, text="Generar ROM", command=build_rom, width=20)
btn_build.pack(pady=5)


# Contenedor para la ruta de salida y el botón de selección
output_frame = tk.Frame(root)
output_frame.pack(pady=5, fill=tk.X)

# Etiqueta para mostrar la carpeta de salida
lbl_output_folder = tk.Label(output_frame, text=f"Carpeta de salida: {DEFAULT_OUTPUT_FOLDER}", wraplength=380, anchor="w")
lbl_output_folder.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)

# Botón para seleccionar la carpeta de salida
btn_select_output = tk.Button(output_frame, text="Seleccionar carpeta", command=select_output_folder, width=20)
btn_select_output.pack(side=tk.RIGHT, padx=5)

# Cargar juegos y opciones al iniciar
load_games()
load_menu_options()

# Ejecutar la app
root.mainloop()