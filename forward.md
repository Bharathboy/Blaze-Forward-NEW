### ➡️ The `/forward` Command: Bulk Message Forwarding

The `/forward` command initiates a powerful, interactive process to copy a large number of existing messages from one chat to another. The bot guides you through each step, making it simple to set up even the most complex forwarding tasks.

---

### **Usage & Interactive Flow** 🚀

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

---

### **Task Execution & Status** 📈

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