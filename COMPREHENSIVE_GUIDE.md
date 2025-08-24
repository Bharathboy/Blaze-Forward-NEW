# ⭐ Blaze Forward Bot: The Ultimate User Manual ⭐

Welcome! This comprehensive guide is designed to turn you into a power user of the Blaze Forward Bot. We'll cover everything from your first setup to mastering the most advanced automation features. The bot is built using Python 3.10.8 with the Pyrogram library.

---

## Table of Contents
1.  **Introduction: What is Blaze Forward Bot?**
2.  **Getting Started: Your First Forward in 5 Minutes**
3.  **The Two Modes of Forwarding**
4.  **The Control Center: The `/settings` Panel**
5.  **Managing Your Identities: Bots & Userbots**
6.  **Setting Your Destinations: Managing Channels**
7.  **Customization: Captions & Buttons**
8.  **The Power of Precision: Configuring Filters**
9.  **Advanced Deduplication: Setting up MongoDB**
10. **Task Management: Staying in Control**
11. **Unlocking Full Potential: Premium Features**
12. **Handy Utilities: `unequify` and `reset`**
13. **Full Command Reference**
14. **Detailed Command Breakdown**
15. **Settings Panel Deep Dive**

---

## 1. Introduction: What is Blaze Forward Bot?
Blaze Forward Bot is a sophisticated tool that automates the process of copying messages from any Telegram chat (channels, groups) to your own channels. It's built for users who need powerful filtering, customization, and reliability. Whether you're archiving content, creating a curated feed, or managing multiple channels, this bot is your all-in-one solution.

---

## 2. Getting Started: Your First Forward in 5 Minutes
Before you can unleash the bot's power, a simple one-time setup is required.

### Step 1: Say Hello!
Start a conversation with the bot by sending the `/start` command.

### Step 2: Add a Forwarding Identity (Bot or Userbot)
The bot needs an "identity" to send messages on your behalf.

* **Go to:** `/settings` -> `🤖 Bots`.

> **To Add a standard Bot:**
> 1.  Click `✚ Add bot`.
> 2.  The bot will prompt you to forward a message from `@BotFather` that contains your bot's API token.
> * **Best for:** Public channels where you have admin rights to add your bot. This is the safest method.

> **To Add a Userbot (Your Telegram Account):**
> 1.  Click `✚ Add User bot`.
> 2.  The bot will ask for your Pyrogram session string. You can get this by using the `✚ Login User bot` option, which will guide you through a secure login process.
> * **Best for:** Forwarding from private channels your account has joined, or public channels where you can't add a bot.
> * **❗️ Important Note:** While secure, using a personal account for automation (as a userbot) is against Telegram's Terms of Service and carries a small risk. It is **highly recommended** to use a secondary, non-essential Telegram account for this purpose.

### Step 3: Set Your Destination Channel
This is the channel where all the forwarded messages will go.

1.  **Go to:** `/settings` -> `🏷 Channels`.
2.  Click `✚ Add Channel`.
3.  Forward any message from your target destination channel to the bot.
4.  **This is the most important step:** Ensure the Bot or Userbot you added in Step 2 is an **admin in this destination channel** with, at minimum, the "Post Messages" permission.

---

## 3. The Two Modes of Forwarding

### Standard Forwarding (`/forward`)
This is the mode for forwarding a large number of *existing* messages from a source chat.

> **Use Case:** You've just found a channel with thousands of files and you want to copy all of them to your own channel.

#### Usage & Interactive Flow 🚀

* **Initiate the Task**
    * __Command__: `/forward`
    * __Description__: This command starts the process. The bot first checks if you have any active tasks and if you've reached your plan's limit.

* **Step 1: Choose Your Forwarder**
    * __Description__: The bot will display a list of all the bots and userbots you've added in `/settings`.
    * __Note__: You can manage your bot and userbot list at any time with the `/settings` command.

* **Step 2: Select Your Destination**
    * __Description__: The bot shows a list of your destination channels.
    * __Usage__: Click the button corresponding to the channel you want to forward messages to.

