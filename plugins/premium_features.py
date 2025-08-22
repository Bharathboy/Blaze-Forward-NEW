import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from plugins.test import update_configs, get_configs

async def is_premium(query):
    user_id = query.from_user.id
    if await db.get_premium_user_rank(user_id) == "default":
        await query.answer(
            "This is a premium-only feature!\n\nUse /plans to see available premium plans.",
            show_alert=True
        )
        return False
    return True

@Client.on_callback_query(filters.regex(r'^premium_features'))
async def premium_features_panel(client, query):
    if not await is_premium(query):
        return
    
    buttons = [
        [InlineKeyboardButton('📜 Regex Filter', callback_data='regex_filter')],
        [InlineKeyboardButton('🔄 Message Replacements', callback_data='message_replacements')],
        [InlineKeyboardButton('💾 Persistent Deduplication', callback_data='persistent_deduplication')],
        [InlineKeyboardButton('⬅️ Back', callback_data='settings#main')]
    ]
    await query.message.edit_text(
        "**💎 Premium Features 💎**\n\n"
        "Here you can configure advanced settings available to premium users.",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^regex_filter'))
async def regex_filter_settings(client, query):
    if not await is_premium(query):
        return
    
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    regex_filter = configs.get('regex_filter', None)

    text = "**📜 Regex Filter**\n\n"
    if regex_filter:
        text += f"A regex filter is currently active."
    else:
        text += "You have not set a regex filter."

    buttons = [
        [InlineKeyboardButton('✏️ Set/Edit Regex', callback_data='set_regex')],
    ]
    if regex_filter:
        buttons[0].append(InlineKeyboardButton('👀 Show Regex', callback_data='show_regex'))
        buttons.append([InlineKeyboardButton('🗑️ Remove Regex', callback_data='remove_regex')])

    buttons.append([InlineKeyboardButton('⬅️ Back', callback_data='premium_features')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^set_regex'))
async def set_regex_filter(client, query):
    if not await is_premium(query):
        return
    
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='regex_filter')]])
    user_id = query.from_user.id
    await query.message.edit_text("Please send me the regex pattern you want to use for filtering.")
    
    while True:
        response = await client.listen(user_id)
        if response.text:
            try:
                re.compile(response.text)
                await update_configs(user_id, 'regex_filter', response.text)
                await response.reply_text(
                    f"✅ Regex filter has been set to:\n`{response.text}`",
                    reply_markup=back_button
                )
                break
            except re.error:
                await response.reply_text("That is not a valid regex pattern. Please try again.")
        else:
            await response.reply_text("Invalid input. Please send a valid regex pattern.", reply_markup=back_button)
            break

@Client.on_callback_query(filters.regex(r'^show_regex'))
async def show_regex_filter(client, query):
    if not await is_premium(query):
        return
    
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    regex_filter = configs.get('regex_filter', 'No regex filter set.')
    await query.answer(regex_filter, show_alert=True)

@Client.on_callback_query(filters.regex(r'^remove_regex'))
async def remove_regex_filter(client, query):
    if not await is_premium(query):
        return
    
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='regex_filter')]])
    user_id = query.from_user.id
    await update_configs(user_id, 'regex_filter', None)
    await query.message.edit_text("✅ Regex filter has been removed.", reply_markup=back_button)

