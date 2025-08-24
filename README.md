# ⭐ Blaze Forward Bot: The Ultimate User Manual ⭐

Welcome! This comprehensive guide is designed to turn you into a power user of the Blaze Forward Bot. We'll cover everything from your first setup to mastering the most advanced automation features.

---

## Table of Contents
1.  **Introduction: What is Blaze Forward Bot?**
2.  **Getting Started: Your First Forward in 5 Minutes**
3.  **The Two Modes of Forwarding**
    * Standard Forwarding (`/forward`): For Bulk/Existing Messages
    * Live Forwarding (`/liveforward`): For Real-Time Syncing
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

-   **Go to:** `/settings` -> `🤖 Bots`

> **To Add a standard Bot:**
> 1.  Click `✚ Add bot`.
> 2.  The bot will prompt you to forward a message from `@BotFather` that contains your bot's API token.
> -   **Best for:** Public channels where you have admin rights to add your bot. This is the safest method.

> **To Add a Userbot (Your Telegram Account):**
> 1.  Click `✚ Add User bot`.
> 2.  The bot will ask for your Pyrogram session string. You can get this by using the `✚ Login User bot` option, which will guide you through a secure login process.
> -   **Best for:** Forwarding from private channels your account has joined, or public channels where you can't add a bot.
> -   **❗️ Important Note:** While secure, using a personal account for automation (as a userbot) is against Telegram's Terms of Service and carries a small risk. It is **highly recommended** to use a secondary, non-essential Telegram account for this purpose.

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

1.  **Start:** Send the `/forward` command.
2.  **Select Identity:** Choose the Bot or Userbot you want to use for this job.
3.  **Select Destination:** Pick the target channel from your list.
4.  **Define Source:** Provide the source chat by either **forwarding a message** from it or **sending a public message link**.
5.  **Skip Messages (Optional):** The bot will ask if you want to skip any messages from the beginning. Enter `100` to skip the first 100 messages, or simply choose `No`.
6.  **Confirm & Launch:** Review the summary. If it's correct, hit **Yes**. The bot will create a live status message so you can track the progress in real-time.

### Live Forwarding (`/liveforward`)
This mode creates a persistent, real-time sync. Once active, any *new* message in the source chat will be instantly forwarded.

> **Use Case:** You want to create a mirror of a news channel, so every new post appears in your channel immediately.

1.  **Start:** Send `/liveforward`.
2.  **Select Listener:** This mode requires a Userbot to "listen" for new messages. Select the Userbot you want to use.
3.  **Select Destination:** Choose your target channel.
4.  **Define Source(s):**
    -   **Free Users:** Provide one source channel by forwarding a message or sending a link.
    -   **Premium Users:** You can add multiple source channels. The bot will show a `Done Adding Sources` button. Keep providing source channels, and click the button when you're finished.
5.  The bot will confirm the setup, and the live forward is now active. To stop it, use the `/stoplive` command.

---

## 4. The Control Center: The `/settings` Panel
The `/settings` command is your gateway to every configuration. The following sections detail what you can do here.

---

## 5. Managing Your Identities: Bots & Userbots
-   **Location:** `/settings` -> `🤖 Bots`
-   Here you can add new bots/userbots, view the ones you've already added, or remove them. The `Login User bot` option provides a safe, interactive way to generate a session string without using external websites.

---

## 6. Setting Your Destinations: Managing Channels
-   **Location:** `/settings` -> `🏷 Channels`
-   This is where you manage the channels the bot is allowed to forward messages *to*. You must be the owner or an admin of these channels.

---

## 7. Customization: Captions & Buttons
-   **Captions:**
    -   **Location:** `/settings` -> `🖋️ Caption`
    -   Define a template for captions on all forwarded media.
    -   **Pro-Tip:** Use placeholders for dynamic content!
        -   `{filename}`: Inserts the file's name.
        -   `{size}`: Inserts a human-readable file size (e.g., "15.4 MB").
        -   `{caption}`: Inserts the original caption from the source message.
-   **Buttons:**
    -   **Location:** `/settings` -> `⏹ Button`
    -   Add a clickable inline URL button to every message.
    -   **Example Format:** `[Join My Channel][buttonurl:https://t.me/mychannel]`

---

## 8. The Power of Precision: Configuring Filters
-   **Location:** `/settings` -> `🕵‍♀ Filters` and `🧪 Extra Settings`
-   **Filter by Type:** In the main `Filters` menu, you can toggle on or off each message type (Text, Video, Document, etc.). An `❌` means it will be skipped.
-   **Filter by Attributes (in `Extra Settings`):**
    -   **Size Limit:** Set a minimum and/or maximum file size.
    -   **Keywords:** Only forward files if their filename contains one of your specified words.
    -   **Extensions:** Blacklist certain file extensions (e.g., enter `zip exe` to block ZIP and EXE files).

---

## 9. Advanced Deduplication: Setting up MongoDB
-   **Location:** `/settings` -> `🗃 MongoDB`
-   **Why?** This is required for the premium **Persistent Deduplication** feature. A database allows the bot to remember every file it has ever forwarded for you, across all tasks.
-   **How:**
    1.  Create a free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas/register).
    2.  Create a free cluster and follow the steps to get a "connection string" (URI).
    3.  Paste that string into the bot when prompted.

---

## 10. Task Management: Staying in Control
-   `/ongoing`: If you accidentally delete a progress message for a standard forward, use this command to get it back.
-   `/stop`: This command lists all your active standard forwarding tasks and lets you cancel them individually.
-   `/stoplive`: This command immediately stops all active live-forwarding sessions.

---

## 11. Unlocking Full Potential: Premium Features
-   **Increased Task Limits:** Run multiple forwards at once.
-   **Regex Filtering:** Use complex patterns to filter filenames. For example, `^\[Movie\].*1080p.*` could match files that start with `[Movie]` and contain `1080p`.
-   **Message Replacements:** Automatically find and replace text in captions. Perfect for removing ads or standardizing formatting.
-   **Persistent Deduplication:** The ultimate duplicate filter. With MongoDB set up, the bot will never forward the same file twice, ever.

---

## 12. Handy Utilities: `unequify` and `reset`
-   `/unequify`: A powerful cleanup tool. It will scan a channel you specify and delete all duplicate media files, leaving your channel clean and organized.
-   `/reset`: A simple command to wipe all your personal settings (filters, captions, etc.) and return them to the bot's default state.

---

## 13. Full Command Reference
**General Commands**
-   `/start`: Checks if the bot is alive.
-   `/forward`: Initiates a bulk forwarding task.
-   `/liveforward`: Initiates a real-time forwarding task.
-   `/stoplive`: Stops all real-time forwards.
-   `/settings`: Access the main configuration panel.
-   `/unequify`: Remove duplicate media from a chat.
-   `/stop`: Cancel a specific bulk forwarding task.
-   `/ongoing`: View the status of active tasks.
-   `/reset`: Reset your personal settings.
-   `/my_plan`: Check your current subscription status.
-   `/plans`: View available premium plans.