* **Step 3: Define Your Source**
    * __Description__: You need to tell the bot which chat to forward from. You can do this in two ways:
        * __Forwarding a message__: Simply forward any message from the source chat (channel or group) to the bot.
        * __Sending a link__: You can also send a public message link. The bot will automatically detect the chat ID and the last message ID from the link.
        * __Example Link__: `https://t.me/c/12345678/100` or `https://t.me/publicchannel/100`.

* **Step 4: Set the Skip Count**
    * __Description__: Don't want to forward every single message from the source chat? The bot gives you the option to skip a number of messages from the beginning.
    * __Usage__: Send a number to specify how many messages to skip (e.g., `100` to skip the first 100 messages) or click "No" to start from the beginning.

* **Step 5: Confirmation**
    * __Description__: A final summary is presented with all your selections, including your chosen bot, the source and destination chats, and the number of messages to skip.
    * __Action__: Click "Yes" to start the process.
    * **Note:** The progress message will show a detailed status including fetched, forwarded, duplicate, deleted, and filtered messages, along with estimated time to completion.

#### Task Execution & Status 📈

Once you confirm, the bot will start the forwarding task and provide a live status message that updates in real time. This message shows a comprehensive overview of the task's progress.

* **Progress Metrics**
    * __Total Messages__: The total number of messages in the source chat to be processed.
    * __Fetched__: The number of messages the bot has successfully accessed from the source chat.
    * __Forwarded__: The number of messages successfully forwarded to the destination.
    * __Remaining__: The number of messages left to process.
    * __Duplicates__: The number of duplicate files that were automatically skipped.
    * __Deleted__: The number of messages that were empty, service messages, or deleted from the source.
    * __Filtered__: The number of messages that were skipped due to your filter settings (by size, keywords, or extension).

* **Task Control**
    * `Stop Task`: You can cancel a specific forwarding task at any time using the `/stop` command.
    * `Retrieve Status`: If the live status message gets lost or deleted, you can use the `/ongoing` command to generate a new one.

### Live Forwarding (`/liveforward`)
This mode creates a persistent, real-time sync. Once active, any *new* message in the source chat will be instantly forwarded.

> **Use Case:** You want to create a mirror of a news channel, so every new post appears in your channel immediately.

#### Prerequisites & Usage 🚀

* **Userbot Requirement**
    * __Requirement__: This feature requires a Userbot to function. A standard bot cannot be used for this task.
    * __Note__: The Userbot you use for this task must be a member of all the source chats you want to forward from.

* **Initiate the Task**
    * __Command__: `/liveforward`
    * __Description__: Starts the interactive setup process. The bot will first check if you already have an active live forwarding session.

#### Interactive Flow

* **Step 1: Choose Your Listener**
    * __Description__: The bot will show a list of all your userbots. Select the one you want to use for this live forwarding task.
    * __Note__: If you only have one userbot, the bot will auto-select it for you.

* **Step 2: Select Your Destination**
    * __Description__: The bot displays a list of your destination channels.
    * __Action__: Click the button corresponding to the channel you want new messages forwarded to.

* **Step 3: Define Your Source(s)**
    * __Description__: This is where you specify the chat(s) you want to listen to.
    * **For Free Users**: You can only add a single source chat. The bot will prompt you to forward a message or send a link from the source.
    * **For Premium Users**: You can add multiple source chats. The bot will ask you to forward a message or send a link from the first source. After adding it, you will see a `Done Adding Sources` button. You can continue adding more sources, one by one, up to your plan's limit.

* **Step 4: Activation & Confirmation**
    * __Description__: Once all sources are added (or after the single source is provided for free users), the bot will activate the live forwarding session. It will send a final confirmation message detailing the Userbot being used, the source chat(s), and the destination chat.
    * __Important__: The bot will apply all your configured filters (from the `/settings` panel) to the messages it forwards.

#### Task Control ⚙️

* **Stopping a Session**
    * __Command__: `/stoplive`
    * __Description__: This command immediately stops all of your active live forwarding sessions at once.

