import flet as ft

def main(page: ft.Page):
    # Настройки страницы
    page.title = "Документы"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window.width = 400
    page.window.height = 600

    # Функция, которая будет вызвана при выборе файла
    def pick_files_result(e: ft.FilePickerResultEvent):
        if e.files:
            selected_file.value = e.files[0].path
            selected_file.update()
            # Здесь можно добавить код для обработки выбранного PDF-файла
            print(f"Выбран файл: {selected_file.value}")

    # Создаем FilePicker
    file_picker = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(file_picker)

    # Текст для отображения выбранного файла
    selected_file = ft.Text("Файл не выбран", size=16)

    # Кнопка для выбора файла
    pick_file_button = ft.ElevatedButton(
        "Выбрать PDF файл",
        icon=ft.Icons.UPLOAD_FILE,
        on_click=lambda _: file_picker.pick_files(
            allowed_extensions=["pdf"],
            dialog_title="Выберите PDF файл"
        ),
    )

    # Добавляем элементы на страницу
    page.add(
        ft.Column(
            [
                ft.Icon(name=ft.Icons.PICTURE_AS_PDF, size=50),
                ft.Text("Выберите PDF файл", size=20),
                pick_file_button,
                selected_file
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=20
        )
    )

# Запускаем приложение
ft.app(target=main)





