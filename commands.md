### 📖 Bot Commands & Usage: A Comprehensive Guide

Here is a detailed breakdown of every command available in the bot, along with its purpose and usage.

---

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

---

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

---

### **Utility Commands**

* **`/unequify`**
    * **Usage**: `/unequify`
    * **Description**: Starts a process to scan a target chat and remove all duplicate media files, requiring a userbot with admin permissions.

* **`/reset`**
    * **Usage**: `/reset`
    * **Description**: Resets all your personal settings (filters, caption, etc.) to the default configuration. This does not affect your added bots or channels.

---

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