* **Handling Errors**
    * __FloodWait__: The bot's forwarding mechanism includes a built-in retry mechanism to handle `FloodWait` errors gracefully by waiting the specified amount of time before trying again.
    * __Permissions__: If your Userbot does not have access to a source or destination chat, the bot will notify you with an error message and guide you on what to do.

---

## 4. The Control Center: The `/settings` Panel
The `/settings` command is your gateway to every configuration. The following sections detail what you can do here.

---

## 5. Managing Your Identities: Bots & Userbots
* **Location:** `/settings` -> `🤖 Bots`.
* Here you can add new bots/userbots, view the ones you've already added, or remove them. The `Login User bot` option provides a safe, interactive way to generate a session string without using external websites.

---

## 6. Setting Your Destinations: Managing Channels
* **Location:** `/settings` -> `🏷 Channels`.
* This is where you manage the channels the bot is allowed to forward messages *to*. You must be the owner or an admin of these channels.

---

## 7. Customization: Captions & Buttons
* **Captions:**
    * **Location:** `/settings` -> `🖋️ Caption`.
    * Define a template for captions on all forwarded media.
    * **Pro-Tip:** Use placeholders for dynamic content!
        * `{filename}`: Inserts the file's name.
        * `{size}`: Inserts a human-readable file size (e.g., "15.4 MB").
        * `{caption}`: Inserts the original caption from the source message.
* **Buttons:**
    * **Location:** `/settings` -> `⏹ Button`.
    * Add a clickable inline URL button to every message.
    * **Example Format:** `[Join My Channel][buttonurl:https://t.me/mychannel]`.

---

## 8. The Power of Precision: Configuring Filters
* **Location:** `/settings` -> `🕵️‍♀️ Filters` and `🧪 Extra Settings`.
* **Filter by Type:** In the main `Filters` menu, you can toggle on or off each message type (Text, Video, Document, etc.). An `❌` means it will be skipped.
* **Filter by Attributes (in `Extra Settings`):**
    * **Size Limit:** Set a minimum and/or maximum file size in MB. Files with sizes greater than the minimum and less than the maximum will be forwarded.
    * **Keywords:** Only forward files if their filename contains one of your specified words.
    * **Extensions:** Blacklist certain file extensions (e.g., enter `zip exe` to block ZIP and EXE files). Files with these extensions will not be forwarded.

---

## 9. Advanced Deduplication: Setting up MongoDB
* **Location:** `/settings` -> `🗃 MongoDB`.
* **Why?** A database is required for persistent deduplication, which prevents the bot from forwarding the same file twice across multiple tasks, even after a bot restart.
* **How:**
    1.  Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
    2.  Create a free cluster and follow the steps to get a "connection string" (URI).
    3.  Paste that string into the bot when prompted.

---

## 10. Task Management: Staying in Control
* `/ongoing`: If you accidentally delete a progress message for a standard forward, use this command to get it back.
* `/stop`: This command lists all your active standard forwarding tasks and lets you cancel them individually.
* `/stoplive`: This command immediately stops all active live-forwarding sessions.

---

## 11. Unlocking Full Potential: Premium Features
* **Increased Task Limits:** Run multiple forwards at once (up to 4 for Gold plan users).
* **Regex Filtering:** Use complex patterns to filter filenames. You can set the mode to either include (only forward files matching the regex) or exclude (skip files matching the regex).
    * **Example:** `^\[Movie\].*1080p.*` could match files that start with `[Movie]` and contain `1080p`.
* **Message Replacements:** Automatically find and replace text in captions. You can add multiple rules by separating them with a newline.
* **Persistent Deduplication:** The ultimate duplicate filter. With MongoDB set up, the bot will never forward the same file twice, ever. This is a premium feature.

---

## 12. Handy Utilities: `unequify` and `reset`
* `/unequify`: A powerful cleanup tool. It will scan a channel you specify and delete all duplicate media files, leaving your channel clean and organized. It requires a userbot to function.
* `/reset`: A simple command to wipe all your personal settings (filters, captions, etc.) and return them to the bot's default state.