@Client.on_callback_query(filters.regex(r'^message_replacements'))
async def message_replacements_settings(client, query):
    if not await is_premium(query):
        return
        
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    replacements = configs.get('message_replacements', None)
    
    text = "**🔄 Message Replacements**\n\n"
    if replacements:
        text += "You have active message replacements."
    else:
        text += "You have no message replacements configured."
        
    buttons = [
        [InlineKeyboardButton('➕ Add/Edit Replacements', callback_data='set_replacement')],
    ]
    if replacements:
        buttons[0].append(InlineKeyboardButton('👀 Show Replacements', callback_data='show_replacements'))
        buttons.append([InlineKeyboardButton('🗑️ Remove All', callback_data='remove_replacements')])

    buttons.append([InlineKeyboardButton('⬅️ Back', callback_data='premium_features')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex(r'^set_replacement'))
async def set_message_replacement(client, query):
    if not await is_premium(query):
        return

    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='message_replacements')]])
    user_id = query.from_user.id
    await query.message.edit_text(
        "Please send the text to find, followed by `|` and the replacement text.\n\n"
        "**Example for a single replacement:**\n`old text|new text`\n\n"
        "**For multiple replacements, send each rule on a new line:**\n"
        "`word|phrase`\n`another|something else`"
    )
    
    response = await client.listen(user_id)
    if response.text:
        configs = await get_configs(user_id)
        replacements = configs.get('message_replacements') or {}
        
        lines = response.text.split('\n')
        added_count = 0
        for line in lines:
            if '|' in line:
                find, replace = line.split('|', 1)
                replacements[find.strip()] = replace.strip()
                added_count += 1
        
        if added_count > 0:
            await update_configs(user_id, 'message_replacements', replacements)
            await response.reply_text(f"✅ Successfully added/updated {added_count} replacement rule(s).", reply_markup=back_button)
        else:
            await response.reply_text("Invalid format. Please use `find|replace`.", reply_markup=back_button)

@Client.on_callback_query(filters.regex(r'^show_replacements'))
async def show_message_replacements(client, query):
    if not await is_premium(query):
        return
        
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    replacements = configs.get('message_replacements', {})
    
    if not replacements:
        return await query.answer("You have no message replacements configured.", show_alert=True)
    
    alert_text = "Your current replacements:\n\n"
    for find, replace in replacements.items():
        alert_text += f"Find: '{find}' -> Replace: '{replace}'\n"
        
    await query.answer(alert_text, show_alert=True)

@Client.on_callback_query(filters.regex(r'^remove_replacements'))
async def remove_message_replacements(client, query):
    if not await is_premium(query):
        return
        
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='message_replacements')]])
    user_id = query.from_user.id
    await update_configs(user_id, 'message_replacements', None)
    await query.message.edit_text("✅ All message replacements have been removed.", reply_markup=back_button)

@Client.on_callback_query(filters.regex(r'^persistent_deduplication'))
async def persistent_deduplication_settings(client, query):
    if not await is_premium(query):
        return
        
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    is_enabled = configs.get('persistent_deduplication', False)
    
    status = "Enabled" if is_enabled else "Disabled"
    button_text = "✅ Disable" if is_enabled else "☑️ Enable"
    
    buttons = [
        [InlineKeyboardButton(button_text, callback_data='toggle_deduplication')],
        [InlineKeyboardButton('⬅️ Back', callback_data='premium_features')]
    ]
    await query.message.edit_text(
        f"**💾 Persistent Deduplication**\n\n"
        f"This feature prevents the same file from being forwarded across all your tasks.\n\n"
        f"**Status:** `{status}`",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

@Client.on_callback_query(filters.regex(r'^toggle_deduplication'))
async def toggle_persistent_deduplication(client, query):
    if not await is_premium(query):
        return
        
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    is_enabled = configs.get('persistent_deduplication', False)
    await update_configs(user_id, 'persistent_deduplication', not is_enabled)
    
    # Manually edit the message after toggling
    new_status = "Enabled" if not is_enabled else "Disabled"
    new_button_text = "✅ Disable" if not is_enabled else "☑️ Enable"
    
    new_buttons = [
        [InlineKeyboardButton(new_button_text, callback_data='toggle_deduplication')],
        [InlineKeyboardButton('⬅️ Back', callback_data='premium_features')]
    ]
    
    await query.message.edit_text(
        f"**💾 Persistent Deduplication**\n\n"
        f"This feature prevents the same file from being forwarded across all your tasks.\n\n"
        f"**Status:** `{new_status}`",
        reply_markup=InlineKeyboardMarkup(new_buttons)
    )