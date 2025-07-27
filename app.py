import subprocess
import flet as ft

def main(page: ft.Page):
    # Настройки окна
    page.title = "Документ-генератор"
    page.window.width = 600
    page.window.height = 350
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    # Элементы интерфейса
    status_text = ft.Text("Выберите файл для обработки", size=20)
    file_path_display = ft.Text("", size=16, color=ft.Colors.GREY_600)


    def run_script(e):
        if not file_picker.result or not file_picker.result.files:
            status_text.value = "Ошибка: файл не выбран!"
            page.update()
            return

        file_path = file_picker.result.files[0].path
        status_text.value = "Запуск обработки..."
        run_btn.disabled = True
        page.update()

        try:
            # Здесь передаём путь в make_document.py
            subprocess.Popen(
                ["python", "main.py", file_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE
            )
            status_text.value = "Обработка запущена в новом окне"
        except Exception as e:
            status_text.value = f"Ошибка: {str(e)}"
            run_btn.disabled = False
        page.update()
    
    # Кнопки
    select_btn = ft.ElevatedButton(
        "Выбрать файл",
        on_click=lambda _: file_picker.pick_files()
    )
    
    run_btn = ft.ElevatedButton(
        "Запустить обработку",
        disabled=True,
        on_click=run_script
    )


    # Обработчик выбора файла
    def on_file_selected(e):
        if e.files:
            file_path = e.files[0].path
            file_path_display.value = f"Выбран файл: {file_path}"
            run_btn.disabled = False
            page.update()

    # Запуск основного скрипта

    # Настройка FilePicker
    file_picker = ft.FilePicker(on_result=on_file_selected)
    page.overlay.append(file_picker)

    # Сборка интерфейса
    page.add(
        ft.Column(
            [
                status_text,
                ft.Row([select_btn, run_btn], alignment=ft.MainAxisAlignment.CENTER),
                file_path_display
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER
        )
    )

ft.app(target=main)