---

## 13. Full Command Reference
**General Commands**
* `/start`: Checks if the bot is alive.
* `/forward`: Initiates a bulk forwarding task.
* `/liveforward`: Initiates a real-time forwarding task.
* `/stoplive`: Stops all real-time forwards.
* `/settings`: Access the main configuration panel.
* `/unequify`: Remove duplicate media from a chat.
* `/stop`: Cancel a specific bulk forwarding task.
* `/ongoing`: View the status of active tasks.
* `/reset`: Reset your personal settings.
* `/my_plan`: Check your current subscription status.
* `/plans`: View available premium plans.

---

## 14. Detailed Command Breakdown

### **General User Commands**

* **`/start`**
    * **Usage**: `/start`
    * **Description**: Checks if the bot is online and shows the welcome message.
    * **Note**: If it's your first time using the bot, it will automatically add you to the database.

* **`/help`**
    * **Usage**: `/help`
    * **Description**: Displays a comprehensive help message that lists all available commands and features.

* **`/about`**
    * **Usage**: `/about`
    * **Description**: Provides information about the bot, including its creator, hosting details, and version.

* **`/settings`**
    * **Usage**: `/settings`
    * **Description**: Opens the central settings panel to manage your bots, channels, and all filter configurations.

* **`/my_plan`**
    * **Usage**: `/my_plan`
    * **Description**: Shows you a summary of your current subscription plan.
    * **Details Displayed**: It will tell you your current plan, the number of simultaneous tasks you can run, and if your plan has an expiration date, it will show the time remaining.

* **`/plans`**
    * **Usage**: `/plans`
    * **Description**: Provides a detailed breakdown of all the available premium subscription plans.

### **Forwarding & Task Management Commands**

* **`/forward`**
    * **Usage**: `/forward`
    * **Description**: Starts an interactive process to perform a one-time, bulk forward of messages from one chat to another.

* **`/liveforward`**
    * **Usage**: `/liveforward`
    * **Description**: Initiates a real-time forwarding session that automatically sends new messages from a source chat to your destination.

* **`/stop`**
    * **Usage**: `/stop`
    * **Description**: Shows a list of your ongoing bulk forwarding tasks and allows you to cancel a specific one.

* **`/stoplive`**
    * **Usage**: `/stoplive`
    * **Description**: Stops all of your active real-time live forwarding sessions at once.

* **`/ongoing`**
    * **Usage**: `/ongoing`
    * **Description**: Regenerates the live status message for any of your active bulk forwarding tasks. This is useful if the original status message was lost or deleted.

### **Utility Commands**

* **`/unequify`**
    * **Usage**: `/unequify`
    * **Description**: Starts a process to scan a target chat and remove all duplicate media files, requiring a userbot with admin permissions.

* **`/reset`**
    * **Usage**: `/reset`
    * **Description**: Resets all your personal settings (filters, caption, etc.) to the default configuration. This does not affect your added bots or channels.

### **Owner-Only Commands**

* **`/broadcast`**
    * **Usage**: Reply to any message with `/broadcast`
    * **Description**: Sends the replied message to every user who has started the bot.

* **`/add_premium`**
    * **Usage**: `/add_premium <user_id> <plan> <duration>`
    * **Example**: `/add_premium 12345678 gold 30d`
    * **Description**: Grants a user a premium subscription. The duration can be in `min` (minutes), `h` (hours), `d` (days), `w` (weeks), or `m` (months).

* **`/remove_premium`**
    * **Usage**: `/remove_premium <user_id>`
    * **Description**: Revokes a user's premium status.

* **`/restart`**
    * **Usage**: `/restart`
    * **Description**: Restarts the bot's server.

* **`/resetall`**
    * **Usage**: `/resetall`
    * **Description**: Resets the settings for every user in the database to default.

---

## 15. Settings Panel Deep Dive

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

---

This comprehensive guide covers every aspect of the Blaze Forward Bot. Bookmark this document and refer back to it as you explore the bot's powerful features!
