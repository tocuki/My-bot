from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, CallbackContext

TOKEN = '7135906610:AAGnlU1P6fun6xVOMTQhcpbj2n-bsnFBtzs'

async def start(update: Update, context: CallbackContext) -> None:
    message = update.message if update.message else update.callback_query.message
    keyboard = [
        [InlineKeyboardButton("📂 Репозиторий", callback_data='repository')],
        [InlineKeyboardButton("📝 Подготовка к дебатам (Beta Test)", callback_data='debate_prep')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await message.reply_text("Выберите действие:", reply_markup=reply_markup)

async def button_handler(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text if update.message else None
    if context.user_data.get('step') == 'creating_folder' and user_input:
        folders = context.bot_data.setdefault('folders', [])
        if user_input in folders:
            await update.message.reply_text("Папка с таким названием уже существует!")
        else:
            folders.append(user_input)
            await update.message.reply_text(f'Папка "{user_input}" создана!')
        context.user_data.clear()
        return
    
    query = update.callback_query
    if query:
        await query.answer()
    
        if query.data == 'repository':
            keyboard = [
                [InlineKeyboardButton("📁 Создать папку", callback_data='create_folder')],
                [InlineKeyboardButton("📂 Выбрать папку", callback_data='choose_folder')],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_menu')]
            ]
            await query.message.reply_text("Репозиторий:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == 'create_folder':
            await query.message.reply_text("Введите название новой папки:")
            context.user_data['step'] = 'creating_folder'
        elif query.data == 'choose_folder':
            folders = context.bot_data.get('folders', [])
            if not folders:
                await query.message.reply_text("Нет доступных папок.")
                return
            keyboard = [[InlineKeyboardButton(folder, callback_data=f'folder_{folder}')]
                        for folder in folders]
            await query.message.reply_text("Выберите папку:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data.startswith('folder_'):
            folder_name = query.data[7:]
            keyboard = [
                [InlineKeyboardButton("📄 Посмотреть записи", callback_data=f'view_{folder_name}')],
                [InlineKeyboardButton("✏ Добавить запись", callback_data=f'add_{folder_name}')],
                [InlineKeyboardButton("✏ Изменить запись", callback_data=f'edit_{folder_name}')],
                [InlineKeyboardButton("🔙 Назад в меню", callback_data='back_to_menu')]
            ]
            await query.message.reply_text(f"Папка: {folder_name}", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data.startswith('view_'):
            folder_name = query.data[5:]
            records = context.bot_data.setdefault('records', {}).setdefault(folder_name, [])
            if not records:
                await query.message.reply_text("Записей нет.")
                return
            await query.message.reply_text("\n".join(records))
        elif query.data.startswith('add_'):
            folder_name = query.data[4:]
            context.user_data['step'] = 'adding_record'
            context.user_data['current_folder'] = folder_name
            await query.message.reply_text(f"Введите текст для добавления в папку {folder_name}:")
        elif query.data.startswith('edit_'):
            folder_name = query.data[5:]
            records = context.bot_data.get('records', {}).get(folder_name, [])
            if not records:
                await query.message.reply_text("Записей нет для редактирования.")
                return
            keyboard = [[InlineKeyboardButton(record[:30] + "...", callback_data=f'edit_text_{folder_name}_{i}')]
                        for i, record in enumerate(records)]
            await query.message.reply_text("Выберите запись для редактирования:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data.startswith('edit_text_'):
            parts = query.data.split('_')
            if len(parts) < 4:
                await query.message.reply_text("Ошибка! Некорректный запрос на редактирование.")
                return
            folder_name = parts[2]
            index = int(parts[3])
            records = context.bot_data.get('records', {}).get(folder_name, [])
            if not records or not (0 <= index < len(records)):
                await query.message.reply_text("Ошибка! Запись не найдена.")
                return
            context.user_data['step'] = 'editing_record'
            context.user_data['current_folder'] = folder_name
            context.user_data['record_index'] = index
            await query.message.reply_text(f"Текущая запись: {records[index]}\nВведите новый текст:")
        elif query.data == 'back_to_menu':
            await start(update, context)

async def handle_text(update: Update, context: CallbackContext) -> None:
    user_input = update.message.text.strip()
    if context.user_data.get('step') == 'adding_record':
        folder_name = context.user_data.get('current_folder')
        records = context.bot_data.setdefault('records', {}).setdefault(folder_name, [])
        records.append(user_input)
        await update.message.reply_text(f'Запись добавлена в {folder_name}!')
        context.user_data.clear()
        return
    if context.user_data.get('step') == 'creating_folder':
        folders = context.bot_data.setdefault('folders', [])
        if user_input in folders:
            await update.message.reply_text("Папка с таким названием уже существует!")
        else:
            folders.append(user_input)
            await update.message.reply_text(f'Папка "{user_input}" создана!')
        context.user_data.clear()
        return
    user_input = update.message.text.strip()
    if context.user_data.get('step') == 'editing_record':
        folder_name = context.user_data.get('current_folder')
        index = context.user_data.get('record_index')
        records = context.bot_data.setdefault('records', {}).setdefault(folder_name, [])
        if 0 <= index < len(records):
            records[index] = user_input
            await update.message.reply_text(f'Запись обновлена в {folder_name}!')
        else:
            await update.message.reply_text("Ошибка! Индекс записи неверный.")
        context.user_data.clear()

def main() -> None:
    app = Application.builder().token(TOKEN).build()
    dp = app
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CallbackQueryHandler(button_handler))
    dp.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.run_polling()

if __name__ == '__main__':
    main()
