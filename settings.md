### ⚙️ The `/settings` Panel: Your Control Center

The `/settings` command is the central hub for customizing and controlling every aspect of your bot. From managing your bots to fine-tuning your filters, everything you need is right here.

---

### **Managing Your Identities & Channels**

* **Bots & Userbots**
    * **Access**: `/settings` -> `🤖 Bots`.
    * **Description**: This is where you manage the identities the bot uses for forwarding. You can add new bots from `@BotFather` or add a userbot (your personal account) by either providing a session string or securely logging in through the bot itself.
    * **Usage**:
        * `✚ Add bot`: Forward the bot token message from `@BotFather`.
        * `✚ Login User bot`: The bot will ask for your phone number and verification code to generate a new session string for you.
        * `✚ Add User bot`: Paste an existing Pyrogram V2 session string.
        * `❌ Remove`: Delete a bot or userbot from your account.

* **Channels**
    * **Access**: `/settings` -> `🏷 Channels`.
    * **Description**: Manage the destination channels where messages will be sent. The bot/userbot you use for forwarding **must** be an admin in this channel.
    * **Usage**:
        * `✚ Add Channel`: Forward any message from your target channel to the bot to add it to your list.
        * `❌ Remove`: Remove a channel from your list.

---

### **Customization & Configuration**

* **Custom Captions**
    * **Access**: `/settings` -> `🖋️ Caption`.
    * **Description**: Set a custom caption template for all forwarded media messages.
    * **Usage**:
        * `✚ Add Caption`: Send your custom text. You can use placeholders for dynamic content:
            * `{filename}`: Inserts the original file's name.
            * `{size}`: Inserts the file's size in a human-readable format (e.g., "15.4 MB").
            * `{caption}`: Inserts the original caption from the source message.

* **Custom Buttons**
    * **Access**: `/settings` -> `⏹ Button`.
    * **Description**: Attach a custom inline URL button to every forwarded message.
    * **Usage**:
        * `✚ Add Button`: Send your button in the format `[Button Text][buttonurl:URL]`.
        * **Example**: `[Join My Channel][buttonurl:https://t.me/Blaze_updateZ]`.

---

### **Advanced Features & Filters**

* **Filters (by Message Type)**
    * **Access**: `/settings` -> `🕵️‍♀️ Filters`.
    * **Description**: Individually toggle which types of messages you want to forward. Toggling a message type to `❌` means it will be skipped.
    * **Usage**: Select from the list to toggle on/off: `Texts`, `Documents`, `Videos`, `Photos`, `Audios`, `Voices`, `Animations`, `Stickers`, & `Polls`. You can also choose to `Skip duplicate` messages based on the current forwarding task.

* **Extra Settings (by File Attribute)**
    * **Access**: `/settings` -> `🧪 Extra Settings`.
    * **Description**: Fine-tune your filters based on specific file attributes.
    * **Usage**:
        * `💾 Min Size Limit`: Set a minimum file size (in MB). Files smaller than this will be filtered.
        * `💾 Max Size Limit`: Set a maximum file size (in MB). Files larger than this will be filtered.
        * `🚥 Keywords`: Add keywords that must be present in a file's name for it to be forwarded. Separate multiple keywords with a space.
        * `🕹 Extensions`: Add file extensions to block. Files with these extensions will not be forwarded.

* **Database (Deduplication)**
    * **Access**: `/settings` -> `🗃 MongoDB`.
    * **Description**: This is required for advanced deduplication features. Connecting a database allows the bot to permanently remember all files it has forwarded.
    * **Usage**: Add your MongoDB connection string (URI). The format is typically `mongodb+srv://...`.

---

### **Premium Features (For Advanced Users)**

* **Access**: `/settings` -> `💎 Premium Features 💎`.
* **Description**: This section contains advanced tools available exclusively to premium users.

* **Regex Filter**
    * **Usage**: `📜 Regex Filter` -> `✏️ Set/Edit Regex`.
    * **Description**: Use regular expressions to create complex filtering patterns. You can set the mode to either:
        * `Include`: Only forward files that match the pattern.
        * `Exclude`: Skip any file that matches the pattern.
    * **Examples**:
        * `^Start`: Matches any filename starting with "Start".
        * `\d{10}`: Matches any 10-digit number.
        * `word1|word2`: Matches filenames containing either "word1" or "word2".

* **Message Replacements**
    * **Usage**: `🔄 Message Replacements` -> `➕ Add/Edit Replacements`.
    * **Description**: Automatically find and replace text in message captions before they are forwarded.
    * **Format**: Send your replacement rules in the format `find|replace`. You can add multiple rules by separating each one with a new line.

* **Persistent Deduplication**
    * **Usage**: `💾 Persistent Deduplication` -> `☑️ Enable`.
    * **Description**: This feature, tied to your MongoDB setup, ensures the bot never forwards the same file twice, even across different tasks or after a restart. The bot keeps a permanent log of all forwarded files.