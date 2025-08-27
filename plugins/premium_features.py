import re
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database import db
from plugins.test import update_configs, get_configs
from config import Config

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
        [InlineKeyboardButton('🖼️ custom cover/thumb', callback_data='custom_cover')],
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
    regex_filter = configs.get('regex_filter')
    mode = configs.get('regex_filter_mode', 'exclude')

    text = f"**📜 Regex Filter**\n\n**Mode:** `{mode.title()}`\n"
    if mode == 'exclude':
        text += "Files matching the regex will be **excluded** (skipped)."
    else:
        text += "Only files matching the regex will be **included** (forwarded)."
    
    buttons = [
        [InlineKeyboardButton(f"🔄 Mode: {'Include' if mode == 'exclude' else 'Exclude'}", callback_data='toggle_regex_mode')],
        [InlineKeyboardButton('✏️ Set/Edit Regex', callback_data='set_regex')],
    ]
    if regex_filter:
        buttons[1].append(InlineKeyboardButton('👀 Show Regex', callback_data='show_regex'))
        buttons.append([InlineKeyboardButton('🗑️ Remove Regex', callback_data='remove_regex')])

    buttons.append([InlineKeyboardButton('⬅️ Back', callback_data='premium_features')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^toggle_regex_mode'))
async def toggle_regex_mode(client, query):
    if not await is_premium(query):
        return
    
    user_id = query.from_user.id
    configs = await get_configs(user_id)
    new_mode = 'include' if configs.get('regex_filter_mode', 'exclude') == 'exclude' else 'exclude'
    await update_configs(user_id, 'regex_filter_mode', new_mode)
    await regex_filter_settings(client, query)

@Client.on_callback_query(filters.regex(r'^set_regex'))
async def set_regex_filter(client, query):
    if not await is_premium(query):
        return
    
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='regex_filter')]])
    user_id = query.from_user.id
    
    # --- ADD BETTER INSTRUCTIONS ---
    await query.message.edit_text(
        "Please send me the regex pattern you want to use for filtering.\n\n"
        "**Tip:** A simple word is a valid pattern, but it's often too broad. "
        "Consider using more specific patterns.\n\n"
        "**Examples:**\n"
        "- `^Start` - Matches messages that start with 'Start'.\n"
        "- `\\d{10}` - Matches any 10-digit number.\n"
        "- `word1|word2` - Matches messages containing either 'word1' or 'word2'.",
        disable_web_page_preview=True
    )
    
    response = await client.listen(user_id)
    
    if response.text:
        pattern = response.text
        # --- VALIDATION LOGIC ---
        try:
            re.compile(pattern)
            
            # Warn if the pattern is too simple (e.g., less than 3 chars and just letters/numbers)
            if len(pattern) < 3 and pattern.isalnum():
                await response.reply_text(
                    f"⚠️ **Warning:** The pattern `{pattern}` is very simple and may match too many messages. "
                    "Are you sure you want to set it?\n\n"
                    "If this was a mistake, send a new pattern. Otherwise, send `/confirm` to use it anyway."
                )
                
                # Wait for confirmation
                confirm_response = await client.listen(user_id)
                if not confirm_response.text or confirm_response.text.lower() != '/confirm':
                    await confirm_response.reply_text("Regex filter cancelled. Please try setting it again.", reply_markup=back_button)
                    return # Exit the function

            # If validation passes or is confirmed, save the pattern
            await update_configs(user_id, 'regex_filter', pattern)
            await response.reply_text(
                f"✅ Regex filter has been set to:\n`{pattern}`",
                reply_markup=back_button
            )
            
        except re.error as e:
            await response.reply_text(f"❌ That is not a valid regex pattern.\n\n**Error:** `{e}`\nPlease try again.")
    else:
        await response.reply_text("Invalid input. Please send a text message.", reply_markup=back_button)

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

@Client.on_callback_query(filters.regex(r'^custom_cover'))
async def custom_cover_settings(client, query):
    if not await is_premium(query):
        return

    user_id = query.from_user.id
    configs = await get_configs(user_id)
    custom_cover = configs.get('custom_cover')

    text = "**🖼️ custom cover/thumb**\n\n"
    text += "Set a custom cover/thumb image that will be used as the thumbnail for forwarded videos."

    buttons = [
        [InlineKeyboardButton('🖼️ Set/Change Cover', callback_data='set_custom_cover')],
    ]
    if custom_cover:
        buttons[0].append(InlineKeyboardButton('👀 Show Cover', callback_data='show_custom_cover'))
        buttons.append([InlineKeyboardButton('🗑️ Remove Cover', callback_data='remove_custom_cover')])

    buttons.append([InlineKeyboardButton('⬅️ Back', callback_data='premium_features')])
    await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(buttons))

@Client.on_callback_query(filters.regex(r'^set_custom_cover'))
async def set_custom_cover(client, query):
    if not await is_premium(query):
        return

    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='custom_cover')]])
    user_id = query.from_user.id

    await query.message.edit_text("Please send me the image you want to use as a custom cover/thumb.")

    response = await client.listen(user_id)

    if response.photo:
        if not Config.PUBLIC_MEDIA_CHANNEL:
            return await response.reply_text("Error: `PUBLIC_MEDIA_CHANNEL` is not set in config.", reply_markup=back_button)
        try:
            log_message = await response.copy(chat_id=Config.PUBLIC_MEDIA_CHANNEL)
            await update_configs(user_id, 'custom_cover', log_message.link)
            await response.reply_text("✅ custom cover/thumb has been set.", reply_markup=back_button)
        except Exception as e:
            await response.reply_text(f"Error: {e}\n\nMake sure the bot is an admin in the public channel.", reply_markup=back_button)
    else:
        await response.reply_text("Invalid input. Please send an image.", reply_markup=back_button)

@Client.on_callback_query(filters.regex(r'^show_custom_cover'))
async def show_custom_cover(client, query):
    if not await is_premium(query):
        return

    user_id = query.from_user.id
    configs = await get_configs(user_id)
    cover_url = configs.get('custom_cover')

    if cover_url:
        # The URL itself is enough to send the photo
        await client.send_photo(query.message.chat.id, cover_url, caption="This is your current custom cover/thumb.")
    else:
        await query.answer("No custom cover/thumb set.", show_alert=True)

@Client.on_callback_query(filters.regex(r'^remove_custom_cover'))
async def remove_custom_cover(client, query):
    if not await is_premium(query):
        return
        
    back_button = InlineKeyboardMarkup([[InlineKeyboardButton('⬅️ Back', callback_data='custom_cover')]])
    user_id = query.from_user.id
    await update_configs(user_id, 'custom_cover', None)
    await query.message.edit_text("✅ custom cover/thumb has been removed.", reply_markup=back_button)